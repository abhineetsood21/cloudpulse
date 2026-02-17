"""
CloudPulse API Client

Usage:
    from cloudpulse import CloudPulseClient

    client = CloudPulseClient("http://localhost:8000", token="your-api-token")

    # List available providers
    catalog = client.get_catalog()

    # Connect a provider
    integration = client.connect("datadog", credentials={
        "api_key": "...", "app_key": "...", "site": "datadoghq.com"
    })

    # Sync cost data
    result = client.sync(integration["id"])

    # Query costs
    costs = client.query_costs(provider="datadog", granularity="daily")
"""

from __future__ import annotations

from typing import Any, Optional

import httpx


class CloudPulseError(Exception):
    """Raised when the CloudPulse API returns an error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class CloudPulseClient:
    """Synchronous client for the CloudPulse v2 API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self._v2 = f"{self.base_url}/api/v2"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(headers=headers, timeout=timeout)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ── HTTP helpers ──────────────────────────────────────────────

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self._v2}{path}"
        resp = self._client.request(method, url, **kwargs)
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            raise CloudPulseError(resp.status_code, detail)
        return resp.json()

    def _get(self, path: str, **params) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, json: Any = None) -> Any:
        return self._request("POST", path, json=json)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    # ── Integrations ─────────────────────────────────────────────

    def get_catalog(self) -> dict:
        """Get the full provider catalog grouped by category."""
        return self._get("/integrations/catalog")

    def list_integrations(self, provider: Optional[str] = None) -> list[dict]:
        """List all active integrations."""
        params = {}
        if provider:
            params["provider"] = provider
        return self._get("/integrations", **params)

    def connect(
        self,
        provider: str,
        credentials: dict,
        display_name: Optional[str] = None,
    ) -> dict:
        """Connect a new provider integration."""
        payload = {
            "provider": provider,
            "credentials": credentials,
        }
        if display_name:
            payload["display_name"] = display_name
        return self._post("/integrations/connect", json=payload)

    def validate(self, integration_id: str) -> dict:
        """Re-validate credentials for an existing integration."""
        return self._post(f"/integrations/{integration_id}/validate")

    def sync(
        self,
        integration_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """Trigger a cost data sync for an integration."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        path = f"/integrations/{integration_id}/sync"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            path = f"{path}?{qs}"
        return self._post(path)

    def disconnect(self, integration_id: str) -> dict:
        """Disconnect an integration."""
        return self._delete(f"/integrations/{integration_id}")

    # ── Cost Queries ─────────────────────────────────────────────

    def query_costs(
        self,
        provider: Optional[str] = None,
        granularity: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[list[str]] = None,
        filter_expr: Optional[str] = None,
        limit: int = 1000,
    ) -> dict:
        """Run a cost query against the DuckDB analytics engine."""
        payload: dict[str, Any] = {
            "granularity": granularity,
            "limit": limit,
        }
        if provider:
            payload["provider"] = provider
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if group_by:
            payload["group_by"] = group_by
        if filter_expr:
            payload["filter"] = filter_expr
        return self._post("/query", json=payload)

    def get_billing_stats(self) -> dict:
        """Get overall billing statistics."""
        return self._get("/query/stats")

    # ── Budgets ──────────────────────────────────────────────────

    def list_budgets(self, page: int = 1, limit: int = 25) -> dict:
        return self._get("/budgets", page=page, limit=limit)

    def create_budget(self, data: dict) -> dict:
        return self._post("/budgets", json=data)

    # ── API Tokens ───────────────────────────────────────────────

    def list_tokens(self, page: int = 1, limit: int = 25) -> dict:
        return self._get("/api_tokens", page=page, limit=limit)

    def create_token(self, name: str, scopes: str = "read") -> dict:
        return self._post("/api_tokens", json={"name": name, "scopes": scopes})

    def revoke_token(self, token_prefix: str) -> dict:
        return self._delete(f"/api_tokens/{token_prefix}")

    # ── Webhooks ─────────────────────────────────────────────────

    def list_webhooks(self) -> list[dict]:
        return self._get("/webhooks")

    def create_webhook(
        self,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> dict:
        payload = {"url": url, "events": events}
        if secret:
            payload["secret"] = secret
        return self._post("/webhooks", json=payload)

    def delete_webhook(self, webhook_id: str) -> dict:
        return self._delete(f"/webhooks/{webhook_id}")
