"""Cost Report endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import CostReport, Workspace, Folder, SavedFilter
from app.api.v2.schemas import (
    CostReportCreate, CostReportUpdate, CostReportResponse,
    CostReportListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/cost_reports", tags=["Cost Reports"])


def _to_response(report: CostReport) -> CostReportResponse:
    return CostReportResponse(
        token=report.token,
        title=report.title,
        workspace_token=report.workspace.token if report.workspace else None,
        folder_token=report.folder.token if report.folder else None,
        filter=report.filter,
        groupings=report.groupings,
        date_interval=report.date_interval.value if report.date_interval else "last_30_days",
        date_bucket=report.date_bucket.value if report.date_bucket else "day",
        start_date=report.start_date,
        end_date=report.end_date,
        settings=report.settings or {},
        created_at=report.created_at,
    )


@router.get("", response_model=CostReportListResponse)
async def list_cost_reports(
    workspace_token: str | None = None,
    page: int = 1,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(CostReport.workspace_id == ws.id)

    items, total = await paginated_query(db, CostReport, page, limit, filters=filters)
    return CostReportListResponse(
        cost_reports=[_to_response(r) for r in items],
        links=pagination_links("/v2/cost_reports", page, limit, total),
    )


@router.post("", response_model=CostReportResponse, status_code=201)
async def create_cost_report(
    payload: CostReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)

    folder_id = None
    if payload.folder_token:
        folder = await get_by_token(db, Folder, payload.folder_token)
        folder_id = folder.id

    saved_filter_id = None
    if payload.saved_filter_token:
        sf = await get_by_token(db, SavedFilter, payload.saved_filter_token)
        saved_filter_id = sf.id

    report = CostReport(
        token=generate_token("rpt"),
        workspace_id=ws.id,
        folder_id=folder_id,
        saved_filter_id=saved_filter_id,
        title=payload.title,
        filter=payload.filter,
        groupings=payload.groupings,
        date_interval=payload.date_interval,
        date_bucket=payload.date_bucket,
        start_date=payload.start_date,
        end_date=payload.end_date,
        settings=payload.settings,
        created_by=current_user.id,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return _to_response(report)


@router.get("/{token}", response_model=CostReportResponse)
async def get_cost_report(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_by_token(db, CostReport, token)
    return _to_response(report)


@router.put("/{token}", response_model=CostReportResponse)
async def update_cost_report(
    token: str,
    payload: CostReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_by_token(db, CostReport, token)
    update_data = payload.model_dump(exclude_unset=True)

    if "folder_token" in update_data:
        if update_data["folder_token"]:
            folder = await get_by_token(db, Folder, update_data.pop("folder_token"))
            report.folder_id = folder.id
        else:
            update_data.pop("folder_token")
            report.folder_id = None

    if "saved_filter_token" in update_data:
        if update_data["saved_filter_token"]:
            sf = await get_by_token(db, SavedFilter, update_data.pop("saved_filter_token"))
            report.saved_filter_id = sf.id
        else:
            update_data.pop("saved_filter_token")
            report.saved_filter_id = None

    for key, value in update_data.items():
        setattr(report, key, value)

    await db.flush()
    await db.refresh(report)
    return _to_response(report)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_cost_report(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_by_token(db, CostReport, token)
    await db.delete(report)
    await db.flush()
    return MessageResponse(message="Cost report deleted")
