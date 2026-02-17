"""
v2 Integrations API — Unified Provider Management

Full integration lifecycle: catalog discovery, credential validation,
connection management, and cost data synchronization for all 28 providers.

Endpoints:
    GET    /api/v2/integrations/catalog      - Provider catalog (drives frontend)
    GET    /api/v2/integrations              - List active integrations
    POST   /api/v2/integrations/connect      - Connect a new provider
    POST   /api/v2/integrations/{id}/validate - Test credentials
    POST   /api/v2/integrations/{id}/sync    - Trigger cost sync
    DELETE /api/v2/integrations/{id}         - Disconnect
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.providers import CloudAccount, CloudProvider, AccountSyncStatus
from app.services.provider_registry import (
    get_catalog_grouped, get_provider, PROVIDER_CATALOG,
)
from app.services.connectors import get_connector
from app.api.v2.webhooks import dispatch_event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ── Schemas ───────────────────────────────────────────────────────

class ConnectRequest(BaseModel):
    provider: str = Field(..., description="Provider key, e.g. 'datadog'")
    display_name: Optional[str] = None
    credentials: dict = Field(..., description="Credential fields matching the provider's required_fields")


class IntegrationResponse(BaseModel):
    id: str
    provider: str
    provider_display_name: str
    display_name: Optional[str]
    status: str
    last_sync_at: Optional[str]
    last_sync_rows: Optional[str]
    sync_error: Optional[str]
    created_at: str


class SyncResponse(BaseModel):
    status: str
    rows_ingested: int = 0
    message: str = ""


class ValidateResponse(BaseModel):
    valid: bool
    error: Optional[str] = None
    account_identifier: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────

def _to_response(account: CloudAccount) -> IntegrationResponse:
    provider_info = get_provider(account.provider.value) or {}
    return IntegrationResponse(
        id=str(account.id),
        provider=account.provider.value,
        provider_display_name=provider_info.get("display_name", account.provider.value),
        display_name=account.display_name,
        status=account.status.value,
        last_sync_at=account.last_sync_at.isoformat() if account.last_sync_at else None,
        last_sync_rows=account.last_sync_rows,
        sync_error=account.sync_error,
        created_at=account.created_at.isoformat(),
    )


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/catalog")
async def get_integration_catalog():
    """
    Return the full provider catalog grouped by category.

    The frontend renders the entire Integrations page from this response.
    """
    return {"categories": get_catalog_grouped()}


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    provider: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all active integrations, optionally filtered by provider."""
    query = select(CloudAccount).where(
        CloudAccount.status != AccountSyncStatus.DISCONNECTED
    )
    if provider:
        query = query.where(CloudAccount.provider == provider)
    query = query.order_by(CloudAccount.created_at.desc())

    result = await db.execute(query)
    accounts = result.scalars().all()
    return [_to_response(a) for a in accounts]


@router.post("/connect", response_model=IntegrationResponse, status_code=201)
async def connect_integration(
    payload: ConnectRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Connect a new provider.

    Validates credentials via the connector, then stores the connection.
    """
    # Validate provider key
    provider_info = get_provider(payload.provider)
    if not provider_info:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {payload.provider}")

    if provider_info.get("status") == "coming_soon":
        raise HTTPException(status_code=400, detail=f"{provider_info['display_name']} is coming soon.")

    # Validate provider enum
    try:
        provider_enum = CloudProvider(payload.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {payload.provider}")

    # Validate credentials
    try:
        connector = get_connector(payload.provider, payload.credentials)
        validation = connector.validate()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Credential validation failed: {e}")

    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid credentials: {validation.error}",
        )

    # Store connection
    account = CloudAccount(
        provider=provider_enum,
        account_identifier=validation.account_identifier or payload.provider,
        display_name=payload.display_name or provider_info["display_name"],
        connection_config=payload.credentials,
        status=AccountSyncStatus.ACTIVE,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)

    # Fire webhook
    await dispatch_event("integration.connected", {
        "integration_id": str(account.id),
        "provider": payload.provider,
        "display_name": account.display_name,
    })

    return _to_response(account)


@router.post("/{integration_id}/validate", response_model=ValidateResponse)
async def validate_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Re-test credentials for an existing integration."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == integration_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Integration not found")

    connector = get_connector(account.provider.value, account.connection_config or {})
    validation = connector.validate()

    return ValidateResponse(
        valid=validation.valid,
        error=validation.error,
        account_identifier=validation.account_identifier,
    )


@router.post("/{integration_id}/sync", response_model=SyncResponse)
async def sync_integration(
    integration_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a cost data sync for an integration."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == integration_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Default: last 30 days
    end_dt = date.fromisoformat(end_date) if end_date else date.today()
    start_dt = date.fromisoformat(start_date) if start_date else end_dt - timedelta(days=30)

    account.status = AccountSyncStatus.SYNCING
    await db.flush()

    try:
        connector = get_connector(account.provider.value, account.connection_config or {})
        ingest_result = connector.ingest(start_dt, end_dt)

        if ingest_result.status == "success":
            account.status = AccountSyncStatus.ACTIVE
            account.last_sync_at = datetime.utcnow()
            account.last_sync_rows = str(ingest_result.rows_ingested)
            account.sync_error = None
        else:
            account.status = AccountSyncStatus.ERROR
            account.sync_error = ingest_result.message

        await db.flush()

        # Refresh DuckDB views
        try:
            from app.services.duckdb_engine import get_duckdb_engine
            engine = get_duckdb_engine()
            engine.refresh_views()
        except Exception:
            pass

        # Fire webhook
        event = "sync.completed" if ingest_result.status == "success" else "sync.failed"
        await dispatch_event(event, {
            "integration_id": integration_id,
            "provider": account.provider.value,
            "rows_ingested": ingest_result.rows_ingested,
            "message": ingest_result.message,
        })

        return SyncResponse(
            status=ingest_result.status,
            rows_ingested=ingest_result.rows_ingested,
            message=ingest_result.message,
        )

    except Exception as e:
        logger.error(f"Sync failed for {integration_id}: {e}")
        account.status = AccountSyncStatus.ERROR
        account.sync_error = str(e)
        await db.flush()
        return SyncResponse(status="error", message=str(e))


@router.delete("/{integration_id}")
async def disconnect_integration(
    integration_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect an integration."""
    result = await db.execute(
        select(CloudAccount).where(CloudAccount.id == integration_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Integration not found")

    account.status = AccountSyncStatus.DISCONNECTED
    await db.flush()

    await dispatch_event("integration.disconnected", {
        "integration_id": integration_id,
        "provider": account.provider.value,
    })

    return {"message": f"Disconnected {account.provider.value} integration."}
