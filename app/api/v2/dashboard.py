"""
v2 Dashboard API — Multi-Provider Summary

Provides aggregated dashboard statistics across all connected
integrations, not just AWS accounts.
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.providers import CloudAccount, AccountSyncStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class ProviderSummary(BaseModel):
    provider: str
    display_name: str
    count: int
    status: str


class DashboardSummaryResponse(BaseModel):
    total_integrations: int
    active_integrations: int
    syncing_integrations: int
    error_integrations: int
    providers: list[ProviderSummary]
    total_synced_rows: int
    last_sync_at: str | None
    has_data: bool


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """
    Multi-provider dashboard summary.

    Returns aggregate stats across all connected integrations.
    """
    from app.services.provider_registry import get_provider

    result = await db.execute(
        select(CloudAccount).where(
            CloudAccount.status != AccountSyncStatus.DISCONNECTED
        )
    )
    accounts = result.scalars().all()

    active = [a for a in accounts if a.status == AccountSyncStatus.ACTIVE]
    syncing = [a for a in accounts if a.status == AccountSyncStatus.SYNCING]
    errors = [a for a in accounts if a.status == AccountSyncStatus.ERROR]

    # Group by provider
    provider_map: dict[str, list] = {}
    for a in accounts:
        key = a.provider.value
        provider_map.setdefault(key, []).append(a)

    providers = []
    for key, accts in provider_map.items():
        info = get_provider(key) or {}
        providers.append(ProviderSummary(
            provider=key,
            display_name=info.get("display_name", key),
            count=len(accts),
            status="active" if any(a.status == AccountSyncStatus.ACTIVE for a in accts) else "error",
        ))

    total_rows = sum(int(a.last_sync_rows or 0) for a in accounts if a.last_sync_rows)

    sync_times = [a.last_sync_at for a in accounts if a.last_sync_at]
    last_sync = max(sync_times).isoformat() if sync_times else None

    # Check DuckDB for data
    has_data = False
    try:
        from app.services.duckdb_engine import get_duckdb_engine
        engine = get_duckdb_engine()
        stats = engine.get_table_stats()
        has_data = len(stats) > 0
    except Exception:
        pass

    return DashboardSummaryResponse(
        total_integrations=len(accounts),
        active_integrations=len(active),
        syncing_integrations=len(syncing),
        error_integrations=len(errors),
        providers=providers,
        total_synced_rows=total_rows,
        last_sync_at=last_sync,
        has_data=has_data,
    )
