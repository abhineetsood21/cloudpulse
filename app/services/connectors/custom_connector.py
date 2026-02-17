"""
Custom Provider Connector — FOCUS-compliant CSV/Parquet import.

Also contains stub connectors for "coming soon" providers (Cloudflare, Vercel).
"""

import logging
from datetime import date
from pathlib import Path
from typing import Any

from app.services.connectors.base import (
    BaseConnector, FocusRecord, IngestResult, ValidationResult,
)

logger = logging.getLogger(__name__)


class CustomConnector(BaseConnector):
    """Import FOCUS-compliant CSV or Parquet files from a local path."""
    provider_key = "custom"

    def validate(self) -> ValidationResult:
        import_path = Path(self.config.get("import_path", ""))
        if import_path.exists() and import_path.is_dir():
            files = list(import_path.glob("*.csv")) + list(import_path.glob("*.parquet"))
            if files:
                return ValidationResult(valid=True, account_identifier=self.config.get("provider_name", "custom"))
            return ValidationResult(valid=False, error=f"No CSV or Parquet files found in {import_path}")
        return ValidationResult(valid=False, error=f"Path does not exist: {import_path}")

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        return []  # Handled in ingest()

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        """Read CSV/Parquet files and copy them to the billing data directory."""
        import shutil
        from app.core.config import get_settings

        settings = get_settings()
        import_path = Path(self.config.get("import_path", ""))
        dest_dir = Path(output_dir or settings.billing_data_dir) / "custom"
        dest_dir.mkdir(parents=True, exist_ok=True)

        files_copied = 0

        # Copy Parquet files directly
        for f in import_path.glob("*.parquet"):
            shutil.copy2(f, dest_dir / f.name)
            files_copied += 1

        # Convert CSVs to Parquet
        for f in import_path.glob("*.csv"):
            try:
                import pyarrow.csv as pcsv
                import pyarrow.parquet as pq
                table = pcsv.read_csv(str(f))
                pq.write_table(table, str(dest_dir / f"{f.stem}.parquet"))
                files_copied += 1
            except Exception as e:
                logger.warning(f"Failed to convert {f}: {e}")

        return IngestResult(
            status="success",
            rows_ingested=files_copied,
            message=f"Imported {files_copied} files from {import_path}.",
        )


class StubConnector(BaseConnector):
    """Placeholder for coming_soon providers."""

    def validate(self) -> ValidationResult:
        return ValidationResult(valid=False, error=f"{self.provider_key} integration is coming soon.")

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        return []

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        return IngestResult(status="error", message=f"{self.provider_key} is coming soon.")


class CloudflareConnector(StubConnector):
    provider_key = "cloudflare"


class VercelConnector(StubConnector):
    provider_key = "vercel"
