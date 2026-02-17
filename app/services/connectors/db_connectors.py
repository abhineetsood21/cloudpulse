"""
Database Connectors — Snowflake, Databricks

Query billing/usage system tables via SQL or REST APIs.
"""

import logging
from datetime import date
from typing import Any

import httpx

from app.services.connectors.base import (
    BaseConnector, FocusRecord, ValidationResult,
)

logger = logging.getLogger(__name__)


class SnowflakeConnector(BaseConnector):
    provider_key = "snowflake"

    def _get_connection(self):
        import snowflake.connector
        return snowflake.connector.connect(
            account=self.config["account"],
            user=self.config["username"],
            password=self.config["password"],
            warehouse=self.config.get("warehouse", "COMPUTE_WH"),
        )

    def validate(self) -> ValidationResult:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT CURRENT_ACCOUNT()")
            acct = cur.fetchone()[0]
            cur.close()
            conn.close()
            return ValidationResult(valid=True, account_identifier=acct)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                USAGE_DATE::VARCHAR AS usage_date,
                SERVICE_TYPE AS service,
                SUM(CREDITS_USED) AS credits,
                SUM(CREDITS_USED * 3.00) AS cost_usd
            FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY
            WHERE USAGE_DATE BETWEEN %s AND %s
            GROUP BY 1, 2
            ORDER BY 1
        """, (start_date.isoformat(), end_date.isoformat()))
        cols = [d[0].lower() for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return rows

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="snowflake",
                service=r.get("service", "Snowflake"),
                usage_date=str(r.get("usage_date", "")),
                amount=float(r.get("cost_usd", 0)),
                currency="USD",
                usage_quantity=float(r.get("credits", 0)),
                usage_type="credits",
            )
            for r in raw
        ]


class DatabricksConnector(BaseConnector):
    provider_key = "databricks"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['access_token']}"}

    def validate(self) -> ValidationResult:
        try:
            url = self.config["workspace_url"].rstrip("/")
            resp = httpx.get(f"{url}/api/2.0/clusters/list", headers=self._headers(), timeout=15)
            resp.raise_for_status()
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        url = self.config["workspace_url"].rstrip("/")
        resp = httpx.post(
            f"{url}/api/2.0/sql/statements",
            headers=self._headers(),
            json={
                "statement": f"""
                    SELECT usage_date, sku_name, SUM(usage_quantity) as quantity,
                           SUM(usage_quantity * list_price) as cost
                    FROM system.billing.usage
                    WHERE usage_date BETWEEN '{start_date}' AND '{end_date}'
                    GROUP BY 1, 2
                    ORDER BY 1
                """,
                "warehouse_id": "auto",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        # Parse statement result
        columns = [c["name"] for c in data.get("manifest", {}).get("schema", {}).get("columns", [])]
        rows = []
        for chunk in data.get("result", {}).get("data_array", []):
            rows.append(dict(zip(columns, chunk)))
        return rows

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="databricks",
                service=r.get("sku_name", "Databricks"),
                usage_date=str(r.get("usage_date", "")),
                amount=float(r.get("cost", 0)),
                currency="USD",
                usage_quantity=float(r.get("quantity", 0)),
            )
            for r in raw
        ]
