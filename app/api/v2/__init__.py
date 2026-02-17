"""
CloudPulse v2 API Router.

Aggregates all v2 sub-routers into a single router mounted at /api/v2.
"""

from fastapi import APIRouter

from app.api.v2.workspaces import router as workspaces_router
from app.api.v2.cost_reports import router as cost_reports_router
from app.api.v2.folders import router as folders_router
from app.api.v2.saved_filters import router as saved_filters_router
from app.api.v2.dashboards import router as dashboards_router
from app.api.v2.segments import router as segments_router
from app.api.v2.teams import router as teams_router
from app.api.v2.virtual_tags import router as virtual_tags_router
from app.api.v2.tokens import router as tokens_router
from app.api.v2.reports import router as reports_router
from app.api.v2.exports import router as exports_router
from app.api.v2.query import router as query_router
from app.api.v2.providers import router as providers_router
from app.api.v2.kubernetes import router as kubernetes_router
from app.api.v2.integrations import router as integrations_router
from app.api.v2.webhooks import router as webhooks_router
from app.api.v2.dashboard import router as dashboard_router

v2_router = APIRouter()

v2_router.include_router(workspaces_router)
v2_router.include_router(cost_reports_router)
v2_router.include_router(folders_router)
v2_router.include_router(saved_filters_router)
v2_router.include_router(dashboards_router)
v2_router.include_router(segments_router)
v2_router.include_router(teams_router)
v2_router.include_router(virtual_tags_router)
v2_router.include_router(tokens_router)
v2_router.include_router(reports_router)
v2_router.include_router(exports_router)
v2_router.include_router(query_router)
v2_router.include_router(providers_router)
v2_router.include_router(kubernetes_router)
v2_router.include_router(integrations_router)
v2_router.include_router(webhooks_router)
v2_router.include_router(dashboard_router)
