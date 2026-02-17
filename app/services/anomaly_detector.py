"""
Anomaly Detection Service

Detects unusual cost spikes by comparing daily spend against a rolling
average. Uses a simple statistical approach (percentage deviation).
"""

import logging
from collections import defaultdict
from datetime import date, timedelta

from app.core.config import get_settings
from app.models.models import AnomalySeverity

logger = logging.getLogger(__name__)
settings = get_settings()


class AnomalyDetector:
    """Detects cost anomalies based on rolling average deviation."""

    def __init__(
        self,
        info_threshold: float | None = None,
        warning_threshold: float | None = None,
        critical_threshold: float | None = None,
        lookback_days: int = 7,
        min_amount: float = 1.00,
    ):
        self.info_threshold = info_threshold or settings.anomaly_threshold_info
        self.warning_threshold = warning_threshold or settings.anomaly_threshold_warning
        self.critical_threshold = critical_threshold or settings.anomaly_threshold_critical
        self.lookback_days = lookback_days
        self.min_amount = min_amount  # Ignore services costing less than this

    def classify_severity(self, deviation_pct: float) -> AnomalySeverity | None:
        """
        Classify anomaly severity based on deviation percentage.

        Returns None if the deviation doesn't meet any threshold.
        """
        if deviation_pct >= self.critical_threshold:
            return AnomalySeverity.CRITICAL
        elif deviation_pct >= self.warning_threshold:
            return AnomalySeverity.WARNING
        elif deviation_pct >= self.info_threshold:
            return AnomalySeverity.INFO
        return None

    def detect(self, cost_records: list[dict], target_date: date | None = None) -> list[dict]:
        """
        Detect anomalies in cost data.

        Args:
            cost_records: List of dicts with keys: date, service, amount
                          Should include enough history for the lookback window.
            target_date: The date to check for anomalies. Defaults to yesterday.

        Returns:
            List of anomaly dicts:
            [
                {
                    "date": "2026-02-15",
                    "service": "Amazon EC2",
                    "expected_amount": 10.00,
                    "actual_amount": 25.00,
                    "deviation_pct": 1.50,
                    "severity": "critical"
                },
                ...
            ]
        """
        if not target_date:
            target_date = date.today() - timedelta(days=1)

        lookback_start = target_date - timedelta(days=self.lookback_days)

        # Group costs by service and date
        service_daily_costs = defaultdict(lambda: defaultdict(float))
        for record in cost_records:
            record_date = (
                date.fromisoformat(record["date"])
                if isinstance(record["date"], str)
                else record["date"]
            )
            service_daily_costs[record["service"]][record_date] += record["amount"]

        anomalies = []

        for service, daily_costs in service_daily_costs.items():
            # Get the target day's cost
            target_amount = daily_costs.get(target_date, 0)

            # Skip low-cost services (noise)
            if target_amount < self.min_amount:
                continue

            # Calculate rolling average (excluding target date)
            lookback_amounts = []
            for day_offset in range(1, self.lookback_days + 1):
                check_date = target_date - timedelta(days=day_offset)
                if check_date in daily_costs:
                    lookback_amounts.append(daily_costs[check_date])

            # Need at least 3 days of history to detect anomalies
            if len(lookback_amounts) < 3:
                continue

            average = sum(lookback_amounts) / len(lookback_amounts)

            # Avoid division by zero
            if average < 0.01:
                continue

            deviation_pct = (target_amount - average) / average
            severity = self.classify_severity(deviation_pct)

            if severity:
                anomalies.append({
                    "date": target_date.isoformat(),
                    "service": service,
                    "expected_amount": round(average, 2),
                    "actual_amount": round(target_amount, 2),
                    "deviation_pct": round(deviation_pct, 4),
                    "severity": severity.value,
                })

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        anomalies.sort(key=lambda x: severity_order.get(x["severity"], 99))

        logger.info(
            f"Detected {len(anomalies)} anomalies for {target_date}"
        )
        return anomalies
