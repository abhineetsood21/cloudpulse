"""CloudPulse Python SDK Client."""

from __future__ import annotations

from typing import Any

import httpx

from cloudpulse.models import (
    Workspace, WorkspaceList,
    CostReport, CostReportList,
    Folder, FolderList,
    SavedFilter, SavedFilterList,
    Dashboard, DashboardList,
    Segment, SegmentList,
    Team, TeamList,
    AccessGrant, AccessGrantList,
    VirtualTag, VirtualTagList,
    APIToken, APITokenCreated, APITokenList,
    ResourceReport, ResourceReportList,
    Message,
)


class CloudPulseError(Exception):
    """Base exception for CloudPulse SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, detail: str | None = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class CloudPulseClient:
    """
    Synchronous client for the CloudPulse v2 API.

    Usage:
        client = CloudPulseClient(api_token="cpls_...")
        workspaces = client.workspaces.list()
    """

    DEFAULT_BASE_URL = "https://api.cloudpulse.dev"
    API_VERSION = "v2"

    def __init__(
        self,
        api_token: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
    ):
        self._base_url = f"{base_url.rstrip('/')}/api/{self.API_VERSION}"
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "User-Agent": "cloudpulse-python/0.1.0",
            },
            timeout=timeout,
        )

        # Resource namespaces
        self.workspaces = WorkspacesResource(self)
        self.cost_reports = CostReportsResource(self)
        self.folders = FoldersResource(self)
        self.saved_filters = SavedFiltersResource(self)
        self.dashboards = DashboardsResource(self)
        self.segments = SegmentsResource(self)
        self.teams = TeamsResource(self)
        self.access_grants = AccessGrantsResource(self)
        self.virtual_tags = VirtualTagsResource(self)
        self.api_tokens = APITokensResource(self)
        self.resource_reports = ResourceReportsResource(self)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        response = self._client.request(method, path, **kwargs)
        if response.status_code >= 400:
            detail = ""
            try:
                body = response.json()
                detail = body.get("detail", "")
            except Exception:
                detail = response.text
            raise CloudPulseError(
                f"API error {response.status_code}: {detail}",
                status_code=response.status_code,
                detail=detail,
            )
        return response.json()

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ---------------------------------------------------------------------------
# Resource classes
# ---------------------------------------------------------------------------

class _Resource:
    def __init__(self, client: CloudPulseClient):
        self._client = client

    def _get(self, path: str, **params) -> dict:
        return self._client._request("GET", path, params=params)

    def _post(self, path: str, data: dict) -> dict:
        return self._client._request("POST", path, json=data)

    def _put(self, path: str, data: dict) -> dict:
        return self._client._request("PUT", path, json=data)

    def _delete(self, path: str) -> dict:
        return self._client._request("DELETE", path)


class WorkspacesResource(_Resource):
    def list(self, page: int = 1, limit: int = 25) -> WorkspaceList:
        return WorkspaceList(**self._get("/workspaces", page=page, limit=limit))

    def get(self, token: str) -> Workspace:
        return Workspace(**self._get(f"/workspaces/{token}"))

    def create(self, name: str) -> Workspace:
        return Workspace(**self._post("/workspaces", {"name": name}))

    def update(self, token: str, name: str) -> Workspace:
        return Workspace(**self._put(f"/workspaces/{token}", {"name": name}))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/workspaces/{token}"))


class CostReportsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> CostReportList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return CostReportList(**self._get("/cost_reports", **params))

    def get(self, token: str) -> CostReport:
        return CostReport(**self._get(f"/cost_reports/{token}"))

    def create(self, **kwargs) -> CostReport:
        return CostReport(**self._post("/cost_reports", kwargs))

    def update(self, token: str, **kwargs) -> CostReport:
        return CostReport(**self._put(f"/cost_reports/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/cost_reports/{token}"))


class FoldersResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> FolderList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return FolderList(**self._get("/folders", **params))

    def get(self, token: str) -> Folder:
        return Folder(**self._get(f"/folders/{token}"))

    def create(self, **kwargs) -> Folder:
        return Folder(**self._post("/folders", kwargs))

    def update(self, token: str, **kwargs) -> Folder:
        return Folder(**self._put(f"/folders/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/folders/{token}"))


class SavedFiltersResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> SavedFilterList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return SavedFilterList(**self._get("/saved_filters", **params))

    def get(self, token: str) -> SavedFilter:
        return SavedFilter(**self._get(f"/saved_filters/{token}"))

    def create(self, **kwargs) -> SavedFilter:
        return SavedFilter(**self._post("/saved_filters", kwargs))

    def update(self, token: str, **kwargs) -> SavedFilter:
        return SavedFilter(**self._put(f"/saved_filters/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/saved_filters/{token}"))


class DashboardsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> DashboardList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return DashboardList(**self._get("/dashboards", **params))

    def get(self, token: str) -> Dashboard:
        return Dashboard(**self._get(f"/dashboards/{token}"))

    def create(self, **kwargs) -> Dashboard:
        return Dashboard(**self._post("/dashboards", kwargs))

    def update(self, token: str, **kwargs) -> Dashboard:
        return Dashboard(**self._put(f"/dashboards/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/dashboards/{token}"))


class SegmentsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> SegmentList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return SegmentList(**self._get("/segments", **params))

    def get(self, token: str) -> Segment:
        return Segment(**self._get(f"/segments/{token}"))

    def create(self, **kwargs) -> Segment:
        return Segment(**self._post("/segments", kwargs))

    def update(self, token: str, **kwargs) -> Segment:
        return Segment(**self._put(f"/segments/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/segments/{token}"))


class TeamsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> TeamList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return TeamList(**self._get("/teams", **params))

    def get(self, token: str) -> Team:
        return Team(**self._get(f"/teams/{token}"))

    def create(self, **kwargs) -> Team:
        return Team(**self._post("/teams", kwargs))

    def update(self, token: str, **kwargs) -> Team:
        return Team(**self._put(f"/teams/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/teams/{token}"))


class AccessGrantsResource(_Resource):
    def list(self, team_token: str | None = None, page: int = 1, limit: int = 25) -> AccessGrantList:
        params = {"page": page, "limit": limit}
        if team_token:
            params["team_token"] = team_token
        return AccessGrantList(**self._get("/access_grants", **params))

    def create(self, **kwargs) -> AccessGrant:
        return AccessGrant(**self._post("/access_grants", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/access_grants/{token}"))


class VirtualTagsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> VirtualTagList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return VirtualTagList(**self._get("/virtual_tags", **params))

    def get(self, token: str) -> VirtualTag:
        return VirtualTag(**self._get(f"/virtual_tags/{token}"))

    def create(self, **kwargs) -> VirtualTag:
        return VirtualTag(**self._post("/virtual_tags", kwargs))

    def update(self, token: str, **kwargs) -> VirtualTag:
        return VirtualTag(**self._put(f"/virtual_tags/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/virtual_tags/{token}"))


class APITokensResource(_Resource):
    def list(self, page: int = 1, limit: int = 25) -> APITokenList:
        return APITokenList(**self._get("/api_tokens", page=page, limit=limit))

    def create(self, name: str, scopes: str = "read") -> APITokenCreated:
        return APITokenCreated(**self._post("/api_tokens", {"name": name, "scopes": scopes}))

    def revoke(self, token_prefix: str) -> Message:
        return Message(**self._delete(f"/api_tokens/{token_prefix}"))


class ResourceReportsResource(_Resource):
    def list(self, workspace_token: str | None = None, page: int = 1, limit: int = 25) -> ResourceReportList:
        params = {"page": page, "limit": limit}
        if workspace_token:
            params["workspace_token"] = workspace_token
        return ResourceReportList(**self._get("/resource_reports", **params))

    def get(self, token: str) -> ResourceReport:
        return ResourceReport(**self._get(f"/resource_reports/{token}"))

    def create(self, **kwargs) -> ResourceReport:
        return ResourceReport(**self._post("/resource_reports", kwargs))

    def update(self, token: str, **kwargs) -> ResourceReport:
        return ResourceReport(**self._put(f"/resource_reports/{token}", kwargs))

    def delete(self, token: str) -> Message:
        return Message(**self._delete(f"/resource_reports/{token}"))
