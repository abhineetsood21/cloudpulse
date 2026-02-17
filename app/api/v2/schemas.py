"""
CloudPulse v2 API Pydantic Schemas.

Request/response models for all v2 endpoints.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Pagination ---

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=25, ge=1, le=500)


class PaginatedResponse(BaseModel):
    links: dict = {}  # {"self": ..., "next": ..., "prev": ...}


# --- Workspaces ---

class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)


class WorkspaceResponse(BaseModel):
    token: str
    name: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkspaceListResponse(PaginatedResponse):
    workspaces: list[WorkspaceResponse]


# --- Cost Reports ---

class CostReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    folder_token: str | None = None
    saved_filter_token: str | None = None
    filter: str | None = None  # CQL expression
    groupings: str = "service"
    date_interval: str = "last_30_days"
    date_bucket: str = "day"
    start_date: date | None = None
    end_date: date | None = None
    settings: dict = {}


class CostReportUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    filter: str | None = None
    folder_token: str | None = None
    saved_filter_token: str | None = None
    groupings: str | None = None
    date_interval: str | None = None
    date_bucket: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    settings: dict | None = None


class CostReportResponse(BaseModel):
    token: str
    title: str
    workspace_token: str | None = None
    folder_token: str | None = None
    filter: str | None = None
    groupings: str
    date_interval: str
    date_bucket: str
    start_date: date | None = None
    end_date: date | None = None
    settings: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class CostReportListResponse(PaginatedResponse):
    cost_reports: list[CostReportResponse]


# --- Folders ---

class FolderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    parent_folder_token: str | None = None


class FolderUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    parent_folder_token: str | None = None


class FolderResponse(BaseModel):
    token: str
    title: str
    workspace_token: str | None = None
    parent_folder_token: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FolderListResponse(PaginatedResponse):
    folders: list[FolderResponse]


# --- Saved Filters ---

class SavedFilterCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    filter: str  # CQL expression


class SavedFilterUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    filter: str | None = None


class SavedFilterResponse(BaseModel):
    token: str
    title: str
    filter: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SavedFilterListResponse(PaginatedResponse):
    saved_filters: list[SavedFilterResponse]


# --- Dashboards ---

class DashboardCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    widgets: list[dict] = []
    date_interval: str = "last_30_days"
    start_date: date | None = None
    end_date: date | None = None


class DashboardUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    widgets: list[dict] | None = None
    date_interval: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class DashboardResponse(BaseModel):
    token: str
    title: str
    widgets: list[dict]
    date_interval: str
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardListResponse(PaginatedResponse):
    dashboards: list[DashboardResponse]


# --- Segments ---

class SegmentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    parent_segment_token: str | None = None
    description: str | None = None
    filter: str | None = None
    priority: int = 0
    track_unallocated: bool = False


class SegmentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    filter: str | None = None
    priority: int | None = None
    track_unallocated: bool | None = None


class SegmentResponse(BaseModel):
    token: str
    title: str
    description: str | None = None
    filter: str | None = None
    priority: int
    track_unallocated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SegmentListResponse(PaginatedResponse):
    segments: list[SegmentResponse]


# --- Teams ---

class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    workspace_token: str
    description: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None


class TeamResponse(BaseModel):
    token: str
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamListResponse(PaginatedResponse):
    teams: list[TeamResponse]


# --- Access Grants ---

class AccessGrantCreate(BaseModel):
    team_token: str
    resource_type: str  # cost_report, folder, dashboard, segment
    resource_token: str
    access_level: str = "viewer"  # viewer, editor, admin


class AccessGrantResponse(BaseModel):
    token: str
    team_token: str | None = None
    resource_type: str
    resource_token: str
    access_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AccessGrantListResponse(PaginatedResponse):
    access_grants: list[AccessGrantResponse]


# --- Virtual Tags ---

class VirtualTagValue(BaseModel):
    name: str
    filter: str  # CQL expression


class VirtualTagCreate(BaseModel):
    key: str = Field(min_length=1, max_length=255)
    workspace_token: str
    description: str | None = None
    overridable: bool = True
    backfill_until: date | None = None
    values: list[VirtualTagValue] = []


class VirtualTagUpdate(BaseModel):
    key: str | None = Field(default=None, max_length=255)
    description: str | None = None
    overridable: bool | None = None
    backfill_until: date | None = None
    values: list[VirtualTagValue] | None = None


class VirtualTagResponse(BaseModel):
    token: str
    key: str
    description: str | None = None
    overridable: bool
    backfill_until: date | None = None
    values: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class VirtualTagListResponse(PaginatedResponse):
    virtual_tags: list[VirtualTagResponse]


# --- API Tokens ---

class APITokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    scopes: str = "read"  # comma-separated: read, write


class APITokenResponse(BaseModel):
    token_prefix: str
    name: str
    scopes: str
    is_active: bool
    last_used_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class APITokenCreatedResponse(APITokenResponse):
    """Returned only on creation — includes the full token."""
    token: str


class APITokenListResponse(PaginatedResponse):
    api_tokens: list[APITokenResponse]


# --- Resource Reports ---

class ResourceReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    filter: str | None = None
    groupings: str = "resource_id"
    columns: list[str] = []


class ResourceReportUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    filter: str | None = None
    groupings: str | None = None
    columns: list[str] | None = None


class ResourceReportResponse(BaseModel):
    token: str
    title: str
    filter: str | None = None
    groupings: str
    columns: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ResourceReportListResponse(PaginatedResponse):
    resource_reports: list[ResourceReportResponse]


# --- Network Flow Reports ---

class NetworkFlowReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    filter: str | None = None
    date_interval: str = "last_30_days"
    date_bucket: str = "day"
    start_date: date | None = None
    end_date: date | None = None


class NetworkFlowReportUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    filter: str | None = None
    date_interval: str | None = None
    date_bucket: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class NetworkFlowReportResponse(BaseModel):
    token: str
    title: str
    filter: str | None = None
    date_interval: str
    date_bucket: str
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NetworkFlowReportListResponse(PaginatedResponse):
    network_flow_reports: list[NetworkFlowReportResponse]


# --- Financial Commitment Reports ---

class FinancialCommitmentReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    filter: str | None = None
    date_interval: str = "last_3_months"
    date_bucket: str = "month"
    groupings: str = "cost_type"
    on_demand_costs_scope: str = "discountable"
    start_date: date | None = None
    end_date: date | None = None


class FinancialCommitmentReportUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    filter: str | None = None
    date_interval: str | None = None
    date_bucket: str | None = None
    groupings: str | None = None
    on_demand_costs_scope: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class FinancialCommitmentReportResponse(BaseModel):
    token: str
    title: str
    filter: str | None = None
    date_interval: str
    date_bucket: str
    groupings: str
    on_demand_costs_scope: str
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FinancialCommitmentReportListResponse(PaginatedResponse):
    financial_commitment_reports: list[FinancialCommitmentReportResponse]


# --- Kubernetes Efficiency Reports ---

class KubernetesEfficiencyReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    workspace_token: str
    cluster_id: str | None = None
    filter: str | None = None
    date_interval: str = "last_7_days"
    date_bucket: str = "day"
    aggregation: str = "namespace"


class KubernetesEfficiencyReportUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    cluster_id: str | None = None
    filter: str | None = None
    date_interval: str | None = None
    date_bucket: str | None = None
    aggregation: str | None = None


class KubernetesEfficiencyReportResponse(BaseModel):
    token: str
    title: str
    cluster_id: str | None = None
    filter: str | None = None
    date_interval: str
    date_bucket: str
    aggregation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class KubernetesEfficiencyReportListResponse(PaginatedResponse):
    kubernetes_efficiency_reports: list[KubernetesEfficiencyReportResponse]


# --- Data Exports ---

class DataExportCreate(BaseModel):
    workspace_token: str
    export_type: str  # cost_report, resource_report
    schema_type: str = "default"  # default, focus
    filter: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class DataExportResponse(BaseModel):
    token: str
    export_type: str
    schema_type: str
    status: str
    file_url: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DataExportListResponse(PaginatedResponse):
    data_exports: list[DataExportResponse]


# --- Unit Costs ---

class UnitCostCreate(BaseModel):
    cost_report_token: str
    date: date
    per_unit_amount: float
    unit_label: str
    total_cost: float
    total_units: float
    currency: str = "USD"


class UnitCostResponse(BaseModel):
    id: UUID
    date: date
    per_unit_amount: float
    unit_label: str
    total_cost: float
    total_units: float
    currency: str
    cost_report_token: str | None = None

    model_config = {"from_attributes": True}


class UnitCostListResponse(PaginatedResponse):
    unit_costs: list[UnitCostResponse]


# --- Generic ---

class MessageResponse(BaseModel):
    message: str
