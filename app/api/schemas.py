"""Pydantic schemas for API request/response validation."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.models import PlanTier, AccountStatus, AlertChannel, AnomalySeverity, ResourceType, BudgetPeriod


# --- User ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: UUID
    email: str
    plan: PlanTier
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- AWS Account ---

class AWSAccountCreate(BaseModel):
    aws_account_id: str = Field(pattern=r"^\d{12}$", description="12-digit AWS account ID")
    role_arn: str = Field(pattern=r"^arn:aws:iam::\d{12}:role/.+$")
    account_name: str | None = None


class AWSAccountResponse(BaseModel):
    id: UUID
    aws_account_id: str
    role_arn: str
    account_name: str | None
    status: AccountStatus
    last_sync_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Cost Data ---

class CostQuery(BaseModel):
    start_date: date
    end_date: date
    granularity: str = "DAILY"  # DAILY, WEEKLY, MONTHLY


class CostRecord(BaseModel):
    date: str
    service: str
    amount: float
    currency: str = "USD"


class CostSummary(BaseModel):
    total_spend: float
    currency: str = "USD"
    period_start: str
    period_end: str
    by_service: list[CostRecord]
    daily_totals: list[dict]


class CostForecast(BaseModel):
    total_forecast: float
    currency: str
    start: str
    end: str
    mtd_spend: float = 0
    daily_avg: float = 0
    days_remaining: int = 0
    projected_total: float = 0
    source: str = "linear"  # "aws" or "linear"


# --- Cost Drill-Down ("Why?") ---

class ServiceChange(BaseModel):
    service: str
    current_amount: float
    previous_amount: float
    change: float
    change_pct: float
    impact_pct: float
    direction: str  # "increase" or "decrease"


class PeriodSummary(BaseModel):
    start: str
    end: str
    total: float


class DrillDownResponse(BaseModel):
    current_period: PeriodSummary
    previous_period: PeriodSummary
    total_change: float
    total_change_pct: float
    direction: str  # "increase", "decrease", "unchanged"
    service_changes: list[ServiceChange]
    top_increases: list[ServiceChange]
    top_decreases: list[ServiceChange]
    new_services: list[ServiceChange]
    removed_services: list[ServiceChange]


# --- Anomalies ---

class AnomalyResponse(BaseModel):
    id: UUID
    date: date
    service: str
    expected_amount: float
    actual_amount: float
    deviation_pct: float
    severity: AnomalySeverity
    acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Recommendations ---

class RecommendationResponse(BaseModel):
    id: UUID
    resource_type: ResourceType
    resource_id: str
    region: str
    recommendation: str
    estimated_monthly_savings: float
    is_resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Alert Config ---

class AlertConfigCreate(BaseModel):
    channel: AlertChannel
    email_address: str | None = None
    slack_webhook_url: str | None = None
    notify_info: bool = False
    notify_warning: bool = True
    notify_critical: bool = True
    daily_summary: bool = True


class AlertConfigResponse(BaseModel):
    id: UUID
    channel: AlertChannel
    is_enabled: bool
    email_address: str | None
    slack_webhook_url: str | None
    notify_info: bool
    notify_warning: bool
    notify_critical: bool
    daily_summary: bool

    model_config = {"from_attributes": True}


# --- Budgets ---

class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    amount: float = Field(gt=0, description="Budget limit in USD")
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    service_filter: str | None = None
    alert_at_pct: float = Field(default=0.80, ge=0.01, le=1.0)


class BudgetUpdate(BaseModel):
    name: str | None = None
    amount: float | None = Field(default=None, gt=0)
    period: BudgetPeriod | None = None
    service_filter: str | None = None
    alert_at_pct: float | None = Field(default=None, ge=0.01, le=1.0)
    is_active: bool | None = None


class BudgetResponse(BaseModel):
    id: UUID
    aws_account_id: UUID
    name: str
    amount: float
    period: BudgetPeriod
    service_filter: str | None
    alert_at_pct: float
    is_active: bool
    current_spend: float
    last_checked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @property
    def pct_used(self) -> float:
        return self.current_spend / self.amount if self.amount > 0 else 0


# --- Auth ---

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Generic ---

class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
