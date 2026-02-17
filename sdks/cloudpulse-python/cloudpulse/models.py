"""CloudPulse SDK data models."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PaginatedLinks(BaseModel):
    self_link: str | None = Field(None, alias="self")
    next: str | None = None
    prev: str | None = None


# --- Workspaces ---

class Workspace(BaseModel):
    token: str
    name: str
    is_default: bool = False
    created_at: datetime


class WorkspaceList(BaseModel):
    workspaces: list[Workspace] = []
    links: dict = {}


# --- Cost Reports ---

class CostReport(BaseModel):
    token: str
    title: str
    workspace_token: str | None = None
    folder_token: str | None = None
    filter: str | None = None
    groupings: str = "service"
    date_interval: str = "last_30_days"
    date_bucket: str = "day"
    start_date: date | None = None
    end_date: date | None = None
    settings: dict = {}
    created_at: datetime


class CostReportList(BaseModel):
    cost_reports: list[CostReport] = []
    links: dict = {}


# --- Folders ---

class Folder(BaseModel):
    token: str
    title: str
    workspace_token: str | None = None
    parent_folder_token: str | None = None
    created_at: datetime


class FolderList(BaseModel):
    folders: list[Folder] = []
    links: dict = {}


# --- Saved Filters ---

class SavedFilter(BaseModel):
    token: str
    title: str
    filter: str
    created_at: datetime


class SavedFilterList(BaseModel):
    saved_filters: list[SavedFilter] = []
    links: dict = {}


# --- Dashboards ---

class Dashboard(BaseModel):
    token: str
    title: str
    widgets: list[dict] = []
    date_interval: str = "last_30_days"
    start_date: date | None = None
    end_date: date | None = None
    created_at: datetime


class DashboardList(BaseModel):
    dashboards: list[Dashboard] = []
    links: dict = {}


# --- Segments ---

class Segment(BaseModel):
    token: str
    title: str
    description: str | None = None
    filter: str | None = None
    priority: int = 0
    track_unallocated: bool = False
    created_at: datetime


class SegmentList(BaseModel):
    segments: list[Segment] = []
    links: dict = {}


# --- Teams ---

class Team(BaseModel):
    token: str
    name: str
    description: str | None = None
    created_at: datetime


class TeamList(BaseModel):
    teams: list[Team] = []
    links: dict = {}


# --- Access Grants ---

class AccessGrant(BaseModel):
    token: str
    team_token: str | None = None
    resource_type: str
    resource_token: str
    access_level: str = "viewer"
    created_at: datetime


class AccessGrantList(BaseModel):
    access_grants: list[AccessGrant] = []
    links: dict = {}


# --- Virtual Tags ---

class VirtualTag(BaseModel):
    token: str
    key: str
    description: str | None = None
    overridable: bool = True
    backfill_until: date | None = None
    values: list[dict] = []
    created_at: datetime


class VirtualTagList(BaseModel):
    virtual_tags: list[VirtualTag] = []
    links: dict = {}


# --- API Tokens ---

class APIToken(BaseModel):
    token_prefix: str
    name: str
    scopes: str
    is_active: bool = True
    last_used_at: datetime | None = None
    created_at: datetime


class APITokenCreated(APIToken):
    token: str


class APITokenList(BaseModel):
    api_tokens: list[APIToken] = []
    links: dict = {}


# --- Resource Reports ---

class ResourceReport(BaseModel):
    token: str
    title: str
    filter: str | None = None
    groupings: str = "resource_id"
    columns: list[str] = []
    created_at: datetime


class ResourceReportList(BaseModel):
    resource_reports: list[ResourceReport] = []
    links: dict = {}


# --- Shared ---

class Message(BaseModel):
    message: str
