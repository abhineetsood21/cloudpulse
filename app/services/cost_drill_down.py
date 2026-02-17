"""
Cost Drill-Down Service ("Why?" Feature)

Compares two time periods and identifies which services and resources
drove the biggest cost changes. This is the killer feature that makes
CloudPulse actionable — not just "your costs went up" but "here's WHY."
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

from app.services.local_cost_explorer import LocalCostExplorerService

logger = logging.getLogger(__name__)


class CostDrillDownService:
    """Explains cost changes between two periods."""

    def __init__(self, cost_service: LocalCostExplorerService | None = None):
        self.cost_service = cost_service or LocalCostExplorerService()

    def analyze_cost_changes(
        self,
        current_start: date,
        current_end: date,
        previous_start: date | None = None,
        previous_end: date | None = None,
    ) -> dict:
        """
        Compare current period vs previous period and explain changes.

        If previous dates aren't provided, defaults to the same-length
        period immediately before current_start.

        Returns:
        {
            "current_period": {"start": "...", "end": "...", "total": 123.45},
            "previous_period": {"start": "...", "end": "...", "total": 100.00},
            "total_change": 23.45,
            "total_change_pct": 0.2345,
            "direction": "increase",
            "service_changes": [
                {
                    "service": "Amazon EC2",
                    "current_amount": 80.00,
                    "previous_amount": 50.00,
                    "change": 30.00,
                    "change_pct": 0.60,
                    "impact_pct": 0.65,  # % of total change this service accounts for
                    "direction": "increase"
                },
                ...
            ],
            "top_increases": [...],
            "top_decreases": [...],
            "new_services": [...],
            "removed_services": [...]
        }
        """
        # Calculate previous period if not provided
        period_days = (current_end - current_start).days
        if not previous_start:
            previous_end = current_start
            previous_start = previous_end - timedelta(days=period_days)
        if not previous_end:
            previous_end = previous_start + timedelta(days=period_days)

        # Fetch cost data for both periods
        current_costs = self.cost_service.get_cost_by_service(current_start, current_end)
        previous_costs = self.cost_service.get_cost_by_service(previous_start, previous_end)

        # Aggregate by service
        current_by_service = defaultdict(float)
        for record in current_costs:
            current_by_service[record["service"]] += record["amount"]

        previous_by_service = defaultdict(float)
        for record in previous_costs:
            previous_by_service[record["service"]] += record["amount"]

        # Calculate totals
        current_total = sum(current_by_service.values())
        previous_total = sum(previous_by_service.values())
        total_change = current_total - previous_total
        total_change_pct = (total_change / previous_total) if previous_total > 0 else 0

        # Calculate per-service changes
        all_services = set(current_by_service.keys()) | set(previous_by_service.keys())
        service_changes = []

        for service in all_services:
            curr = current_by_service.get(service, 0)
            prev = previous_by_service.get(service, 0)
            change = curr - prev

            if abs(change) < 0.01:
                continue

            change_pct = (change / prev) if prev > 0 else (1.0 if curr > 0 else 0)
            impact_pct = (change / total_change) if abs(total_change) > 0.01 else 0

            service_changes.append({
                "service": service,
                "current_amount": round(curr, 2),
                "previous_amount": round(prev, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 4),
                "impact_pct": round(abs(impact_pct), 4),
                "direction": "increase" if change > 0 else "decrease",
            })

        # Sort by absolute change (biggest movers first)
        service_changes.sort(key=lambda x: abs(x["change"]), reverse=True)

        # Categorize
        top_increases = [s for s in service_changes if s["direction"] == "increase"]
        top_decreases = [s for s in service_changes if s["direction"] == "decrease"]
        new_services = [
            s for s in service_changes
            if s["previous_amount"] == 0 and s["current_amount"] > 0
        ]
        removed_services = [
            s for s in service_changes
            if s["current_amount"] == 0 and s["previous_amount"] > 0
        ]

        return {
            "current_period": {
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
                "total": round(current_total, 2),
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat(),
                "total": round(previous_total, 2),
            },
            "total_change": round(total_change, 2),
            "total_change_pct": round(total_change_pct, 4),
            "direction": "increase" if total_change > 0 else ("decrease" if total_change < 0 else "unchanged"),
            "service_changes": service_changes,
            "top_increases": top_increases[:10],
            "top_decreases": top_decreases[:10],
            "new_services": new_services,
            "removed_services": removed_services,
        }

    def analyze_daily_change(self, target_date: date | None = None) -> dict:
        """
        Quick analysis: compare target_date vs the day before.
        Default: yesterday vs day before yesterday.
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        return self.analyze_cost_changes(
            current_start=target_date,
            current_end=target_date + timedelta(days=1),
            previous_start=target_date - timedelta(days=1),
            previous_end=target_date,
        )

    def analyze_weekly_change(self, end_date: date | None = None) -> dict:
        """Compare this week vs last week."""
        if not end_date:
            end_date = date.today()

        current_start = end_date - timedelta(days=7)
        previous_start = current_start - timedelta(days=7)

        return self.analyze_cost_changes(
            current_start=current_start,
            current_end=end_date,
            previous_start=previous_start,
            previous_end=current_start,
        )

    def analyze_from_stored_data(
        self,
        cost_records: list[dict],
        current_start: date,
        current_end: date,
        previous_start: date,
        previous_end: date,
    ) -> dict:
        """
        Same analysis but from already-stored database records instead
        of live AWS API calls. Useful for fast responses from cached data.
        """
        current_by_service = defaultdict(float)
        previous_by_service = defaultdict(float)

        for record in cost_records:
            record_date = (
                date.fromisoformat(record["date"])
                if isinstance(record["date"], str)
                else record["date"]
            )
            service = record["service"]
            amount = record["amount"]

            if current_start <= record_date < current_end:
                current_by_service[service] += amount
            elif previous_start <= record_date < previous_end:
                previous_by_service[service] += amount

        current_total = sum(current_by_service.values())
        previous_total = sum(previous_by_service.values())
        total_change = current_total - previous_total
        total_change_pct = (total_change / previous_total) if previous_total > 0 else 0

        all_services = set(current_by_service.keys()) | set(previous_by_service.keys())
        service_changes = []

        for service in all_services:
            curr = current_by_service.get(service, 0)
            prev = previous_by_service.get(service, 0)
            change = curr - prev

            if abs(change) < 0.01:
                continue

            change_pct = (change / prev) if prev > 0 else (1.0 if curr > 0 else 0)
            impact_pct = (change / total_change) if abs(total_change) > 0.01 else 0

            service_changes.append({
                "service": service,
                "current_amount": round(curr, 2),
                "previous_amount": round(prev, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 4),
                "impact_pct": round(abs(impact_pct), 4),
                "direction": "increase" if change > 0 else "decrease",
            })

        service_changes.sort(key=lambda x: abs(x["change"]), reverse=True)

        top_increases = [s for s in service_changes if s["direction"] == "increase"]
        top_decreases = [s for s in service_changes if s["direction"] == "decrease"]

        return {
            "current_period": {
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
                "total": round(current_total, 2),
            },
            "previous_period": {
                "start": previous_start.isoformat(),
                "end": previous_end.isoformat(),
                "total": round(previous_total, 2),
            },
            "total_change": round(total_change, 2),
            "total_change_pct": round(total_change_pct, 4),
            "direction": "increase" if total_change > 0 else ("decrease" if total_change < 0 else "unchanged"),
            "service_changes": service_changes,
            "top_increases": top_increases[:10],
            "top_decreases": top_decreases[:10],
            "new_services": [s for s in service_changes if s["previous_amount"] == 0 and s["current_amount"] > 0],
            "removed_services": [s for s in service_changes if s["current_amount"] == 0 and s["previous_amount"] > 0],
        }
