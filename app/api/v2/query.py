"""
v2 Query API — Flexible cost data queries via DuckDB.

Accepts CQL filters, date ranges, groupings, and granularity.
Queries FOCUS-normalized Parquet data through the DuckDB engine.

Endpoints:
    POST /api/v2/query           - Run a cost query
    GET  /api/v2/query/stats     - Get billing data statistics
    POST /api/v2/query/validate  - Validate a CQL expression
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.duckdb_engine import get_duckdb_engine
from app.services.cql_parser import cql_to_duckdb_sql, validate_cql

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])


# --- Request/Response Models ---

class CostQueryRequest(BaseModel):
    """Request body for a cost query."""
    filter: Optional[str] = Field(None, description="CQL filter expression")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    group_by: str = Field("service", description="Group by: service, region, account_id, provider, charge_type")
    granularity: str = Field("day", description="Time granularity: day, week, month")
    provider: Optional[str] = Field(None, description="Filter by provider: aws, gcp, azure")
    account_id: Optional[str] = Field(None, description="Filter by account ID")
    limit: int = Field(1000, ge=1, le=10000)


class CostQueryResult(BaseModel):
    """Single row in a cost query result."""
    period: Optional[str] = None
    group_value: Optional[str] = None
    total_amount: float
    currency: str = "USD"


class CostQueryResponse(BaseModel):
    """Response for a cost query."""
    results: list[dict]
    total_amount: float
    row_count: int
    query_filter: Optional[str] = None


class ValidateCQLRequest(BaseModel):
    """Request to validate a CQL expression."""
    filter: str


class ValidateCQLResponse(BaseModel):
    """Response for CQL validation."""
    is_valid: bool
    errors: list[str]


class BillingStatsResponse(BaseModel):
    """Response for billing data statistics."""
    providers: dict
    has_data: bool


# --- Endpoints ---

@router.post("", response_model=CostQueryResponse)
async def run_cost_query(req: CostQueryRequest):
    """
    Run a flexible cost query against billing data.

    Supports CQL filters, date ranges, groupings, and time granularity.
    Data is queried from FOCUS-normalized Parquet files via DuckDB.

    Example request:
        {
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "group_by": "service",
            "granularity": "month",
            "filter": "costs.provider = 'aws' AND costs.region = 'us-east-1'"
        }
    """
    engine = get_duckdb_engine()

    # Build base query
    view = f"{req.provider}_costs" if req.provider else "all_costs"
    valid_groups = {"service", "region", "account_id", "provider", "charge_type", "resource_id"}
    group_by = req.group_by if req.group_by in valid_groups else "service"

    # Date granularity
    if req.granularity == "month":
        date_expr = "CAST(DATE_TRUNC('month', usage_date) AS VARCHAR)"
    elif req.granularity == "week":
        date_expr = "CAST(DATE_TRUNC('week', usage_date) AS VARCHAR)"
    else:
        date_expr = "CAST(usage_date AS VARCHAR)"

    # Build WHERE clause
    where_parts = ["usage_date >= ? AND usage_date < ?"]
    params = [req.start_date, req.end_date]

    if req.account_id:
        where_parts.append("account_id = ?")
        params.append(req.account_id)

    # Apply CQL filter
    if req.filter:
        is_valid, errors = validate_cql(req.filter)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CQL filter: {'; '.join(errors)}",
            )
        cql_sql, cql_params = cql_to_duckdb_sql(req.filter)
        if cql_sql != "1=1":
            where_parts.append(cql_sql)
            params.extend(cql_params)

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT
            {date_expr} AS period,
            {group_by} AS group_value,
            SUM(amount) AS total_amount,
            currency
        FROM {view}
        WHERE {where_sql}
        GROUP BY period, group_value, currency
        ORDER BY period, total_amount DESC
        LIMIT {req.limit}
    """

    try:
        results = engine.query(sql, params)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

    total = sum(r.get("total_amount", 0) for r in results)

    return CostQueryResponse(
        results=results,
        total_amount=round(total, 2),
        row_count=len(results),
        query_filter=req.filter,
    )


@router.get("/stats", response_model=BillingStatsResponse)
async def get_billing_stats():
    """Get statistics about loaded billing data."""
    engine = get_duckdb_engine()
    stats = engine.get_table_stats()

    return BillingStatsResponse(
        providers=stats,
        has_data=len(stats) > 0,
    )


@router.post("/validate", response_model=ValidateCQLResponse)
async def validate_cql_expression(req: ValidateCQLRequest):
    """Validate a CQL filter expression without executing it."""
    is_valid, errors = validate_cql(req.filter)
    return ValidateCQLResponse(is_valid=is_valid, errors=errors)
