"""
Multi-Cloud Provider Models

Provider-agnostic cloud account model that replaces the AWS-only
AWSAccount for multi-cloud support.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, DateTime, Enum, Boolean, Index, Text, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class CloudProvider(str, PyEnum):
    # Cloud
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ORACLE = "oracle"
    LINODE = "linode"
    # Kubernetes
    KUBERNETES = "kubernetes"
    # Observability
    DATADOG = "datadog"
    NEW_RELIC = "new_relic"
    CORALOGIX = "coralogix"
    GRAFANA_CLOUD = "grafana_cloud"
    # Database
    MONGODB = "mongodb"
    SNOWFLAKE = "snowflake"
    DATABRICKS = "databricks"
    PLANETSCALE = "planetscale"
    CLICKHOUSE = "clickhouse"
    # AI / ML
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    ANYSCALE = "anyscale"
    CURSOR = "cursor"
    # DevTools
    GITHUB = "github"
    TEMPORAL_CLOUD = "temporal_cloud"
    TWILIO = "twilio"
    # CDN / Streaming
    FASTLY = "fastly"
    CONFLUENT = "confluent"
    CLOUDFLARE = "cloudflare"
    VERCEL = "vercel"
    # Custom
    CUSTOM = "custom"


class AccountSyncStatus(str, PyEnum):
    PENDING = "pending"
    SYNCING = "syncing"
    ACTIVE = "active"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class CloudAccount(Base):
    """
    Unified cloud account model supporting AWS, GCP, and Azure.

    Stores provider-specific credentials as encrypted JSON.
    """
    __tablename__ = "cloud_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(Enum(CloudProvider), nullable=False)
    account_identifier = Column(String(255), nullable=False)  # AWS account ID, GCP project ID, Azure subscription ID
    display_name = Column(String(255), nullable=True)
    status = Column(Enum(AccountSyncStatus), default=AccountSyncStatus.PENDING, nullable=False)

    # Provider-specific connection details (stored as JSON)
    # AWS: {"role_arn": "...", "external_id": "...", "cur_bucket": "...", "cur_prefix": "..."}
    # GCP: {"service_account_json": "...", "billing_dataset": "..."}
    # Azure: {"client_id": "...", "tenant_id": "...", "storage_account": "...", "container": "..."}
    connection_config = Column(JSON, default=dict)

    # Ingestion tracking
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_rows = Column(String(50), nullable=True)
    sync_error = Column(Text, nullable=True)

    # Metadata
    workspace_id = Column(UUID(as_uuid=True), nullable=True)  # v2 workspace association
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_cloud_accounts_provider", "provider"),
        Index("ix_cloud_accounts_workspace", "workspace_id"),
    )
