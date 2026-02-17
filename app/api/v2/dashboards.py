"""Dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import DashboardModel, Workspace
from app.api.v2.schemas import (
    DashboardCreate, DashboardUpdate, DashboardResponse,
    DashboardListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


def _to_response(d: DashboardModel) -> DashboardResponse:
    return DashboardResponse(
        token=d.token, title=d.title, widgets=d.widgets or [],
        date_interval=d.date_interval.value if d.date_interval else "last_30_days",
        start_date=d.start_date, end_date=d.end_date, created_at=d.created_at,
    )


@router.get("", response_model=DashboardListResponse)
async def list_dashboards(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(DashboardModel.workspace_id == ws.id)
    items, total = await paginated_query(db, DashboardModel, page, limit, filters=filters)
    return DashboardListResponse(
        dashboards=[_to_response(d) for d in items],
        links=pagination_links("/v2/dashboards", page, limit, total),
    )


@router.post("", response_model=DashboardResponse, status_code=201)
async def create_dashboard(
    payload: DashboardCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    dash = DashboardModel(
        token=generate_token("dash"), workspace_id=ws.id,
        title=payload.title, widgets=payload.widgets,
        date_interval=payload.date_interval,
        start_date=payload.start_date, end_date=payload.end_date,
    )
    db.add(dash)
    await db.flush()
    await db.refresh(dash)
    return _to_response(dash)


@router.get("/{token}", response_model=DashboardResponse)
async def get_dashboard(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _to_response(await get_by_token(db, DashboardModel, token))


@router.put("/{token}", response_model=DashboardResponse)
async def update_dashboard(
    token: str, payload: DashboardUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    d = await get_by_token(db, DashboardModel, token)
    for field in ("title", "widgets", "date_interval", "start_date", "end_date"):
        val = getattr(payload, field, None)
        if val is not None:
            setattr(d, field, val)
    await db.flush()
    await db.refresh(d)
    return _to_response(d)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_dashboard(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    d = await get_by_token(db, DashboardModel, token)
    await db.delete(d)
    await db.flush()
    return MessageResponse(message="Dashboard deleted")
