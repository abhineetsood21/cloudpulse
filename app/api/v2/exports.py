"""Data Export and Unit Cost endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import DataExport, UnitCost, Workspace, CostReport
from app.api.v2.schemas import (
    DataExportCreate, DataExportResponse, DataExportListResponse,
    UnitCostCreate, UnitCostResponse, UnitCostListResponse,
    MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(tags=["Exports"])


# --- Data Exports ---

@router.get("/data_exports", response_model=DataExportListResponse)
async def list_data_exports(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(DataExport.workspace_id == ws.id)
    items, total = await paginated_query(db, DataExport, page, limit, filters=filters)

    def _enum_val(v):
        return v.value if hasattr(v, "value") else v

    return DataExportListResponse(
        data_exports=[DataExportResponse(
            token=e.token, export_type=e.export_type,
            schema_type=_enum_val(e.schema_type), status=_enum_val(e.status),
            file_url=e.file_url, created_at=e.created_at, completed_at=e.completed_at,
        ) for e in items],
        links=pagination_links("/v2/data_exports", page, limit, total),
    )


@router.post("/data_exports", response_model=DataExportResponse, status_code=201)
async def create_data_export(
    payload: DataExportCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    export = DataExport(
        token=generate_token("exp"), workspace_id=ws.id,
        export_type=payload.export_type, schema_type=payload.schema_type,
        filter=payload.filter, start_date=payload.start_date, end_date=payload.end_date,
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)

    def _enum_val(v):
        return v.value if hasattr(v, "value") else v

    return DataExportResponse(
        token=export.token, export_type=export.export_type,
        schema_type=_enum_val(export.schema_type), status=_enum_val(export.status),
        file_url=export.file_url, created_at=export.created_at, completed_at=export.completed_at,
    )


@router.get("/data_exports/{token}", response_model=DataExportResponse)
async def get_data_export(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    e = await get_by_token(db, DataExport, token)

    def _enum_val(v):
        return v.value if hasattr(v, "value") else v

    return DataExportResponse(
        token=e.token, export_type=e.export_type,
        schema_type=_enum_val(e.schema_type), status=_enum_val(e.status),
        file_url=e.file_url, created_at=e.created_at, completed_at=e.completed_at,
    )


# --- Unit Costs ---

@router.get("/unit_costs", response_model=UnitCostListResponse)
async def list_unit_costs(
    cost_report_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if cost_report_token:
        report = await get_by_token(db, CostReport, cost_report_token)
        filters.append(UnitCost.cost_report_id == report.id)
    items, total = await paginated_query(db, UnitCost, page, limit, filters=filters)
    return UnitCostListResponse(
        unit_costs=[UnitCostResponse(
            id=uc.id, date=uc.date, per_unit_amount=uc.per_unit_amount,
            unit_label=uc.unit_label, total_cost=uc.total_cost,
            total_units=uc.total_units, currency=uc.currency,
            cost_report_token=uc.cost_report.token if uc.cost_report else None,
        ) for uc in items],
        links=pagination_links("/v2/unit_costs", page, limit, total),
    )


@router.post("/unit_costs", response_model=UnitCostResponse, status_code=201)
async def create_unit_cost(
    payload: UnitCostCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_by_token(db, CostReport, payload.cost_report_token)
    uc = UnitCost(
        cost_report_id=report.id,
        date=payload.date, per_unit_amount=payload.per_unit_amount,
        unit_label=payload.unit_label, total_cost=payload.total_cost,
        total_units=payload.total_units, currency=payload.currency,
    )
    db.add(uc)
    await db.flush()
    await db.refresh(uc)
    return UnitCostResponse(
        id=uc.id, date=uc.date, per_unit_amount=uc.per_unit_amount,
        unit_label=uc.unit_label, total_cost=uc.total_cost,
        total_units=uc.total_units, currency=uc.currency,
        cost_report_token=report.token,
    )


@router.delete("/unit_costs/{unit_cost_id}", response_model=MessageResponse)
async def delete_unit_cost(
    unit_cost_id: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import select
    result = await db.execute(select(UnitCost).where(UnitCost.id == unit_cost_id))
    uc = result.scalar_one_or_none()
    if not uc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Unit cost not found")
    await db.delete(uc)
    await db.flush()
    return MessageResponse(message="Unit cost deleted")
