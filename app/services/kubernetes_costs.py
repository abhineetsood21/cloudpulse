"""
Kubernetes Cost Allocation Service

Allocates Kubernetes node-level costs (from CUR/billing data) to
namespaces and pods proportionally by resource usage.

Computes:
    - Cluster-level cost summary
    - Namespace-level cost breakdown
    - Pod-level cost attribution
    - Idle cost (allocated but unused resources)
    - Rightsizing recommendations

Metrics are pushed by the CloudPulse K8s agent running in each cluster.
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from app.core.database import Base

logger = logging.getLogger(__name__)


# --- In-Memory Store for Agent Metrics ---
# In production, this would be stored in the database.
# For now, the agent pushes metrics and we store them in memory.

_cluster_metrics: dict[str, dict] = {}


class KubernetesCostService:
    """Allocates cloud costs to Kubernetes workloads."""

    def __init__(self):
        pass

    def ingest_metrics(self, cluster_id: str, metrics: dict) -> dict:
        """
        Ingest metrics pushed by the K8s agent.

        Expected metrics payload:
        {
            "cluster_name": "prod-eks-us-east-1",
            "region": "us-east-1",
            "provider": "aws",
            "timestamp": "2026-02-17T00:00:00Z",
            "nodes": [
                {
                    "name": "ip-10-0-1-50",
                    "instance_type": "m5.xlarge",
                    "allocatable_cpu_millicores": 3920,
                    "allocatable_memory_bytes": 15032385536,
                    "capacity_cpu_millicores": 4000,
                    "capacity_memory_bytes": 16106127360,
                }
            ],
            "pods": [
                {
                    "name": "api-gateway-7d8f9-abc12",
                    "namespace": "api-gateway",
                    "node": "ip-10-0-1-50",
                    "cpu_request_millicores": 500,
                    "cpu_limit_millicores": 1000,
                    "cpu_usage_millicores": 350,
                    "memory_request_bytes": 536870912,
                    "memory_limit_bytes": 1073741824,
                    "memory_usage_bytes": 402653184,
                    "labels": {"app": "api-gateway", "team": "backend"}
                }
            ],
            "namespaces": [
                {"name": "api-gateway", "labels": {"team": "backend"}}
            ]
        }
        """
        _cluster_metrics[cluster_id] = {
            **metrics,
            "cluster_id": cluster_id,
            "received_at": datetime.utcnow().isoformat(),
        }
        logger.info(
            f"Ingested metrics for cluster {cluster_id}: "
            f"{len(metrics.get('nodes', []))} nodes, "
            f"{len(metrics.get('pods', []))} pods"
        )
        return {"status": "ok", "cluster_id": cluster_id}

    def list_clusters(self) -> list[dict]:
        """List all clusters with summary stats."""
        clusters = []
        for cluster_id, metrics in _cluster_metrics.items():
            nodes = metrics.get("nodes", [])
            pods = metrics.get("pods", [])

            total_cpu_cap = sum(n.get("allocatable_cpu_millicores", 0) for n in nodes)
            total_cpu_used = sum(p.get("cpu_usage_millicores", 0) for p in pods)
            total_mem_cap = sum(n.get("allocatable_memory_bytes", 0) for n in nodes)
            total_mem_used = sum(p.get("memory_usage_bytes", 0) for p in pods)

            cpu_util = (total_cpu_used / total_cpu_cap * 100) if total_cpu_cap > 0 else 0
            mem_util = (total_mem_used / total_mem_cap * 100) if total_mem_cap > 0 else 0

            # Estimate monthly cost based on node count and typical pricing
            estimated_monthly = self._estimate_cluster_cost(nodes)
            idle_cost = estimated_monthly * (1 - cpu_util / 100) * 0.5  # rough idle estimate

            clusters.append({
                "cluster_id": cluster_id,
                "cluster_name": metrics.get("cluster_name", cluster_id),
                "region": metrics.get("region", ""),
                "provider": metrics.get("provider", ""),
                "node_count": len(nodes),
                "pod_count": len(pods),
                "namespace_count": len(set(p.get("namespace", "") for p in pods)),
                "cpu_utilization_pct": round(cpu_util, 1),
                "memory_utilization_pct": round(mem_util, 1),
                "estimated_monthly_cost": round(estimated_monthly, 2),
                "idle_cost": round(idle_cost, 2),
                "last_updated": metrics.get("received_at"),
            })

        return clusters

    def get_namespace_costs(self, cluster_id: str) -> list[dict]:
        """Get cost breakdown by namespace for a cluster."""
        metrics = _cluster_metrics.get(cluster_id)
        if not metrics:
            return []

        nodes = metrics.get("nodes", [])
        pods = metrics.get("pods", [])

        total_cluster_cost = self._estimate_cluster_cost(nodes)
        total_cpu_cap = sum(n.get("allocatable_cpu_millicores", 0) for n in nodes)
        total_mem_cap = sum(n.get("allocatable_memory_bytes", 0) for n in nodes)

        # Aggregate by namespace
        ns_stats: dict[str, dict] = {}
        for pod in pods:
            ns = pod.get("namespace", "default")
            if ns not in ns_stats:
                ns_stats[ns] = {
                    "pod_count": 0,
                    "cpu_request": 0,
                    "cpu_usage": 0,
                    "cpu_limit": 0,
                    "mem_request": 0,
                    "mem_usage": 0,
                    "mem_limit": 0,
                }
            s = ns_stats[ns]
            s["pod_count"] += 1
            s["cpu_request"] += pod.get("cpu_request_millicores", 0)
            s["cpu_usage"] += pod.get("cpu_usage_millicores", 0)
            s["cpu_limit"] += pod.get("cpu_limit_millicores", 0)
            s["mem_request"] += pod.get("memory_request_bytes", 0)
            s["mem_usage"] += pod.get("memory_usage_bytes", 0)
            s["mem_limit"] += pod.get("memory_limit_bytes", 0)

        result = []
        for ns, s in ns_stats.items():
            # Cost allocation: weighted 50% by CPU request, 50% by memory request
            cpu_share = (s["cpu_request"] / total_cpu_cap) if total_cpu_cap > 0 else 0
            mem_share = (s["mem_request"] / total_mem_cap) if total_mem_cap > 0 else 0
            cost_share = (cpu_share + mem_share) / 2
            ns_cost = total_cluster_cost * cost_share

            # Efficiency: usage / request
            cpu_eff = (s["cpu_usage"] / s["cpu_request"] * 100) if s["cpu_request"] > 0 else 0
            mem_eff = (s["mem_usage"] / s["mem_request"] * 100) if s["mem_request"] > 0 else 0
            efficiency = (cpu_eff + mem_eff) / 2

            result.append({
                "namespace": ns,
                "pod_count": s["pod_count"],
                "cpu_request_millicores": s["cpu_request"],
                "cpu_usage_millicores": s["cpu_usage"],
                "memory_request_bytes": s["mem_request"],
                "memory_usage_bytes": s["mem_usage"],
                "estimated_monthly_cost": round(ns_cost, 2),
                "efficiency_pct": round(efficiency, 1),
            })

        result.sort(key=lambda x: x["estimated_monthly_cost"], reverse=True)
        return result

    def get_rightsizing_recommendations(self, cluster_id: str) -> list[dict]:
        """
        Generate rightsizing recommendations for pods with over-provisioned resources.

        A pod is over-provisioned if usage is < 50% of request.
        """
        metrics = _cluster_metrics.get(cluster_id)
        if not metrics:
            return []

        nodes = metrics.get("nodes", [])
        pods = metrics.get("pods", [])
        total_cluster_cost = self._estimate_cluster_cost(nodes)
        total_cpu_cap = sum(n.get("allocatable_cpu_millicores", 0) for n in nodes)

        recommendations = []
        for pod in pods:
            cpu_req = pod.get("cpu_request_millicores", 0)
            cpu_used = pod.get("cpu_usage_millicores", 0)
            mem_req = pod.get("memory_request_bytes", 0)
            mem_used = pod.get("memory_usage_bytes", 0)

            if cpu_req == 0:
                continue

            cpu_ratio = cpu_used / cpu_req if cpu_req > 0 else 1
            mem_ratio = mem_used / mem_req if mem_req > 0 else 1

            # Flag if usage is less than 50% of request
            if cpu_ratio < 0.5 or mem_ratio < 0.5:
                # Suggest 2x of actual usage as new request (with floor)
                suggested_cpu = max(int(cpu_used * 2), 50)
                suggested_mem = max(int(mem_used * 2), 67108864)  # 64Mi floor

                # Estimate savings
                cpu_saved = max(0, cpu_req - suggested_cpu)
                cost_per_millicore_month = total_cluster_cost / total_cpu_cap if total_cpu_cap > 0 else 0
                savings = cpu_saved * cost_per_millicore_month

                recommendations.append({
                    "pod_name": pod.get("name", ""),
                    "namespace": pod.get("namespace", ""),
                    "current_cpu_request": f"{cpu_req}m",
                    "suggested_cpu_request": f"{suggested_cpu}m",
                    "current_memory_request": self._format_bytes(mem_req),
                    "suggested_memory_request": self._format_bytes(suggested_mem),
                    "cpu_utilization_pct": round(cpu_ratio * 100, 1),
                    "memory_utilization_pct": round(mem_ratio * 100, 1),
                    "estimated_monthly_savings": round(savings, 2),
                })

        recommendations.sort(key=lambda x: x["estimated_monthly_savings"], reverse=True)
        return recommendations

    def _estimate_cluster_cost(self, nodes: list[dict]) -> float:
        """Estimate monthly cluster cost based on node instance types."""
        # Rough hourly cost by instance type (AWS on-demand)
        HOURLY_COSTS = {
            "m5.large": 0.096, "m5.xlarge": 0.192, "m5.2xlarge": 0.384,
            "m5.4xlarge": 0.768, "c5.large": 0.085, "c5.xlarge": 0.17,
            "c5.2xlarge": 0.34, "r5.large": 0.126, "r5.xlarge": 0.252,
            "t3.medium": 0.0416, "t3.large": 0.0832, "t3.xlarge": 0.1664,
        }
        DEFAULT_HOURLY = 0.10  # fallback

        total = 0
        for node in nodes:
            itype = node.get("instance_type", "")
            hourly = HOURLY_COSTS.get(itype, DEFAULT_HOURLY)
            total += hourly * 730  # ~730 hours/month

        return total

    @staticmethod
    def _format_bytes(b: int) -> str:
        """Format bytes to human-readable string."""
        if b >= 1073741824:
            return f"{b / 1073741824:.0f}Gi"
        elif b >= 1048576:
            return f"{b / 1048576:.0f}Mi"
        elif b >= 1024:
            return f"{b / 1024:.0f}Ki"
        return f"{b}B"


# Module-level singleton
_service: Optional[KubernetesCostService] = None


def get_kubernetes_cost_service() -> KubernetesCostService:
    global _service
    if _service is None:
        _service = KubernetesCostService()
    return _service
