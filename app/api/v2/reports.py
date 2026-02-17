"""
Resource Reports, Network Flow Reports, Financial Commitment Reports,
and Kubernetes Efficiency Reports endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import (
    ResourceReport, NetworkFlowReport, FinancialCommitmentReport,
    KubernetesEfficiencyReport, Workspace,
)
from app.api.v2.schemas import (
    ResourceReportCreate, ResourceReportUpdate, ResourceReportResponse, ResourceReportListResponse,
    NetworkFlowReportCreate, NetworkFlowReportUpdate, NetworkFlowReportResponse, NetworkFlowReportListResponse,
    FinancialCommitmentReportCreate, FinancialCommitmentReportUpdate,
    FinancialCommitmentReportResponse, FinancialCommitmentReportListResponse,
    KubernetesEfficiencyReportCreate, KubernetesEfficiencyReportUpdate,
    KubernetesEfficiencyReportResponse, KubernetesEfficiencyReportListResponse,
    MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(tags=["Reports"])


# -----------------------------------------------------------------------
# Generic CRUD factory (avoids repeating boilerplate for each report type)
# -----------------------------------------------------------------------

def _enum_val(v):
    return v.value if hasattr(v, "value") else v


# -----------------------------------------------------------------------
# Resource Reports
# -----------------------------------------------------------------------

@router.get("/resource_reports", response_model=ResourceReportListResponse)
async def list_resource_reports(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(ResourceReport.workspace_id == ws.id)
    items, total = await paginated_query(db, ResourceReport, page, limit, filters=filters)
    return ResourceReportListResponse(
        resource_reports=[ResourceReportResponse.model_validate(r) for r in items],
        links=pagination_links("/v2/resource_reports", page, limit, total),
    )


@router.post("/resource_reports", response_model=ResourceReportResponse, status_code=201)
async def create_resource_report(
    payload: ResourceReportCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    rr = ResourceReport(
        token=generate_token("rr"), workspace_id=ws.id,
        title=payload.title, filter=payload.filter,
        groupings=payload.groupings, columns=payload.columns,
    )
    db.add(rr)
    await db.flush()
    await db.refresh(rr)
    return ResourceReportResponse.model_validate(rr)


@router.get("/resource_reports/{token}", response_model=ResourceReportResponse)
async def get_resource_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ResourceReportResponse.model_validate(await get_by_token(db, ResourceReport, token))


@router.put("/resource_reports/{token}", response_model=ResourceReportResponse)
async def update_resource_report(token: str, payload: ResourceReportUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rr = await get_by_token(db, ResourceReport, token)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(rr, k, v)
    await db.flush()
    await db.refresh(rr)
    return ResourceReportResponse.model_validate(rr)


@router.delete("/resource_reports/{token}", response_model=MessageResponse)
async def delete_resource_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rr = await get_by_token(db, ResourceReport, token)
    await db.delete(rr)
    await db.flush()
    return MessageResponse(message="Resource report deleted")


# -----------------------------------------------------------------------
# Network Flow Reports
# -----------------------------------------------------------------------

@router.get("/network_flow_reports", response_model=NetworkFlowReportListResponse)
async def list_network_flow_reports(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(NetworkFlowReport.workspace_id == ws.id)
    items, total = await paginated_query(db, NetworkFlowReport, page, limit, filters=filters)
    return NetworkFlowReportListResponse(
        network_flow_reports=[NetworkFlowReportResponse(
            token=r.token, title=r.title, filter=r.filter,
            date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
            start_date=r.start_date, end_date=r.end_date, created_at=r.created_at,
        ) for r in items],
        links=pagination_links("/v2/network_flow_reports", page, limit, total),
    )


@router.post("/network_flow_reports", response_model=NetworkFlowReportResponse, status_code=201)
async def create_network_flow_report(
    payload: NetworkFlowReportCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    nfr = NetworkFlowReport(
        token=generate_token("nfr"), workspace_id=ws.id,
        title=payload.title, filter=payload.filter,
        date_interval=payload.date_interval, date_bucket=payload.date_bucket,
        start_date=payload.start_date, end_date=payload.end_date,
    )
    db.add(nfr)
    await db.flush()
    await db.refresh(nfr)
    return NetworkFlowReportResponse(
        token=nfr.token, title=nfr.title, filter=nfr.filter,
        date_interval=_enum_val(nfr.date_interval), date_bucket=_enum_val(nfr.date_bucket),
        start_date=nfr.start_date, end_date=nfr.end_date, created_at=nfr.created_at,
    )


@router.get("/network_flow_reports/{token}", response_model=NetworkFlowReportResponse)
async def get_network_flow_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, NetworkFlowReport, token)
    return NetworkFlowReportResponse(
        token=r.token, title=r.title, filter=r.filter,
        date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
        start_date=r.start_date, end_date=r.end_date, created_at=r.created_at,
    )


@router.delete("/network_flow_reports/{token}", response_model=MessageResponse)
async def delete_network_flow_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, NetworkFlowReport, token)
    await db.delete(r)
    await db.flush()
    return MessageResponse(message="Network flow report deleted")


# -----------------------------------------------------------------------
# Financial Commitment Reports
# -----------------------------------------------------------------------

@router.get("/financial_commitment_reports", response_model=FinancialCommitmentReportListResponse)
async def list_financial_commitment_reports(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(FinancialCommitmentReport.workspace_id == ws.id)
    items, total = await paginated_query(db, FinancialCommitmentReport, page, limit, filters=filters)
    return FinancialCommitmentReportListResponse(
        financial_commitment_reports=[FinancialCommitmentReportResponse(
            token=r.token, title=r.title, filter=r.filter,
            date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
            groupings=r.groupings, on_demand_costs_scope=r.on_demand_costs_scope,
            start_date=r.start_date, end_date=r.end_date, created_at=r.created_at,
        ) for r in items],
        links=pagination_links("/v2/financial_commitment_reports", page, limit, total),
    )


@router.post("/financial_commitment_reports", response_model=FinancialCommitmentReportResponse, status_code=201)
async def create_financial_commitment_report(
    payload: FinancialCommitmentReportCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    fcr = FinancialCommitmentReport(
        token=generate_token("fcr"), workspace_id=ws.id,
        title=payload.title, filter=payload.filter,
        date_interval=payload.date_interval, date_bucket=payload.date_bucket,
        groupings=payload.groupings, on_demand_costs_scope=payload.on_demand_costs_scope,
        start_date=payload.start_date, end_date=payload.end_date,
    )
    db.add(fcr)
    await db.flush()
    await db.refresh(fcr)
    return FinancialCommitmentReportResponse(
        token=fcr.token, title=fcr.title, filter=fcr.filter,
        date_interval=_enum_val(fcr.date_interval), date_bucket=_enum_val(fcr.date_bucket),
        groupings=fcr.groupings, on_demand_costs_scope=fcr.on_demand_costs_scope,
        start_date=fcr.start_date, end_date=fcr.end_date, created_at=fcr.created_at,
    )


@router.get("/financial_commitment_reports/{token}", response_model=FinancialCommitmentReportResponse)
async def get_financial_commitment_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, FinancialCommitmentReport, token)
    return FinancialCommitmentReportResponse(
        token=r.token, title=r.title, filter=r.filter,
        date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
        groupings=r.groupings, on_demand_costs_scope=r.on_demand_costs_scope,
        start_date=r.start_date, end_date=r.end_date, created_at=r.created_at,
    )


@router.delete("/financial_commitment_reports/{token}", response_model=MessageResponse)
async def delete_financial_commitment_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, FinancialCommitmentReport, token)
    await db.delete(r)
    await db.flush()
    return MessageResponse(message="Financial commitment report deleted")


# -----------------------------------------------------------------------
# Kubernetes Efficiency Reports
# -----------------------------------------------------------------------

@router.get("/kubernetes_efficiency_reports", response_model=KubernetesEfficiencyReportListResponse)
async def list_kubernetes_efficiency_reports(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(KubernetesEfficiencyReport.workspace_id == ws.id)
    items, total = await paginated_query(db, KubernetesEfficiencyReport, page, limit, filters=filters)
    return KubernetesEfficiencyReportListResponse(
        kubernetes_efficiency_reports=[KubernetesEfficiencyReportResponse(
            token=r.token, title=r.title, cluster_id=r.cluster_id, filter=r.filter,
            date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
            aggregation=r.aggregation, created_at=r.created_at,
        ) for r in items],
        links=pagination_links("/v2/kubernetes_efficiency_reports", page, limit, total),
    )


@router.post("/kubernetes_efficiency_reports", response_model=KubernetesEfficiencyReportResponse, status_code=201)
async def create_kubernetes_efficiency_report(
    payload: KubernetesEfficiencyReportCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    ker = KubernetesEfficiencyReport(
        token=generate_token("ker"), workspace_id=ws.id,
        title=payload.title, cluster_id=payload.cluster_id,
        filter=payload.filter, date_interval=payload.date_interval,
        date_bucket=payload.date_bucket, aggregation=payload.aggregation,
    )
    db.add(ker)
    await db.flush()
    await db.refresh(ker)
    return KubernetesEfficiencyReportResponse(
        token=ker.token, title=ker.title, cluster_id=ker.cluster_id, filter=ker.filter,
        date_interval=_enum_val(ker.date_interval), date_bucket=_enum_val(ker.date_bucket),
        aggregation=ker.aggregation, created_at=ker.created_at,
    )


@router.get("/kubernetes_efficiency_reports/{token}", response_model=KubernetesEfficiencyReportResponse)
async def get_kubernetes_efficiency_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, KubernetesEfficiencyReport, token)
    return KubernetesEfficiencyReportResponse(
        token=r.token, title=r.title, cluster_id=r.cluster_id, filter=r.filter,
        date_interval=_enum_val(r.date_interval), date_bucket=_enum_val(r.date_bucket),
        aggregation=r.aggregation, created_at=r.created_at,
    )


@router.delete("/kubernetes_efficiency_reports/{token}", response_model=MessageResponse)
async def delete_kubernetes_efficiency_report(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await get_by_token(db, KubernetesEfficiencyReport, token)
    await db.delete(r)
    await db.flush()
    return MessageResponse(message="Kubernetes efficiency report deleted")
