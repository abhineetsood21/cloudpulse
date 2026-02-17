"""
API-Key Based Connectors

Covers providers that authenticate via API key / token pairs:
Datadog, MongoDB, Confluent, Fastly, New Relic, Coralogix, Linode,
OpenAI, Anthropic, Grafana Cloud, ClickHouse, Anyscale, Temporal Cloud,
Twilio, Cursor.
"""

import logging
from datetime import date
from typing import Any

import httpx

from app.services.connectors.base import (
    BaseConnector, FocusRecord, ValidationResult,
)

logger = logging.getLogger(__name__)


# ── Helper ────────────────────────────────────────────────────────

def _get(url: str, headers: dict, params: dict | None = None) -> dict:
    """Synchronous GET with httpx."""
    resp = httpx.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Datadog ───────────────────────────────────────────────────────

class DatadogConnector(BaseConnector):
    provider_key = "datadog"

    def validate(self) -> ValidationResult:
        site = self.config.get("site", "datadoghq.com")
        try:
            data = _get(
                f"https://api.{site}/api/v1/validate",
                headers={
                    "DD-API-KEY": self.config["api_key"],
                    "DD-APPLICATION-KEY": self.config["app_key"],
                },
            )
            return ValidationResult(valid=data.get("valid", False))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        site = self.config.get("site", "datadoghq.com")
        headers = {
            "DD-API-KEY": self.config["api_key"],
            "DD-APPLICATION-KEY": self.config["app_key"],
        }
        data = _get(
            f"https://api.{site}/api/v2/usage/cost_by_org",
            headers=headers,
            params={"start_month": start_date.strftime("%Y-%m")},
        )
        return data.get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        records = []
        for entry in raw:
            attrs = entry.get("attributes", {})
            for charge in attrs.get("charges", []):
                records.append(FocusRecord(
                    provider="datadog",
                    service=charge.get("product_name", "Datadog"),
                    usage_date=attrs.get("date", ""),
                    amount=charge.get("cost", 0.0),
                    currency="USD",
                    account_id=attrs.get("org_name"),
                ))
        return records


# ── MongoDB Atlas ─────────────────────────────────────────────────

class MongoDBConnector(BaseConnector):
    provider_key = "mongodb"

    def validate(self) -> ValidationResult:
        try:
            data = _get(
                f"https://cloud.mongodb.com/api/atlas/v2/orgs/{self.config['org_id']}",
                headers={"Accept": "application/vnd.atlas.2023-01-01+json"},
            )
            return ValidationResult(valid=True, account_identifier=data.get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            f"https://cloud.mongodb.com/api/atlas/v2/orgs/{self.config['org_id']}/invoices",
            headers={"Accept": "application/vnd.atlas.2023-01-01+json"},
        )
        return data.get("results", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        records = []
        for inv in raw:
            for item in inv.get("lineItems", []):
                records.append(FocusRecord(
                    provider="mongodb",
                    service=item.get("sku", "MongoDB Atlas"),
                    usage_date=inv.get("created", "")[:10],
                    amount=item.get("totalPriceCents", 0) / 100.0,
                    currency="USD",
                    account_id=self.config.get("org_id"),
                ))
        return records


# ── Confluent ─────────────────────────────────────────────────────

class ConfluentConnector(BaseConnector):
    provider_key = "confluent"

    def _headers(self) -> dict:
        import base64
        creds = base64.b64encode(
            f"{self.config['api_key']}:{self.config['api_secret']}".encode()
        ).decode()
        return {"Authorization": f"Basic {creds}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get("https://api.confluent.cloud/org/v2/environments", headers=self._headers())
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://api.confluent.cloud/billing/v1/costs",
            headers=self._headers(),
            params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )
        return data.get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="confluent",
                service=r.get("resource", {}).get("display_name", "Confluent Cloud"),
                usage_date=r.get("start_date", "")[:10],
                amount=float(r.get("amount", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Fastly ────────────────────────────────────────────────────────

class FastlyConnector(BaseConnector):
    provider_key = "fastly"

    def validate(self) -> ValidationResult:
        try:
            data = _get(
                "https://api.fastly.com/current_customer",
                headers={"Fastly-Key": self.config["api_key"]},
            )
            return ValidationResult(valid=True, account_identifier=data.get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://api.fastly.com/billing/v3/invoices",
            headers={"Fastly-Key": self.config["api_key"]},
        )
        return data.get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="fastly",
                service="Fastly CDN",
                usage_date=r.get("attributes", {}).get("invoice_date", "")[:10],
                amount=float(r.get("attributes", {}).get("total", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── New Relic ─────────────────────────────────────────────────────

class NewRelicConnector(BaseConnector):
    provider_key = "new_relic"

    def validate(self) -> ValidationResult:
        try:
            resp = httpx.post(
                "https://api.newrelic.com/graphql",
                headers={"API-Key": self.config["api_key"]},
                json={"query": "{ actor { user { name } } }"},
                timeout=15,
            )
            resp.raise_for_status()
            return ValidationResult(valid=True, account_identifier=self.config.get("account_id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        query = """
        {
          actor {
            account(id: %s) {
              nrql(query: "SELECT sum(estimatedCost) FROM NrConsumption SINCE '%s' UNTIL '%s' FACET productLine TIMESERIES 1 day") {
                results
              }
            }
          }
        }
        """ % (self.config["account_id"], start_date, end_date)
        resp = httpx.post(
            "https://api.newrelic.com/graphql",
            headers={"API-Key": self.config["api_key"]},
            json={"query": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("actor", {}).get("account", {}).get("nrql", {}).get("results", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="new_relic",
                service=r.get("facet", "New Relic"),
                usage_date=r.get("beginTimeSeconds", ""),
                amount=float(r.get("sum.estimatedCost", 0)),
                currency="USD",
                account_id=self.config.get("account_id"),
            )
            for r in raw
        ]


# ── Coralogix ─────────────────────────────────────────────────────

class CoralogixConnector(BaseConnector):
    provider_key = "coralogix"

    def validate(self) -> ValidationResult:
        domain = self.config.get("domain", "coralogix.com")
        try:
            _get(
                f"https://api.{domain}/api/v1/external/team",
                headers={"Authorization": f"Bearer {self.config['api_key']}"},
            )
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        domain = self.config.get("domain", "coralogix.com")
        data = _get(
            f"https://api.{domain}/api/v1/external/usage",
            headers={"Authorization": f"Bearer {self.config['api_key']}"},
        )
        return data.get("usage", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="coralogix",
                service=r.get("pillar", "Coralogix"),
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("cost", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Linode ────────────────────────────────────────────────────────

class LinodeConnector(BaseConnector):
    provider_key = "linode"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get("https://api.linode.com/v4/account", headers=self._headers())
            return ValidationResult(valid=True, account_identifier=data.get("euuid"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get("https://api.linode.com/v4/account/invoices", headers=self._headers())
        return data.get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="linode",
                service="Linode",
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("total", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── OpenAI ────────────────────────────────────────────────────────

class OpenAIConnector(BaseConnector):
    provider_key = "openai"

    def _headers(self) -> dict:
        h = {"Authorization": f"Bearer {self.config['api_key']}"}
        if self.config.get("org_id"):
            h["OpenAI-Organization"] = self.config["org_id"]
        return h

    def validate(self) -> ValidationResult:
        try:
            data = _get("https://api.openai.com/v1/organization", headers=self._headers())
            return ValidationResult(valid=True, account_identifier=data.get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://api.openai.com/v1/organization/costs",
            headers=self._headers(),
            params={"start_time": int(start_date.strftime("%s")), "end_time": int(end_date.strftime("%s"))},
        )
        return data.get("data", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        records = []
        for bucket in raw:
            for result in bucket.get("results", []):
                records.append(FocusRecord(
                    provider="openai",
                    service=result.get("object", "OpenAI API"),
                    usage_date=bucket.get("start_time", "")[:10],
                    amount=float(result.get("amount", {}).get("value", 0)),
                    currency="USD",
                ))
        return records


# ── Anthropic ─────────────────────────────────────────────────────

class AnthropicConnector(BaseConnector):
    provider_key = "anthropic"

    def _headers(self) -> dict:
        return {
            "x-api-key": self.config["api_key"],
            "anthropic-version": "2024-01-01",
        }

    def validate(self) -> ValidationResult:
        try:
            data = _get(
                "https://api.anthropic.com/v1/organizations/self",
                headers=self._headers(),
            )
            return ValidationResult(valid=True, account_identifier=data.get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://api.anthropic.com/v1/organizations/self/usage",
            headers=self._headers(),
            params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )
        return data.get("daily_usage", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="anthropic",
                service="Anthropic API",
                usage_date=r.get("date", ""),
                amount=float(r.get("spend", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Grafana Cloud ─────────────────────────────────────────────────

class GrafanaCloudConnector(BaseConnector):
    provider_key = "grafana_cloud"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def validate(self) -> ValidationResult:
        slug = self.config.get("org_slug", "")
        try:
            data = _get(
                f"https://grafana.com/api/orgs/{slug}",
                headers=self._headers(),
            )
            return ValidationResult(valid=True, account_identifier=str(data.get("id")))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        slug = self.config["org_slug"]
        data = _get(
            f"https://grafana.com/api/orgs/{slug}/billing/usage",
            headers=self._headers(),
        )
        return data.get("items", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="grafana_cloud",
                service=r.get("product", "Grafana Cloud"),
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("cost", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── ClickHouse Cloud ──────────────────────────────────────────────

class ClickHouseConnector(BaseConnector):
    provider_key = "clickhouse"

    def _headers(self) -> dict:
        import base64
        creds = base64.b64encode(
            f"{self.config['api_key_id']}:{self.config['api_key_secret']}".encode()
        ).decode()
        return {"Authorization": f"Basic {creds}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get(
                f"https://api.clickhouse.cloud/v1/organizations/{self.config['org_id']}",
                headers=self._headers(),
            )
            return ValidationResult(valid=True, account_identifier=data.get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            f"https://api.clickhouse.cloud/v1/organizations/{self.config['org_id']}/billing",
            headers=self._headers(),
        )
        return data.get("usage", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="clickhouse",
                service="ClickHouse Cloud",
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("total", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Anyscale ──────────────────────────────────────────────────────

class AnyscaleConnector(BaseConnector):
    provider_key = "anyscale"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get("https://console.anyscale.com/api/v2/organization", headers=self._headers())
            return ValidationResult(valid=True, account_identifier=data.get("result", {}).get("id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://console.anyscale.com/api/v2/billing/usage",
            headers=self._headers(),
            params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )
        return data.get("results", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="anyscale",
                service=r.get("product", "Anyscale"),
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("cost", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Temporal Cloud ────────────────────────────────────────────────

class TemporalCloudConnector(BaseConnector):
    provider_key = "temporal_cloud"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get("https://saas-api.tmprl.cloud/api/v1/namespaces", headers=self._headers())
            return ValidationResult(valid=True)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://saas-api.tmprl.cloud/api/v1/billing/usage",
            headers=self._headers(),
        )
        return data.get("usage", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="temporal_cloud",
                service="Temporal Cloud",
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("cost", 0)),
                currency="USD",
            )
            for r in raw
        ]


# ── Twilio ────────────────────────────────────────────────────────

class TwilioConnector(BaseConnector):
    provider_key = "twilio"

    def validate(self) -> ValidationResult:
        try:
            resp = httpx.get(
                f"https://api.twilio.com/2010-04-01/Accounts/{self.config['account_sid']}.json",
                auth=(self.config["account_sid"], self.config["auth_token"]),
                timeout=15,
            )
            resp.raise_for_status()
            return ValidationResult(valid=True, account_identifier=self.config["account_sid"])
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        resp = httpx.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.config['account_sid']}/Usage/Records/Daily.json",
            auth=(self.config["account_sid"], self.config["auth_token"]),
            params={"StartDate": start_date.isoformat(), "EndDate": end_date.isoformat()},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("usage_records", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="twilio",
                service=r.get("category", "Twilio"),
                usage_date=r.get("start_date", ""),
                amount=float(r.get("price", 0)),
                currency=r.get("price_unit", "USD"),
                usage_type=r.get("description"),
                usage_quantity=float(r.get("count", 0)),
            )
            for r in raw
        ]


# ── Cursor ────────────────────────────────────────────────────────

class CursorConnector(BaseConnector):
    provider_key = "cursor"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}"}

    def validate(self) -> ValidationResult:
        try:
            data = _get(
                "https://api.cursor.com/v1/team",
                headers=self._headers(),
            )
            return ValidationResult(valid=True, account_identifier=self.config.get("team_id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        data = _get(
            "https://api.cursor.com/v1/usage",
            headers=self._headers(),
            params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        )
        return data.get("usage", [])

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return [
            FocusRecord(
                provider="cursor",
                service="Cursor",
                usage_date=r.get("date", "")[:10],
                amount=float(r.get("cost", 0)),
                currency="USD",
            )
            for r in raw
        ]
