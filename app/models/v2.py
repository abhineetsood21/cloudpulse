"""
CloudPulse v2 Data Models

Extended models for the Vantage-style v2 API, including:
Workspaces, Cost Reports, Folders, Saved Filters, Dashboards,
Segments, Teams, Access Grants, Virtual Tags, API Tokens,
Resource Reports, Network Flow Reports, Financial Commitment Reports.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Float, DateTime, Date, ForeignKey, Text, Enum,
    Boolean, Index, Integer, Table, JSON,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- Association Tables ---

workspace_members = Table(
    "workspace_members",
    Base.metadata,
    Column("workspace_id", UUID(as_uuid=True), ForeignKey("workspaces.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role", String(50), default="member"),  # owner, admin, editor, viewer
    Column("joined_at", DateTime, default=datetime.utcnow),
)

team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", UUID(as_uuid=True), ForeignKey("teams.id"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("role", String(50), default="member"),
    Column("joined_at", DateTime, default=datetime.utcnow),
)


# --- Enums ---

class ReportDateInterval(str, PyEnum):
    CUSTOM = "custom"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_12_MONTHS = "last_12_months"


class DateBucket(str, PyEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ExportSchema(str, PyEnum):
    DEFAULT = "default"
    FOCUS = "focus"


class ExportStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Models ---

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cost_reports = relationship("CostReport", back_populates="workspace", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="workspace", cascade="all, delete-orphan")
    dashboards = relationship("DashboardModel", back_populates="workspace", cascade="all, delete-orphan")


class CostReport(Base):
    __tablename__ = "cost_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    title = Column(String(255), nullable=False)
    filter = Column(Text, nullable=True)  # CQL filter expression
    saved_filter_id = Column(UUID(as_uuid=True), ForeignKey("saved_filters.id"), nullable=True)
    groupings = Column(String(255), default="service")  # service, region, account_id, tag
    date_interval = Column(Enum(ReportDateInterval), default=ReportDateInterval.LAST_30_DAYS)
    date_bucket = Column(Enum(DateBucket), default=DateBucket.DAY)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    settings = Column(JSON, default=dict)  # include_credits, include_refunds, amortize, etc.
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="cost_reports")
    folder = relationship("Folder", back_populates="cost_reports")
    saved_filter = relationship("SavedFilter")

    __table_args__ = (
        Index("ix_cost_reports_workspace", "workspace_id"),
    )


class Folder(Base):
    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="folders")
    parent = relationship("Folder", remote_side=[id])
    cost_reports = relationship("CostReport", back_populates="folder")


class SavedFilter(Base):
    __tablename__ = "saved_filters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filter = Column(Text, nullable=False)  # CQL expression
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DashboardModel(Base):
    __tablename__ = "v2_dashboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    widgets = Column(JSON, default=list)  # List of widget configurations
    date_interval = Column(Enum(ReportDateInterval), default=ReportDateInterval.LAST_30_DAYS)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="dashboards")


class Segment(Base):
    __tablename__ = "segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    parent_segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filter = Column(Text, nullable=True)  # CQL expression
    priority = Column(Integer, default=0)
    track_unallocated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Segment", remote_side=[id])

    __table_args__ = (
        Index("ix_segments_workspace", "workspace_id"),
    )


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessGrant(Base):
    __tablename__ = "access_grants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    resource_type = Column(String(100), nullable=False)  # cost_report, folder, dashboard, segment
    resource_token = Column(String(64), nullable=False)
    access_level = Column(String(50), default="viewer")  # viewer, editor, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")


class VirtualTag(Base):
    __tablename__ = "virtual_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    key = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    overridable = Column(Boolean, default=True)
    backfill_until = Column(Date, nullable=True)
    values = Column(JSON, default=list)  # [{filter: "CQL", name: "value_name"}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    token_prefix = Column(String(20), nullable=False)  # First 8 chars for identification
    token_type = Column(String(20), default="user")  # user, service
    scopes = Column(String(255), default="read")  # comma-separated: read,write
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

    @property
    def scopes_list(self) -> list[str]:
        return [s.strip() for s in (self.scopes or "").split(",")]


class ResourceReport(Base):
    __tablename__ = "resource_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filter = Column(Text, nullable=True)  # CQL expression
    groupings = Column(String(255), default="resource_id")
    columns = Column(JSON, default=list)  # Custom columns to display
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NetworkFlowReport(Base):
    __tablename__ = "network_flow_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filter = Column(Text, nullable=True)  # CQL expression
    date_interval = Column(Enum(ReportDateInterval), default=ReportDateInterval.LAST_30_DAYS)
    date_bucket = Column(Enum(DateBucket), default=DateBucket.DAY)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinancialCommitmentReport(Base):
    __tablename__ = "financial_commitment_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filter = Column(Text, nullable=True)  # CQL expression
    date_interval = Column(Enum(ReportDateInterval), default=ReportDateInterval.LAST_3_MONTHS)
    date_bucket = Column(Enum(DateBucket), default=DateBucket.MONTH)
    groupings = Column(String(255), default="cost_type")
    on_demand_costs_scope = Column(String(50), default="discountable")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KubernetesEfficiencyReport(Base):
    __tablename__ = "kubernetes_efficiency_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    title = Column(String(255), nullable=False)
    cluster_id = Column(String(255), nullable=True)
    filter = Column(Text, nullable=True)
    date_interval = Column(Enum(ReportDateInterval), default=ReportDateInterval.LAST_7_DAYS)
    date_bucket = Column(Enum(DateBucket), default=DateBucket.DAY)
    aggregation = Column(String(50), default="namespace")  # namespace, label, controller
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DataExport(Base):
    __tablename__ = "data_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(64), unique=True, nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    export_type = Column(String(50), nullable=False)  # cost_report, resource_report
    schema_type = Column(Enum(ExportSchema), default=ExportSchema.DEFAULT)
    status = Column(Enum(ExportStatus), default=ExportStatus.PENDING)
    filter = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    file_url = Column(Text, nullable=True)  # S3 URL once completed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class UnitCost(Base):
    __tablename__ = "unit_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_report_id = Column(UUID(as_uuid=True), ForeignKey("cost_reports.id"), nullable=False)
    date = Column(Date, nullable=False)
    per_unit_amount = Column(Float, nullable=False)
    unit_label = Column(String(100), nullable=False)  # e.g., "per request", "per GB"
    total_cost = Column(Float, nullable=False)
    total_units = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    cost_report = relationship("CostReport")

    __table_args__ = (
        Index("ix_unit_costs_report_date", "cost_report_id", "date"),
    )
