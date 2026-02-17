"""
Oracle Cloud Infrastructure (OCI) Connector
"""

import logging
from datetime import date
from typing import Any

import httpx

from app.services.connectors.base import (
    BaseConnector, FocusRecord, ValidationResult,
)

logger = logging.getLogger(__name__)


class OracleConnector(BaseConnector):
    provider_key = "oracle"

    def _get_signer(self):
        """Build OCI request signer from config."""
        try:
            from oci.signer import Signer
            return Signer(
                tenancy=self.config["tenancy_ocid"],
                user=self.config["user_ocid"],
                fingerprint=self.config["fingerprint"],
                private_key_content=self.config["private_key"],
            )
        except ImportError:
            raise RuntimeError("oci package not installed. pip install oci")

    def validate(self) -> ValidationResult:
        try:
            signer = self._get_signer()
            region = self.config.get("region", "us-ashburn-1")
            resp = httpx.get(
                f"https://identity.{region}.oraclecloud.com/20160918/tenancies/{self.config['tenancy_ocid']}",
                auth=signer,
                timeout=15,
            )
            resp.raise_for_status()
            return ValidationResult(valid=True, account_identifier=self.config["tenancy_ocid"])
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        signer = self._get_signer()
        region = self.config.get("region", "us-ashburn-1")
        resp = httpx.post(
            f"https://usageapi.{region}.oci.oraclecloud.com/20200107/usage",
            auth=signer,
            json={
                "tenantId": self.config["tenancy_ocid"],
                "timeUsageStarted": f"{start_date}T00:00:00Z",
                "timeUsageEnded": f"{end_date}T00:00:00Z",
                "granularity": "DAILY",
                "queryType": "COST",
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="oracle",
                service=r.get("service", "OCI"),
                usage_date=r.get("timeUsageStarted", "")[:10],
                amount=float(r.get("computedAmount", 0)),
                currency=r.get("currency", "USD"),
                region=r.get("region"),
                account_id=self.config.get("tenancy_ocid"),
            )
            for r in raw
        ]
