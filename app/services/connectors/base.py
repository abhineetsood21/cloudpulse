"""
Base Connector — Abstract interface for all CloudPulse integrations.

Every provider connector inherits from BaseConnector and implements:
  • validate()   — verify credentials are valid
  • fetch_costs() — pull raw billing / usage data from the provider
  • normalize()  — transform raw records into FOCUS-compatible dicts
  • ingest()     — orchestrate the full pipeline: fetch → normalize → write Parquet
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a credential validation check."""
    valid: bool
    error: str | None = None
    account_identifier: str | None = None  # auto-detected account/org ID


@dataclass
class IngestResult:
    """Result of a full ingestion run."""
    status: str = "success"  # success | error
    rows_ingested: int = 0
    message: str = ""
    parquet_path: str | None = None


@dataclass
class FocusRecord:
    """
    A single cost record in the FOCUS schema.

    See https://focus.finops.org/ for the full specification.
    """
    provider: str
    service: str
    usage_date: str           # YYYY-MM-DD
    amount: float
    currency: str = "USD"
    region: str | None = None
    account_id: str | None = None
    resource_id: str | None = None
    usage_type: str | None = None
    usage_quantity: float | None = None
    tags: dict[str, str] = field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract base class for all provider connectors."""

    # Subclasses set this to their provider key (e.g. "datadog")
    provider_key: str = ""

    def __init__(self, config: dict[str, Any]):
        """
        Args:
            config: Provider-specific credentials / connection details,
                    matching the required_fields from the provider registry.
        """
        self.config = config

    # ── Required interface ─────────────────────────────────────────

    @abstractmethod
    def validate(self) -> ValidationResult:
        """
        Test that the stored credentials are valid.

        Should make a lightweight API call (e.g. "get account info")
        and return success/failure.
        """
        ...

    @abstractmethod
    def fetch_costs(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """
        Pull raw billing / usage records from the provider API.

        Returns a list of provider-native dicts.
        """
        ...

    @abstractmethod
    def normalize(self, raw_records: list[dict[str, Any]]) -> list[FocusRecord]:
        """
        Transform provider-native records into FOCUS-schema records.
        """
        ...

    # ── Default orchestrator ───────────────────────────────────────

    def ingest(
        self,
        start_date: date,
        end_date: date,
        output_dir: str | None = None,
    ) -> IngestResult:
        """
        Full ingestion pipeline: fetch → normalize → write Parquet.

        Can be overridden by connectors that need custom pipelines
        (e.g. AWS CUR downloads pre-built Parquet files).
        """
        try:
            raw = self.fetch_costs(start_date, end_date)
            records = self.normalize(raw)

            if not records:
                return IngestResult(
                    status="success",
                    rows_ingested=0,
                    message="No records found for the given date range.",
                )

            # Write to Parquet
            parquet_path = self._write_parquet(records, output_dir)

            return IngestResult(
                status="success",
                rows_ingested=len(records),
                message=f"Ingested {len(records)} records from {self.provider_key}.",
                parquet_path=parquet_path,
            )

        except Exception as e:
            logger.error(f"[{self.provider_key}] Ingestion failed: {e}")
            return IngestResult(
                status="error",
                rows_ingested=0,
                message=str(e),
            )

    # ── Parquet writer ─────────────────────────────────────────────

    def _write_parquet(
        self,
        records: list[FocusRecord],
        output_dir: str | None = None,
    ) -> str:
        """Write FOCUS records to a Parquet file."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        from app.core.config import get_settings

        settings = get_settings()
        base_dir = Path(output_dir or settings.billing_data_dir) / self.provider_key
        base_dir.mkdir(parents=True, exist_ok=True)

        # Build table
        data = {
            "provider": [r.provider for r in records],
            "service": [r.service for r in records],
            "usage_date": [r.usage_date for r in records],
            "amount": [r.amount for r in records],
            "currency": [r.currency for r in records],
            "region": [r.region for r in records],
            "account_id": [r.account_id for r in records],
            "resource_id": [r.resource_id for r in records],
            "usage_type": [r.usage_type for r in records],
            "usage_quantity": [r.usage_quantity for r in records],
            "tags": [str(r.tags) for r in records],
        }

        table = pa.table(data)
        outfile = base_dir / f"{self.provider_key}_costs.parquet"
        pq.write_table(table, str(outfile))

        logger.info(f"[{self.provider_key}] Wrote {len(records)} records → {outfile}")
        return str(outfile)
