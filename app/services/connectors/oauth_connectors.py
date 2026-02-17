"""
OAuth / Token Connectors — GitHub, PlanetScale
"""

import logging
from datetime import date
from typing import Any

import httpx

from app.services.connectors.base import (
    BaseConnector, FocusRecord, ValidationResult,
)

logger = logging.getLogger(__name__)


class GitHubConnector(BaseConnector):
    provider_key = "github"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config['access_token']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def validate(self) -> ValidationResult:
        try:
            resp = httpx.get(
                f"https://api.github.com/orgs/{self.config['org']}",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return ValidationResult(valid=True, account_identifier=data.get("login"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        org = self.config["org"]
        results = []
        for billing_type in ("actions", "packages", "shared-storage"):
            resp = httpx.get(
                f"https://api.github.com/orgs/{org}/settings/billing/{billing_type}",
                headers=self._headers(),
                timeout=15,
            )
            if resp.is_success:
                data = resp.json()
                data["_billing_type"] = billing_type
                results.append(data)
        return results

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        records = []
        for r in raw:
            billing_type = r.get("_billing_type", "github")
            amount = 0.0
            if billing_type == "actions":
                amount = float(r.get("total_paid_minutes_used", 0)) * 0.008  # ~$0.008/min
            elif billing_type == "packages":
                amount = float(r.get("total_paid_gigabytes_bandwidth_used", 0)) * 0.50
            elif billing_type == "shared-storage":
                amount = float(r.get("estimated_paid_storage_for_month", 0)) * 0.25
            records.append(FocusRecord(
                provider="github",
                service=f"GitHub {billing_type.replace('-', ' ').title()}",
                usage_date=date.today().isoformat(),
                amount=round(amount, 4),
                currency="USD",
                account_id=self.config["org"],
            ))
        return records


class PlanetScaleConnector(BaseConnector):
    provider_key = "planetscale"

    def _headers(self) -> dict:
        return {
            "Authorization": f"{self.config['service_token_id']}:{self.config['service_token']}",
            "Accept": "application/json",
        }

    def validate(self) -> ValidationResult:
        try:
            org = self.config["organization"]
            resp = httpx.get(
                f"https://api.planetscale.com/v1/organizations/{org}",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            return ValidationResult(valid=True, account_identifier=org)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        org = self.config["organization"]
        resp = httpx.get(
            f"https://api.planetscale.com/v1/organizations/{org}/invoices",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="planetscale",
                service="PlanetScale",
                usage_date=r.get("period_start", "")[:10],
                amount=float(r.get("total_in_cents", 0)) / 100.0,
                currency="USD",
                account_id=self.config["organization"],
            )
            for r in raw
        ]
