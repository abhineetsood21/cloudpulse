"""
DuckDB Analytics Engine

Embedded analytical query engine for CloudPulse billing data.
Queries FOCUS-normalized Parquet files using DuckDB — eliminates
the need for expensive managed OLAP databases.

Usage:
    engine = DuckDBEngine()
    engine.load_billing_data()
    results = engine.get_cost_by_service("2026-01-01", "2026-02-01")
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional

import duckdb

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DuckDBEngine:
    """Embedded DuckDB engine for analytical queries over billing data."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.duckdb_path
        self.billing_dir = Path(settings.billing_data_dir)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Lazy connection — created on first access."""
        if self._conn is None:
            self._conn = duckdb.connect(self.db_path)
            self._conn.execute("SET threads = 4")
            self._conn.execute("SET memory_limit = '512MB'")
            self._setup_views()
        return self._conn

    def close(self):
        """Close the DuckDB connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _setup_views(self):
        """Create views over billing Parquet files for each provider."""
        for provider in ("aws", "gcp", "azure"):
            parquet_dir = self.billing_dir / provider
            if parquet_dir.exists() and any(parquet_dir.glob("*.parquet")):
                self._conn.execute(f"""
                    CREATE OR REPLACE VIEW {provider}_costs AS
                    SELECT * FROM read_parquet('{parquet_dir}/*.parquet')
                """)
                logger.info(f"Created DuckDB view: {provider}_costs")

        # Unified view across all providers
        provider_views = []
        for provider in ("aws", "gcp", "azure"):
            parquet_dir = self.billing_dir / provider
            if parquet_dir.exists() and any(parquet_dir.glob("*.parquet")):
                provider_views.append(f"SELECT * FROM {provider}_costs")

        if provider_views:
            union_sql = " UNION ALL ".join(provider_views)
            self._conn.execute(f"""
                CREATE OR REPLACE VIEW all_costs AS {union_sql}
            """)
            logger.info("Created unified DuckDB view: all_costs")

    def refresh_views(self):
        """Refresh views after new data is ingested."""
        if self._conn:
            self._setup_views()

    def load_parquet(self, path: str, table_name: str):
        """Load a Parquet file into a named DuckDB table."""
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT * FROM read_parquet('{path}')
        """)
        count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        logger.info(f"Loaded {count} rows into {table_name} from {path}")

    def query(self, sql: str, params: Optional[list] = None) -> list[dict]:
        """Execute a SQL query and return results as list of dicts."""
        try:
            if params:
                result = self.conn.execute(sql, params)
            else:
                result = self.conn.execute(sql)

            columns = [desc[0] for desc in result.description]
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except duckdb.Error as e:
            logger.error(f"DuckDB query error: {e}\nSQL: {sql}")
            raise

    def get_cost_by_service(
        self,
        start_date: str,
        end_date: str,
        provider: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> list[dict]:
        """Get cost grouped by service within a date range."""
        view = f"{provider}_costs" if provider else "all_costs"
        where_clauses = ["usage_date >= ? AND usage_date < ?"]
        params: list[Any] = [start_date, end_date]

        if account_id:
            where_clauses.append("account_id = ?")
            params.append(account_id)

        where_sql = " AND ".join(where_clauses)

        sql = f"""
            SELECT
                service,
                provider,
                SUM(amount) AS total_amount,
                currency
            FROM {view}
            WHERE {where_sql}
            GROUP BY service, provider, currency
            ORDER BY total_amount DESC
        """
        return self.query(sql, params)

    def get_cost_by_tag(
        self,
        start_date: str,
        end_date: str,
        tag_key: str,
        provider: Optional[str] = None,
    ) -> list[dict]:
        """Get cost grouped by a specific tag key."""
        view = f"{provider}_costs" if provider else "all_costs"

        sql = f"""
            SELECT
                COALESCE(tags ->> ?, '(untagged)') AS tag_value,
                SUM(amount) AS total_amount,
                currency
            FROM {view}
            WHERE usage_date >= ? AND usage_date < ?
            GROUP BY tag_value, currency
            ORDER BY total_amount DESC
        """
        return self.query(sql, [tag_key, start_date, end_date])

    def get_total_cost(
        self,
        start_date: str,
        end_date: str,
        granularity: str = "day",
        provider: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> list[dict]:
        """Get total cost over time with specified granularity."""
        view = f"{provider}_costs" if provider else "all_costs"
        where_clauses = ["usage_date >= ? AND usage_date < ?"]
        params: list[Any] = [start_date, end_date]

        if account_id:
            where_clauses.append("account_id = ?")
            params.append(account_id)

        where_sql = " AND ".join(where_clauses)

        if granularity == "month":
            date_expr = "DATE_TRUNC('month', usage_date)"
        elif granularity == "week":
            date_expr = "DATE_TRUNC('week', usage_date)"
        else:
            date_expr = "usage_date"

        sql = f"""
            SELECT
                {date_expr} AS period,
                SUM(amount) AS total_amount,
                currency
            FROM {view}
            WHERE {where_sql}
            GROUP BY period, currency
            ORDER BY period
        """
        return self.query(sql, params)

    def get_cost_by_region(
        self,
        start_date: str,
        end_date: str,
        provider: Optional[str] = None,
    ) -> list[dict]:
        """Get cost grouped by region."""
        view = f"{provider}_costs" if provider else "all_costs"

        sql = f"""
            SELECT
                region,
                provider,
                SUM(amount) AS total_amount,
                currency
            FROM {view}
            WHERE usage_date >= ? AND usage_date < ?
            GROUP BY region, provider, currency
            ORDER BY total_amount DESC
        """
        return self.query(sql, [start_date, end_date])

    def get_cost_by_account(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get cost grouped by cloud account across all providers."""
        sql = """
            SELECT
                account_id,
                provider,
                SUM(amount) AS total_amount,
                currency
            FROM all_costs
            WHERE usage_date >= ? AND usage_date < ?
            GROUP BY account_id, provider, currency
            ORDER BY total_amount DESC
        """
        return self.query(sql, [start_date, end_date])

    def get_cost_breakdown(
        self,
        start_date: str,
        end_date: str,
        group_by: str = "service",
        provider: Optional[str] = None,
        account_id: Optional[str] = None,
        granularity: str = "day",
    ) -> list[dict]:
        """
        Flexible cost breakdown — used by the /api/v2/query endpoint.

        Args:
            group_by: One of 'service', 'region', 'account_id', 'provider', 'charge_type'
            granularity: One of 'day', 'week', 'month'
        """
        view = f"{provider}_costs" if provider else "all_costs"
        valid_groups = {"service", "region", "account_id", "provider", "charge_type", "resource_id"}

        if group_by not in valid_groups:
            group_by = "service"

        where_clauses = ["usage_date >= ? AND usage_date < ?"]
        params: list[Any] = [start_date, end_date]

        if account_id:
            where_clauses.append("account_id = ?")
            params.append(account_id)

        where_sql = " AND ".join(where_clauses)

        if granularity == "month":
            date_expr = "DATE_TRUNC('month', usage_date)"
        elif granularity == "week":
            date_expr = "DATE_TRUNC('week', usage_date)"
        else:
            date_expr = "usage_date"

        sql = f"""
            SELECT
                {date_expr} AS period,
                {group_by},
                SUM(amount) AS total_amount,
                currency
            FROM {view}
            WHERE {where_sql}
            GROUP BY period, {group_by}, currency
            ORDER BY period, total_amount DESC
        """
        return self.query(sql, params)

    def get_table_stats(self) -> dict:
        """Get stats about loaded billing data."""
        stats = {}
        for provider in ("aws", "gcp", "azure"):
            parquet_dir = self.billing_dir / provider
            if parquet_dir.exists() and any(parquet_dir.glob("*.parquet")):
                try:
                    row = self.conn.execute(f"""
                        SELECT
                            COUNT(*) AS row_count,
                            MIN(usage_date) AS earliest_date,
                            MAX(usage_date) AS latest_date,
                            COUNT(DISTINCT service) AS service_count,
                            SUM(amount) AS total_amount
                        FROM {provider}_costs
                    """).fetchone()
                    stats[provider] = {
                        "row_count": row[0],
                        "earliest_date": str(row[1]) if row[1] else None,
                        "latest_date": str(row[2]) if row[2] else None,
                        "service_count": row[3],
                        "total_amount": round(float(row[4] or 0), 2),
                    }
                except duckdb.Error:
                    stats[provider] = {"error": "View not available"}
        return stats


# Module-level singleton for reuse across requests
_engine: Optional[DuckDBEngine] = None


def get_duckdb_engine() -> DuckDBEngine:
    """Get or create the singleton DuckDB engine instance."""
    global _engine
    if _engine is None:
        _engine = DuckDBEngine()
    return _engine
