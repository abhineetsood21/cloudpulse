"""
v2 Kubernetes API — Cluster cost visibility and rightsizing.

Endpoints:
    POST /api/v2/kubernetes/metrics              - Agent pushes metrics
    GET  /api/v2/kubernetes/clusters             - List clusters with costs
    GET  /api/v2/kubernetes/clusters/{id}/namespaces  - Namespace costs
    GET  /api/v2/kubernetes/clusters/{id}/rightsizing  - Rightsizing recs
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.kubernetes_costs import get_kubernetes_cost_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kubernetes", tags=["Kubernetes"])


class MetricsPayload(BaseModel):
    cluster_name: str
    region: str = ""
    provider: str = ""
    timestamp: Optional[str] = None
    nodes: list[dict] = Field(default_factory=list)
    pods: list[dict] = Field(default_factory=list)
    namespaces: list[dict] = Field(default_factory=list)


@router.post("/metrics")
async def push_metrics(cluster_id: str, payload: MetricsPayload):
    """
    Receive metrics from the CloudPulse K8s agent.

    The agent running in each cluster pushes node/pod metrics every 5 minutes.
    """
    svc = get_kubernetes_cost_service()
    result = svc.ingest_metrics(cluster_id, payload.model_dump())
    return result


@router.get("/clusters")
async def list_clusters():
    """List all Kubernetes clusters with cost summaries."""
    svc = get_kubernetes_cost_service()
    clusters = svc.list_clusters()
    return {"clusters": clusters, "total": len(clusters)}


@router.get("/clusters/{cluster_id}/namespaces")
async def get_namespace_costs(cluster_id: str):
    """Get namespace-level cost breakdown for a cluster."""
    svc = get_kubernetes_cost_service()
    namespaces = svc.get_namespace_costs(cluster_id)
    if not namespaces:
        raise HTTPException(
            status_code=404,
            detail=f"No data for cluster {cluster_id}. Ensure the agent is running.",
        )
    return {"cluster_id": cluster_id, "namespaces": namespaces}


@router.get("/clusters/{cluster_id}/rightsizing")
async def get_rightsizing(cluster_id: str):
    """Get rightsizing recommendations for a cluster."""
    svc = get_kubernetes_cost_service()
    recs = svc.get_rightsizing_recommendations(cluster_id)
    total_savings = sum(r["estimated_monthly_savings"] for r in recs)
    return {
        "cluster_id": cluster_id,
        "recommendations": recs,
        "total_potential_savings": round(total_savings, 2),
    }
