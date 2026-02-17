"""
API Routes

All FastAPI endpoint handlers for CloudPulse.
"""

import logging
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.models import (
    AWSAccount, CostRecord as CostRecordModel, Anomaly,
    Recommendation, AlertConfig, AccountStatus, Budget, User, SharedReport,
)
from app.api.schemas import (
    AWSAccountCreate, AWSAccountResponse,
    CostQuery, CostSummary, CostForecast,
    DrillDownResponse,
    AnomalyResponse, RecommendationResponse,
    BudgetCreate, BudgetUpdate, BudgetResponse,
    AlertConfigCreate, AlertConfigResponse,
    UserCreate, UserResponse, TokenResponse,
    MessageResponse,
)
from app.core.auth import (
    hash_password, verify_password, create_access_token, get_current_user, get_optional_user,
)
from app.services.cost_explorer import CostExplorerService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# -------------------------------------------------------------------
# Authentication
# -------------------------------------------------------------------

@router.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account."""
    # Check if email already registered
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return a JWT token."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token(user_id=str(user.id), email=user.email)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user."""
    return current_user


# -------------------------------------------------------------------
# AWS Account Management
# -------------------------------------------------------------------

@router.post("/accounts", response_model=AWSAccountResponse, status_code=201)
async def connect_aws_account(
    payload: AWSAccountCreate,
    db: AsyncSession = Depends(get_db),
):
    """Connect a new AWS account by providing an IAM role ARN."""
    external_id = str(uuid.uuid4())

    # Validate access to the customer's AWS account
    ce_service = CostExplorerService(
        role_arn=payload.role_arn,
        external_id=external_id,
    )

    if not ce_service.validate_access():
        raise HTTPException(
            status_code=400,
            detail="Unable to access AWS account. Verify the IAM role and trust policy.",
        )

    account = AWSAccount(
        aws_account_id=payload.aws_account_id,
        role_arn=payload.role_arn,
        external_id=external_id,
        account_name=payload.account_name,
        status=AccountStatus.ACTIVE,
        # TODO: set user_id from auth context
    )

    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/accounts", response_model=list[AWSAccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
):
    """List all connected AWS accounts."""
    # TODO: filter by authenticated user
    result = await db.execute(select(AWSAccount))
    accounts = result.scalars().all()
    return accounts


@router.delete("/accounts/{account_id}", response_model=MessageResponse)
async def disconnect_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect an AWS account."""
    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.status = AccountStatus.DISCONNECTED
    await db.flush()
    return MessageResponse(message="Account disconnected successfully")


# -------------------------------------------------------------------
# Cost Data
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/costs", response_model=CostSummary)
async def get_costs(
    account_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    granularity: str = "DAILY",
    db: AsyncSession = Depends(get_db),
):
    """Get cost data for an AWS account."""
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Query stored cost records
    cost_query = (
        select(CostRecordModel)
        .where(CostRecordModel.aws_account_id == account_id)
        .where(CostRecordModel.date >= start_date)
        .where(CostRecordModel.date <= end_date)
        .order_by(CostRecordModel.date)
    )
    cost_result = await db.execute(cost_query)
    records = cost_result.scalars().all()

    # Build service breakdown
    service_totals = {}
    daily_totals = {}

    for record in records:
        # Service totals
        if record.service not in service_totals:
            service_totals[record.service] = 0
        service_totals[record.service] += record.amount

        # Daily totals
        day_str = record.date.isoformat()
        if day_str not in daily_totals:
            daily_totals[day_str] = 0
        daily_totals[day_str] += record.amount

    by_service = [
        {"date": "", "service": svc, "amount": round(amt, 2), "currency": "USD"}
        for svc, amt in sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    daily_list = [
        {"date": d, "amount": round(amt, 2)}
        for d, amt in sorted(daily_totals.items())
    ]

    total = sum(service_totals.values())

    return CostSummary(
        total_spend=round(total, 2),
        currency="USD",
        period_start=start_date.isoformat(),
        period_end=end_date.isoformat(),
        by_service=by_service,
        daily_totals=daily_list,
    )


@router.get("/accounts/{account_id}/forecast", response_model=CostForecast)
async def get_forecast(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get cost forecast for an AWS account.
    Uses stored data for a linear projection. Falls back to AWS API if available.
    """
    from calendar import monthrange

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()
    month_start = today.replace(day=1)
    days_in_month = monthrange(today.year, today.month)[1]
    if today.month == 12:
        month_end = date(today.year + 1, 1, 1)
    else:
        month_end = date(today.year, today.month + 1, 1)

    # Get MTD spend from stored records
    mtd_result = await db.execute(
        select(func.sum(CostRecordModel.amount))
        .where(CostRecordModel.aws_account_id == account_id)
        .where(CostRecordModel.date >= month_start)
        .where(CostRecordModel.date <= today)
    )
    mtd_spend = round(mtd_result.scalar() or 0, 2)

    days_elapsed = max((today - month_start).days, 1)
    days_remaining = days_in_month - days_elapsed
    daily_avg = round(mtd_spend / days_elapsed, 2)
    projected_total = round(daily_avg * days_in_month, 2)

    # Try AWS forecast API for a more accurate number
    try:
        from app.services.local_cost_explorer import LocalCostExplorerService
        ce = LocalCostExplorerService()
        aws_forecast = ce.get_cost_forecast(
            start_date=today + timedelta(days=1),
            end_date=month_end,
        )
        if aws_forecast:
            return CostForecast(
                total_forecast=aws_forecast["total_forecast"],
                currency=aws_forecast["currency"],
                start=aws_forecast["start"],
                end=aws_forecast["end"],
                mtd_spend=mtd_spend,
                daily_avg=daily_avg,
                days_remaining=days_remaining,
                projected_total=projected_total,
                source="aws",
            )
    except Exception as e:
        logger.warning(f"AWS forecast unavailable, using linear: {e}")

    return CostForecast(
        total_forecast=projected_total,
        currency="USD",
        start=today.isoformat(),
        end=month_end.isoformat(),
        mtd_spend=mtd_spend,
        daily_avg=daily_avg,
        days_remaining=days_remaining,
        projected_total=projected_total,
        source="linear",
    )


# -------------------------------------------------------------------
# Cost Drill-Down ("Why?")
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/drill-down", response_model=DrillDownResponse)
async def get_cost_drill_down(
    account_id: str,
    current_start: date | None = None,
    current_end: date | None = None,
    previous_start: date | None = None,
    previous_end: date | None = None,
    mode: str = "week",  # "day", "week", "month", or "custom"
    db: AsyncSession = Depends(get_db),
):
    """
    Explain WHY costs changed between two periods.

    Modes:
    - day: yesterday vs day before
    - week: last 7 days vs prior 7 days
    - month: last 30 days vs prior 30 days
    - custom: use provided date params
    """
    from app.services.cost_drill_down import CostDrillDownService

    # Verify account exists
    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()

    # Determine periods based on mode
    if mode == "custom" and current_start and current_end:
        if not previous_start:
            delta = (current_end - current_start).days
            previous_end = current_start
            previous_start = previous_end - timedelta(days=delta)
        if not previous_end:
            delta = (current_end - current_start).days
            previous_end = previous_start + timedelta(days=delta)
    elif mode == "day":
        current_end = today
        current_start = today - timedelta(days=1)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=1)
    elif mode == "month":
        current_end = today
        current_start = today - timedelta(days=30)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=30)
    else:  # default: week
        current_end = today
        current_start = today - timedelta(days=7)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=7)

    # Fetch stored cost records covering both periods
    cost_query = (
        select(CostRecordModel)
        .where(CostRecordModel.aws_account_id == account_id)
        .where(CostRecordModel.date >= previous_start)
        .where(CostRecordModel.date < current_end)
        .order_by(CostRecordModel.date)
    )
    cost_result = await db.execute(cost_query)
    records = cost_result.scalars().all()

    cost_records = [
        {"date": r.date, "service": r.service, "amount": float(r.amount)}
        for r in records
    ]

    drill_down = CostDrillDownService()
    analysis = drill_down.analyze_from_stored_data(
        cost_records=cost_records,
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )

    return analysis


# -------------------------------------------------------------------
# Anomalies
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/anomalies", response_model=list[AnomalyResponse])
async def get_anomalies(
    account_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
    severity: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get detected anomalies for an AWS account."""
    query = select(Anomaly).where(Anomaly.aws_account_id == account_id)

    if start_date:
        query = query.where(Anomaly.date >= start_date)
    if end_date:
        query = query.where(Anomaly.date <= end_date)
    if severity:
        query = query.where(Anomaly.severity == severity)

    query = query.order_by(Anomaly.date.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/anomalies/{anomaly_id}/acknowledge", response_model=MessageResponse)
async def acknowledge_anomaly(
    anomaly_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark an anomaly as acknowledged."""
    result = await db.execute(
        select(Anomaly).where(Anomaly.id == anomaly_id)
    )
    anomaly = result.scalar_one_or_none()
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    anomaly.acknowledged = True
    await db.flush()
    return MessageResponse(message="Anomaly acknowledged")


# -------------------------------------------------------------------
# Recommendations
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/recommendations", response_model=list[RecommendationResponse])
async def get_recommendations(
    account_id: str,
    include_resolved: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get cost optimization recommendations for an AWS account."""
    query = select(Recommendation).where(Recommendation.aws_account_id == account_id)

    if not include_resolved:
        query = query.where(Recommendation.is_resolved == False)

    query = query.order_by(Recommendation.estimated_monthly_savings.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/recommendations/{rec_id}/resolve", response_model=MessageResponse)
async def resolve_recommendation(
    rec_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark a recommendation as resolved."""
    result = await db.execute(
        select(Recommendation).where(Recommendation.id == rec_id)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.is_resolved = True
    await db.flush()
    return MessageResponse(message="Recommendation marked as resolved")


# -------------------------------------------------------------------
# Budgets
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/budgets", response_model=list[BudgetResponse])
async def list_budgets(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List all budgets for an account."""
    result = await db.execute(
        select(Budget)
        .where(Budget.aws_account_id == account_id)
        .order_by(Budget.created_at.desc())
    )
    return result.scalars().all()


@router.post("/accounts/{account_id}/budgets", response_model=BudgetResponse, status_code=201)
async def create_budget(
    account_id: str,
    payload: BudgetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new budget for an account."""
    # Verify account exists
    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    budget = Budget(
        aws_account_id=account_id,
        name=payload.name,
        amount=payload.amount,
        period=payload.period,
        service_filter=payload.service_filter,
        alert_at_pct=payload.alert_at_pct,
    )
    db.add(budget)
    await db.flush()
    await db.refresh(budget)
    return budget


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: str,
    payload: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing budget."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    await db.flush()
    await db.refresh(budget)
    return budget


@router.delete("/budgets/{budget_id}", response_model=MessageResponse)
async def delete_budget(
    budget_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a budget."""
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    await db.delete(budget)
    await db.flush()
    return MessageResponse(message="Budget deleted")


@router.post("/accounts/{account_id}/budgets/check", response_model=list[BudgetResponse])
async def check_budgets(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Recalculate current_spend for all active budgets and return them.
    Used by the frontend refresh button and by cron jobs.
    """
    from datetime import datetime as dt

    # Get all active budgets for this account
    result = await db.execute(
        select(Budget)
        .where(Budget.aws_account_id == account_id)
        .where(Budget.is_active == True)
    )
    budgets = result.scalars().all()

    today = date.today()
    month_start = today.replace(day=1)

    for budget in budgets:
        # Determine period start
        if budget.period.value == "quarterly":
            quarter_month = ((today.month - 1) // 3) * 3 + 1
            period_start = today.replace(month=quarter_month, day=1)
        else:
            period_start = month_start

        # Query actual spend
        spend_query = select(func.sum(CostRecordModel.amount)).where(
            CostRecordModel.aws_account_id == account_id,
            CostRecordModel.date >= period_start,
            CostRecordModel.date <= today,
        )
        if budget.service_filter:
            spend_query = spend_query.where(
                CostRecordModel.service == budget.service_filter
            )

        spend_result = await db.execute(spend_query)
        current_spend = spend_result.scalar() or 0.0

        budget.current_spend = round(current_spend, 2)
        budget.last_checked_at = dt.utcnow()

    await db.flush()

    # Refresh all budgets to get updated data
    for budget in budgets:
        await db.refresh(budget)

    return budgets


# -------------------------------------------------------------------
# Cost-per-Tag Breakdown (P1)
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/tags")
async def get_available_tags(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """List available tag keys for cost grouping."""
    from app.services.local_cost_explorer import LocalCostExplorerService

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()
    ce = LocalCostExplorerService()
    tags = ce.get_available_tags(
        start_date=today - timedelta(days=30),
        end_date=today,
    )
    return {"tags": tags}


@router.get("/accounts/{account_id}/costs/by-tag")
async def get_costs_by_tag(
    account_id: str,
    tag_key: str = "Environment",
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get cost breakdown grouped by a specific tag."""
    from app.services.local_cost_explorer import LocalCostExplorerService

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()
    ce = LocalCostExplorerService()

    try:
        tag_costs = ce.get_cost_by_tag(
            start_date=today - timedelta(days=days),
            end_date=today,
            tag_key=tag_key,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch tag data: {str(e)}")

    # Aggregate by tag value
    tag_totals = {}
    for record in tag_costs:
        tv = record["tag_value"]
        tag_totals[tv] = tag_totals.get(tv, 0) + record["amount"]

    total = sum(tag_totals.values())
    breakdown = [
        {
            "tag_value": tv,
            "amount": round(amt, 2),
            "pct": round(amt / total * 100, 1) if total > 0 else 0,
        }
        for tv, amt in sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "tag_key": tag_key,
        "total": round(total, 2),
        "breakdown": breakdown,
        "raw": tag_costs,
    }


# -------------------------------------------------------------------
# One-Click CloudFormation Setup (P1)
# -------------------------------------------------------------------

@router.get("/setup/cloudformation")
async def get_cloudformation_url():
    """
    Generate a CloudFormation Launch Stack URL with a unique external ID.
    Users click this to auto-create the IAM role in their AWS account.
    """
    import urllib.parse

    external_id = str(uuid.uuid4())
    template_url = f"{settings.app_url}/static/cloudpulse-iam-role.yaml"

    # Build the CloudFormation quick-create URL
    params = urllib.parse.urlencode({
        "templateURL": template_url,
        "stackName": "CloudPulse-IAM-Role",
        "param_ExternalId": external_id,
    })
    launch_url = f"https://console.aws.amazon.com/cloudformation/home#/stacks/quickcreate?{params}"

    return {
        "launch_url": launch_url,
        "external_id": external_id,
        "template_url": template_url,
        "instructions": [
            "1. Click the Launch Stack URL to open AWS CloudFormation",
            "2. Review the template and click 'Create stack'",
            "3. Wait for stack creation to complete (~1 min)",
            "4. Copy the Role ARN from the Outputs tab",
            "5. Paste the Role ARN back in CloudPulse to connect your account",
        ],
    }


@router.post("/setup/connect")
async def connect_via_cloudformation(
    role_arn: str,
    external_id: str,
    account_name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Connect an AWS account using the role ARN from CloudFormation.
    """
    # Extract account ID from ARN
    # arn:aws:iam::123456789012:role/CloudPulseCostReader
    try:
        aws_account_id = role_arn.split("::")[1].split(":")[0]
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid Role ARN format")

    # Validate access
    ce_service = CostExplorerService(role_arn=role_arn, external_id=external_id)
    if not ce_service.validate_access():
        raise HTTPException(
            status_code=400,
            detail="Cannot access AWS account. Ensure the CloudFormation stack completed successfully.",
        )

    account = AWSAccount(
        aws_account_id=aws_account_id,
        role_arn=role_arn,
        external_id=external_id,
        account_name=account_name or f"AWS {aws_account_id}",
        status=AccountStatus.ACTIVE,
        # TODO: set user_id from auth context
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)

    return {
        "message": "Account connected successfully",
        "account_id": str(account.id),
        "aws_account_id": aws_account_id,
    }


# -------------------------------------------------------------------
# AI Cost Insights (P1)
# -------------------------------------------------------------------

@router.get("/accounts/{account_id}/insights")
async def get_ai_insights(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate AI-powered plain-English cost insights.
    Uses Bedrock (Claude) when available, falls back to template.
    """
    from app.services.ai_insights import AICostInsightsService
    from app.services.cost_drill_down import CostDrillDownService

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()
    month_start = today.replace(day=1)

    # Get MTD cost data
    cost_result = await db.execute(
        select(CostRecordModel)
        .where(CostRecordModel.aws_account_id == account_id)
        .where(CostRecordModel.date >= month_start)
        .where(CostRecordModel.date <= today)
        .order_by(CostRecordModel.date)
    )
    records = cost_result.scalars().all()

    # Aggregate by service
    service_totals = {}
    total = 0
    for r in records:
        service_totals[r.service] = service_totals.get(r.service, 0) + r.amount
        total += r.amount

    top_services = [
        {"service": svc, "amount": round(amt, 2), "pct": round(amt / total * 100, 1) if total > 0 else 0}
        for svc, amt in sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
    ][:5]

    # Get anomaly count
    anomaly_result = await db.execute(
        select(func.count(Anomaly.id))
        .where(Anomaly.aws_account_id == account_id)
        .where(Anomaly.acknowledged == False)
        .where(Anomaly.date >= today - timedelta(days=7))
    )
    anomaly_count = anomaly_result.scalar() or 0

    # Get week-over-week change
    cost_records = [
        {"date": r.date, "service": r.service, "amount": float(r.amount)}
        for r in records
    ]
    drill_down = CostDrillDownService()
    weekly = drill_down.analyze_from_stored_data(
        cost_records=[{"date": r.date, "service": r.service, "amount": float(r.amount)}
                      for r in (await db.execute(
                          select(CostRecordModel)
                          .where(CostRecordModel.aws_account_id == account_id)
                          .where(CostRecordModel.date >= today - timedelta(days=14))
                          .where(CostRecordModel.date <= today)
                      )).scalars().all()],
        current_start=today - timedelta(days=7),
        current_end=today,
        previous_start=today - timedelta(days=14),
        previous_end=today - timedelta(days=7),
    )

    ctx = {
        "total_spend": round(total, 2),
        "period": f"{month_start.isoformat()} to {today.isoformat()}",
        "top_services": top_services,
        "anomaly_count": anomaly_count,
        "change_pct": weekly["total_change_pct"] * 100 if weekly else None,
    }

    ai = AICostInsightsService()
    insight = ai.generate_insight(ctx)

    return {
        "insight": insight,
        "context": ctx,
    }


# -------------------------------------------------------------------
# Alert Configuration
# -------------------------------------------------------------------

@router.get("/alerts/config", response_model=list[AlertConfigResponse])
async def get_alert_configs(
    db: AsyncSession = Depends(get_db),
):
    """Get all alert configurations."""
    # TODO: filter by authenticated user
    result = await db.execute(select(AlertConfig))
    return result.scalars().all()


@router.post("/alerts/config", response_model=AlertConfigResponse, status_code=201)
async def create_alert_config(
    payload: AlertConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert configuration."""
    config = AlertConfig(
        channel=payload.channel,
        email_address=payload.email_address,
        slack_webhook_url=payload.slack_webhook_url,
        notify_info=payload.notify_info,
        notify_warning=payload.notify_warning,
        notify_critical=payload.notify_critical,
        daily_summary=payload.daily_summary,
        # TODO: set user_id from auth context
    )

    db.add(config)
    await db.flush()
    await db.refresh(config)
    return config


@router.delete("/alerts/config/{config_id}", response_model=MessageResponse)
async def delete_alert_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert configuration."""
    result = await db.execute(
        select(AlertConfig).where(AlertConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Alert config not found")

    await db.delete(config)
    await db.flush()
    return MessageResponse(message="Alert config deleted")


# -------------------------------------------------------------------
# Shareable Reports (P1)
# -------------------------------------------------------------------

@router.post("/accounts/{account_id}/reports/share")
async def create_shared_report(
    account_id: str,
    title: str = "Cost Report",
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a shareable report snapshot. Returns a public URL token.
    """
    import json
    import secrets

    result = await db.execute(
        select(AWSAccount).where(AWSAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    today = date.today()
    start = today - timedelta(days=days)

    # Snapshot cost data
    cost_result = await db.execute(
        select(CostRecordModel)
        .where(CostRecordModel.aws_account_id == account_id)
        .where(CostRecordModel.date >= start)
        .where(CostRecordModel.date <= today)
        .order_by(CostRecordModel.date)
    )
    records = cost_result.scalars().all()

    service_totals = {}
    daily_totals = {}
    for r in records:
        service_totals[r.service] = service_totals.get(r.service, 0) + r.amount
        d = r.date.isoformat()
        daily_totals[d] = daily_totals.get(d, 0) + r.amount

    report_data = {
        "account_name": account.account_name or account.aws_account_id,
        "period_start": start.isoformat(),
        "period_end": today.isoformat(),
        "total_spend": round(sum(service_totals.values()), 2),
        "by_service": [
            {"service": s, "amount": round(a, 2)}
            for s, a in sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
        ],
        "daily_totals": [
            {"date": d, "amount": round(a, 2)}
            for d, a in sorted(daily_totals.items())
        ],
    }

    token = secrets.token_urlsafe(32)
    report = SharedReport(
        aws_account_id=account_id,
        token=token,
        title=title,
        report_data=json.dumps(report_data),
    )
    db.add(report)
    await db.flush()

    return {
        "token": token,
        "url": f"{settings.app_url}/reports/{token}",
        "title": title,
    }


@router.get("/reports/{token}")
async def get_shared_report(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — view a shared report. No authentication required.
    """
    import json
    from datetime import datetime as dt

    result = await db.execute(
        select(SharedReport).where(SharedReport.token == token)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check expiration
    if report.expires_at and report.expires_at < dt.utcnow():
        raise HTTPException(status_code=410, detail="Report has expired")

    return {
        "title": report.title,
        "created_at": report.created_at.isoformat(),
        "data": json.loads(report.report_data),
    }


# -------------------------------------------------------------------
# Dashboard Summary
# -------------------------------------------------------------------

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get a high-level dashboard summary across all accounts."""
    # TODO: filter by authenticated user
    today = date.today()
    month_start = today.replace(day=1)

    # Total accounts
    account_count = await db.execute(
        select(func.count(AWSAccount.id)).where(AWSAccount.status == AccountStatus.ACTIVE)
    )

    # Month-to-date spend
    mtd_result = await db.execute(
        select(func.sum(CostRecordModel.amount))
        .where(CostRecordModel.date >= month_start)
        .where(CostRecordModel.date <= today)
    )

    # Active anomalies
    anomaly_count = await db.execute(
        select(func.count(Anomaly.id))
        .where(Anomaly.acknowledged == False)
        .where(Anomaly.date >= today - timedelta(days=7))
    )

    # Total potential savings
    savings_result = await db.execute(
        select(func.sum(Recommendation.estimated_monthly_savings))
        .where(Recommendation.is_resolved == False)
    )

    return {
        "active_accounts": account_count.scalar() or 0,
        "mtd_spend": round(mtd_result.scalar() or 0, 2),
        "active_anomalies": anomaly_count.scalar() or 0,
        "potential_monthly_savings": round(savings_result.scalar() or 0, 2),
    }
