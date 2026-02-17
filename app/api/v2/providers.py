"""
v2 Providers API — Multi-Cloud Account Management

CRUD endpoints for connecting and managing cloud accounts across
AWS, GCP, and Azure. Also provides ingestion trigger endpoints.

Endpoints:
    GET    /api/v2/cloud_accounts          - List all cloud accounts
    POST   /api/v2/cloud_accounts          - Connect a new cloud account
    GET    /api/v2/cloud_accounts/{id}     - Get account details
    PUT    /api/v2/cloud_accounts/{id}     - Update account
    DELETE /api/v2/cloud_accounts/{id}     - Disconnect account
    POST   /api/v2/cloud_accounts/{id}/sync - Trigger data sync
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.providers import CloudAccount, CloudProvider, AccountSyncStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cloud_accounts", tags=["Cloud Accounts"])


# --- Schemas ---

class CloudAccountCreate(BaseModel):
    provider: str = Field(..., description="Cloud provider: aws, gcp, azure")
    account_identifier: str = Field(..., description="Account/project/subscription ID")
    display_name: Optional[str] = None
    connection_config: dict = Field(default_factory=dict, description="Provider-specific connection details")


class CloudAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    connection_config: Optional[dict] = None


class CloudAccountResponse(BaseModel):
    id: str
    provider: str
    account_identifier: str
    display_name: Optional[str]
    status: str
    last_sync_at: Optional[str]
    last_sync_rows: Optional[str]
    sync_error: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class SyncResponse(BaseModel):
    status: str
    rows_ingested: int = 0
    message: str = ""


# --- Endpoints ---

@router.get("", response_model=list[CloudAccountResponse])
async def list_cloud_accounts(
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all connected cloud accounts, optionally filtered by provider."""
    query = select(CloudAccount)
    if provider:
        query = query.where(CloudAccount.provider == provider)
    query = query.order_by(CloudAccount.created_at.desc())

    result = await db.execute(query)
    accounts = result.scalars().all()

    return [
        CloudAccountResponse(
            id=str(a.id),
            provider=a.provider.value,
            account_identifier=a.account_identifier,
            display_name=a.display_name,
            status=a.status.value,
            last_sync_at=a.last_sync_at.isoformat() if a.last_sync_at else None,
            last_sync_rows=a.last_sync_rows,
            sync_error=a.sync_error,
            created_at=a.created_at.isoformat(),
        )
        for a in accounts
    ]


@router.post("", response_model=CloudAccountResponse, status_code=201)
async def create_cloud_account(
    payload: CloudAccountCreate,
    db: AsyncSession = Depends(get_db),
):
    """Connect a new cloud account."""
    # Validate provider
    try:
        provider = CloudProvider(payload.provider)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider: {payload.provider}. Must be one of: aws, gcp, azure",
        )

    account = CloudAccount(
        provider=provider,
        account_identifier=payload.account_identifier,
        display_name=payload.display_name,
        connection_config=payload.connection_config,
        status=AccountSyncStatus.PENDING,
    )

    db.add(account)
    await db.flush()
    await db.refresh(account)

    return CloudAccountResponse(
        id=str(account.id),
        provider=account.provider.value,
        account_identifier=account.account_identifier,
        display_name=account.display_name,
        status=account.status.value,
        last_sync_at=None,
        last_sync_rows=None,
        sync_error=None,
        created_at=account.created_at.isoformat(),
    )


@router.get("/{account_id}", response_model=CloudAccountResponse)
async def get_cloud_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get details for a specific cloud account."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return CloudAccountResponse(
        id=str(account.id),
        provider=account.provider.value,
        account_identifier=account.account_identifier,
        display_name=account.display_name,
        status=account.status.value,
        last_sync_at=account.last_sync_at.isoformat() if account.last_sync_at else None,
        last_sync_rows=account.last_sync_rows,
        sync_error=account.sync_error,
        created_at=account.created_at.isoformat(),
    )


@router.put("/{account_id}", response_model=CloudAccountResponse)
async def update_cloud_account(
    account_id: str,
    payload: CloudAccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a cloud account's display name or connection config."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if payload.display_name is not None:
        account.display_name = payload.display_name
    if payload.connection_config is not None:
        account.connection_config = payload.connection_config

    await db.flush()
    await db.refresh(account)

    return CloudAccountResponse(
        id=str(account.id),
        provider=account.provider.value,
        account_identifier=account.account_identifier,
        display_name=account.display_name,
        status=account.status.value,
        last_sync_at=account.last_sync_at.isoformat() if account.last_sync_at else None,
        last_sync_rows=account.last_sync_rows,
        sync_error=account.sync_error,
        created_at=account.created_at.isoformat(),
    )


@router.delete("/{account_id}")
async def delete_cloud_account(
    account_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a cloud account."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    account.status = AccountSyncStatus.DISCONNECTED
    await db.flush()

    return {"message": "Account disconnected successfully"}


@router.post("/{account_id}/sync", response_model=SyncResponse)
async def sync_cloud_account(
    account_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a data sync for a cloud account.

    Downloads billing data, normalizes to FOCUS schema, and writes Parquet.
    """
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Default date range: last 30 days
    from datetime import date, timedelta
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).isoformat()

    account.status = AccountSyncStatus.SYNCING
    await db.flush()

    try:
        rows = 0
        config = account.connection_config or {}

        if account.provider == CloudProvider.AWS:
            from app.services.cur_ingestor import CURIngestor
            ingestor = CURIngestor(
                role_arn=config.get("role_arn"),
                external_id=config.get("external_id"),
                bucket=config.get("cur_bucket"),
                prefix=config.get("cur_prefix"),
                report_name=config.get("cur_report_name"),
            )
            result_data = ingestor.ingest()
            rows = result_data.get("total_rows", 0)

        elif account.provider == CloudProvider.GCP:
            from app.services.gcp_connector import GCPBillingConnector
            connector = GCPBillingConnector(
                service_account_json=config.get("service_account_json"),
                billing_dataset=config.get("billing_dataset"),
            )
            result_data = connector.ingest(start_date=start_date, end_date=end_date)
            rows = result_data.get("rows_ingested", 0)

        elif account.provider == CloudProvider.AZURE:
            from app.services.azure_connector import AzureCostConnector
            connector = AzureCostConnector(
                client_id=config.get("client_id"),
                client_secret=config.get("client_secret"),
                tenant_id=config.get("tenant_id"),
                storage_account=config.get("storage_account"),
                container=config.get("container"),
            )
            result_data = connector.ingest(start_date=start_date, end_date=end_date)
            rows = result_data.get("rows_ingested", 0)

        # Refresh DuckDB views
        from app.services.duckdb_engine import get_duckdb_engine
        engine = get_duckdb_engine()
        engine.refresh_views()

        account.status = AccountSyncStatus.ACTIVE
        account.last_sync_at = datetime.utcnow()
        account.last_sync_rows = str(rows)
        account.sync_error = None
        await db.flush()

        return SyncResponse(
            status="success",
            rows_ingested=rows,
            message=f"Synced {rows} billing records from {account.provider.value}",
        )

    except Exception as e:
        logger.error(f"Sync failed for {account_id}: {e}")
        account.status = AccountSyncStatus.ERROR
        account.sync_error = str(e)
        await db.flush()

        return SyncResponse(
            status="error",
            rows_ingested=0,
            message=str(e),
        )
