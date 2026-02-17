"""
GCP Billing Connector

Queries GCP BigQuery billing export, normalizes to FOCUS schema,
and writes Parquet files for DuckDB analytics.

Prerequisites:
    - GCP billing export enabled to BigQuery
    - Service account with BigQuery Data Viewer role
    - Service account JSON key configured

Usage:
    connector = GCPBillingConnector()
    connector.ingest(start_date="2026-01-01", end_date="2026-02-01")
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.services.focus_schema import normalize_gcp_export, write_focus_parquet

logger = logging.getLogger(__name__)
settings = get_settings()


class GCPBillingConnector:
    """Ingests GCP billing data from BigQuery billing export."""

    def __init__(
        self,
        service_account_json: Optional[str] = None,
        billing_dataset: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.service_account_json = service_account_json or settings.gcp_service_account_json
        self.billing_dataset = billing_dataset or settings.gcp_billing_dataset
        self.output_dir = Path(output_dir or settings.billing_data_dir) / "gcp"
        self._client = None

    def _get_client(self):
        """Get an authenticated BigQuery client."""
        if self._client:
            return self._client

        from google.cloud import bigquery
        from google.oauth2 import service_account

        if self.service_account_json:
            # Load from JSON string or file path
            if self.service_account_json.startswith("{"):
                info = json.loads(self.service_account_json)
                credentials = service_account.Credentials.from_service_account_info(info)
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_json
                )
            self._client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        else:
            # Use Application Default Credentials
            self._client = bigquery.Client()

        return self._client

    def validate_access(self) -> bool:
        """Test that we can query the billing dataset."""
        try:
            client = self._get_client()
            query = f"SELECT 1 FROM `{self.billing_dataset}` LIMIT 1"
            result = client.query(query).result()
            return True
        except Exception as e:
            logger.error(f"GCP billing access validation failed: {e}")
            return False

    def ingest(
        self,
        start_date: str,
        end_date: str,
    ) -> dict:
        """
        Ingest GCP billing data for a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            {"rows_ingested": N, "output_path": "..."}
        """
        client = self._get_client()

        query = f"""
            SELECT
                project.id AS project_id,
                service.description AS service_description,
                location.region AS location_region,
                resource.name AS resource_name,
                usage_start_time,
                cost_type,
                cost,
                currency,
                labels
            FROM `{self.billing_dataset}`
            WHERE DATE(usage_start_time) >= @start_date
              AND DATE(usage_start_time) < @end_date
              AND cost != 0
            ORDER BY usage_start_time
        """

        from google.cloud import bigquery as bq

        job_config = bq.QueryJobConfig(
            query_parameters=[
                bq.ScalarQueryParameter("start_date", "DATE", start_date),
                bq.ScalarQueryParameter("end_date", "DATE", end_date),
            ]
        )

        try:
            logger.info(f"Querying GCP billing: {start_date} to {end_date}")
            result = client.query(query, job_config=job_config).result()

            rows = []
            for row in result:
                rows.append(dict(row))

            logger.info(f"Fetched {len(rows)} GCP billing rows")
        except Exception as e:
            logger.error(f"GCP billing query failed: {e}")
            raise

        if not rows:
            return {"rows_ingested": 0, "output_path": None}

        # Normalize to FOCUS schema
        normalized = normalize_gcp_export(rows)

        if not normalized:
            return {"rows_ingested": 0, "output_path": None}

        # Write Parquet
        self.output_dir.mkdir(parents=True, exist_ok=True)
        period = f"{start_date.replace('-', '')}_{end_date.replace('-', '')}"
        output_path = str(self.output_dir / f"gcp_{period}.parquet")
        write_focus_parquet(normalized, output_path)

        return {
            "rows_ingested": len(normalized),
            "output_path": output_path,
        }

    def ingest_from_csv(self, csv_path: str) -> int:
        """
        Ingest GCP billing data from a local CSV export (for development).

        Args:
            csv_path: Path to a GCP billing export CSV.

        Returns:
            Number of rows ingested.
        """
        import csv

        path = Path(csv_path)
        if not path.exists():
            logger.error(f"File not found: {csv_path}")
            return 0

        with open(path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        logger.info(f"Read {len(rows)} rows from {csv_path}")

        normalized = normalize_gcp_export(rows)
        if not normalized:
            return 0

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = path.stem
        output_path = str(self.output_dir / f"gcp_{stem}.parquet")
        write_focus_parquet(normalized, output_path)

        return len(normalized)
