"""
Azure Cost Management Connector

Downloads Azure Cost Management exports from Blob Storage,
normalizes to FOCUS schema, and writes Parquet for DuckDB.

Prerequisites:
    - Azure Cost Management export configured to Blob Storage
    - Service principal with Storage Blob Data Reader role
    - Credentials configured (client_id, client_secret, tenant_id)

Usage:
    connector = AzureCostConnector()
    connector.ingest(start_date="2026-01-01", end_date="2026-02-01")
"""

import csv
import io
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.services.focus_schema import normalize_azure_export, write_focus_parquet

logger = logging.getLogger(__name__)
settings = get_settings()


class AzureCostConnector:
    """Ingests Azure cost data from Cost Management exports in Blob Storage."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        storage_account: Optional[str] = None,
        container: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.client_id = client_id or settings.azure_client_id
        self.client_secret = client_secret or settings.azure_client_secret
        self.tenant_id = tenant_id or settings.azure_tenant_id
        self.storage_account = storage_account or settings.azure_storage_account
        self.container = container or settings.azure_cost_export_container
        self.output_dir = Path(output_dir or settings.billing_data_dir) / "azure"
        self._blob_client = None

    def _get_blob_service_client(self):
        """Get an authenticated Azure Blob Storage client."""
        if self._blob_client:
            return self._blob_client

        from azure.identity import ClientSecretCredential
        from azure.storage.blob import BlobServiceClient

        if self.client_id and self.client_secret and self.tenant_id:
            credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
        else:
            # Fall back to DefaultAzureCredential
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()

        account_url = f"https://{self.storage_account}.blob.core.windows.net"
        self._blob_client = BlobServiceClient(account_url, credential=credential)
        return self._blob_client

    def validate_access(self) -> bool:
        """Test that we can list blobs in the cost export container."""
        try:
            client = self._get_blob_service_client()
            container_client = client.get_container_client(self.container)
            # List first blob to verify access
            blobs = container_client.list_blobs(results_per_page=1)
            next(blobs, None)
            return True
        except Exception as e:
            logger.error(f"Azure storage access validation failed: {e}")
            return False

    def list_export_files(self, prefix: str = "") -> list[str]:
        """List CSV export files in the container."""
        client = self._get_blob_service_client()
        container_client = client.get_container_client(self.container)

        files = []
        try:
            for blob in container_client.list_blobs(name_starts_with=prefix):
                if blob.name.endswith(".csv"):
                    files.append(blob.name)
        except Exception as e:
            logger.error(f"Failed to list Azure export files: {e}")

        files.sort()
        return files

    def _download_csv(self, blob_name: str) -> list[dict]:
        """Download and parse a CSV export from Blob Storage."""
        client = self._get_blob_service_client()
        container_client = client.get_container_client(self.container)

        try:
            blob_client = container_client.get_blob_client(blob_name)
            data = blob_client.download_blob().readall()
            text = data.decode("utf-8-sig")  # Azure CSVs often have BOM

            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            logger.info(f"Downloaded {len(rows)} rows from {blob_name}")
            return rows
        except Exception as e:
            logger.error(f"Failed to download {blob_name}: {e}")
            return []

    def ingest(
        self,
        start_date: str,
        end_date: str,
        export_prefix: str = "",
    ) -> dict:
        """
        Ingest Azure cost data for a date range.

        Finds CSV exports in Blob Storage, downloads them,
        normalizes to FOCUS schema, and writes Parquet.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            export_prefix: Optional blob prefix to filter export files

        Returns:
            {"rows_ingested": N, "files_processed": N, "output_path": "..."}
        """
        files = self.list_export_files(prefix=export_prefix)
        if not files:
            logger.warning("No Azure cost export files found")
            return {"rows_ingested": 0, "files_processed": 0, "output_path": None}

        all_rows = []
        for f in files:
            rows = self._download_csv(f)
            # Filter rows by date range
            for row in rows:
                row_date = row.get("Date", row.get("UsageDateTime", ""))[:10]
                if row_date and start_date <= row_date < end_date:
                    all_rows.append(row)

        if not all_rows:
            return {"rows_ingested": 0, "files_processed": len(files), "output_path": None}

        # Normalize to FOCUS schema
        normalized = normalize_azure_export(all_rows)

        if not normalized:
            return {"rows_ingested": 0, "files_processed": len(files), "output_path": None}

        # Write Parquet
        self.output_dir.mkdir(parents=True, exist_ok=True)
        period = f"{start_date.replace('-', '')}_{end_date.replace('-', '')}"
        output_path = str(self.output_dir / f"azure_{period}.parquet")
        write_focus_parquet(normalized, output_path)

        return {
            "rows_ingested": len(normalized),
            "files_processed": len(files),
            "output_path": output_path,
        }

    def ingest_from_csv(self, csv_path: str) -> int:
        """
        Ingest Azure cost data from a local CSV export (for development).

        Args:
            csv_path: Path to an Azure Cost Management CSV export.

        Returns:
            Number of rows ingested.
        """
        path = Path(csv_path)
        if not path.exists():
            logger.error(f"File not found: {csv_path}")
            return 0

        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        logger.info(f"Read {len(rows)} rows from {csv_path}")

        normalized = normalize_azure_export(rows)
        if not normalized:
            return 0

        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = path.stem
        output_path = str(self.output_dir / f"azure_{stem}.parquet")
        write_focus_parquet(normalized, output_path)

        return len(normalized)
