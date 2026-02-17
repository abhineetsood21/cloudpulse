"""
Commitment Analyzer — Savings Plans & Reserved Instances

Analyzes RI/SP utilization and recommends new commitments
based on steady-state usage patterns.

Usage:
    analyzer = CommitmentAnalyzer(session)
    ri_data = analyzer.get_ri_utilization()
    sp_data = analyzer.get_sp_utilization()
    recs = analyzer.get_commitment_recommendations()
"""

import logging
from datetime import date, timedelta

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CommitmentAnalyzer:
    """Analyzes Savings Plans and Reserved Instance utilization."""

    def __init__(self, session: boto3.Session):
        self.session = session

    def _get_ce_client(self):
        return self.session.client("ce", region_name="us-east-1")

    def get_ri_utilization(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get Reserved Instance utilization data.

        Returns:
        {
            "total_ri_cost": 1234.56,
            "used_ri_cost": 1100.00,
            "utilization_pct": 89.1,
            "unused_cost": 134.56,
            "by_service": [...]
        }
        """
        ce = self._get_ce_client()
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        try:
            response = ce.get_reservation_utilization(
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Granularity="MONTHLY",
            )
        except ClientError as e:
            logger.error(f"Failed to get RI utilization: {e}")
            return {"error": str(e)}

        totals = response.get("Total", {})
        utilization = totals.get("UtilizationPercentage", "0")
        total_cost = float(totals.get("TotalAmortizedFee", "0"))
        used_cost = float(totals.get("UtilizedAmortizedFee", "0"))

        by_service = []
        for group in response.get("UtilizationsByTime", []):
            for item in group.get("Groups", []):
                by_service.append({
                    "key": item.get("Key", ""),
                    "value": item.get("Value", ""),
                    "utilization_pct": float(item.get("Utilization", {}).get("UtilizationPercentage", "0")),
                })

        return {
            "total_ri_cost": round(total_cost, 2),
            "used_ri_cost": round(used_cost, 2),
            "utilization_pct": round(float(utilization), 1),
            "unused_cost": round(total_cost - used_cost, 2),
            "by_service": by_service,
        }

    def get_sp_utilization(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """
        Get Savings Plans utilization data.

        Returns:
        {
            "total_commitment": 500.00,
            "used_commitment": 450.00,
            "utilization_pct": 90.0,
            "unused_commitment": 50.00
        }
        """
        ce = self._get_ce_client()
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        try:
            response = ce.get_savings_plans_utilization(
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Granularity="MONTHLY",
            )
        except ClientError as e:
            logger.error(f"Failed to get SP utilization: {e}")
            return {"error": str(e)}

        totals = response.get("Total", {})
        utilization = totals.get("Utilization", {})
        total = float(utilization.get("TotalCommitment", "0"))
        used = float(utilization.get("UsedCommitment", "0"))
        pct = float(utilization.get("UtilizationPercentage", "0"))

        return {
            "total_commitment": round(total, 2),
            "used_commitment": round(used, 2),
            "utilization_pct": round(pct, 1),
            "unused_commitment": round(total - used, 2),
        }

    def get_commitment_recommendations(self) -> list[dict]:
        """
        Generate recommendations for new RI/SP commitments based on
        steady-state on-demand usage over the past 30 days.

        Returns list of recommendations with estimated savings.
        """
        ce = self._get_ce_client()
        recommendations = []

        # Get RI purchase recommendations
        for service in ["Amazon Elastic Compute Cloud - Compute", "Amazon Relational Database Service"]:
            try:
                response = ce.get_reservation_purchase_recommendation(
                    Service=service,
                    TermInYears="ONE_YEAR",
                    PaymentOption="NO_UPFRONT",
                    LookbackPeriodInDays="THIRTY_DAYS",
                )

                for rec in response.get("Recommendations", []):
                    for detail in rec.get("RecommendationDetails", []):
                        estimated_savings = float(
                            detail.get("EstimatedMonthlySavingsAmount", "0")
                        )
                        if estimated_savings < 5:
                            continue

                        recommendations.append({
                            "type": "reserved_instance",
                            "service": service,
                            "instance_type": detail.get("InstanceDetails", {}).get(
                                "EC2InstanceDetails", {}
                            ).get("InstanceType", "N/A"),
                            "term": "1 year",
                            "payment_option": "No Upfront",
                            "estimated_monthly_savings": round(estimated_savings, 2),
                            "estimated_monthly_cost": round(
                                float(detail.get("EstimatedMonthlyOnDemandCost", "0")), 2
                            ),
                            "recommendation": (
                                f"Purchase RI for {service}: "
                                f"save ~${estimated_savings:.0f}/mo"
                            ),
                        })
            except ClientError as e:
                logger.warning(f"RI recommendation failed for {service}: {e}")

        # Get Savings Plans recommendations
        try:
            response = ce.get_savings_plans_purchase_recommendation(
                SavingsPlansType="COMPUTE_SP",
                TermInYears="ONE_YEAR",
                PaymentOption="NO_UPFRONT",
                LookbackPeriodInDays="THIRTY_DAYS",
            )

            for rec in response.get("SavingsPlansPurchaseRecommendation", {}).get(
                "SavingsPlansPurchaseRecommendationDetails", []
            ):
                estimated_savings = float(
                    rec.get("EstimatedMonthlySavingsAmount", "0")
                )
                if estimated_savings < 5:
                    continue

                recommendations.append({
                    "type": "savings_plan",
                    "service": "Compute",
                    "instance_type": "N/A",
                    "term": "1 year",
                    "payment_option": "No Upfront",
                    "hourly_commitment": round(
                        float(rec.get("HourlyCommitmentToPurchase", "0")), 4
                    ),
                    "estimated_monthly_savings": round(estimated_savings, 2),
                    "recommendation": (
                        f"Purchase Compute Savings Plan: "
                        f"save ~${estimated_savings:.0f}/mo"
                    ),
                })
        except ClientError as e:
            logger.warning(f"SP recommendation failed: {e}")

        recommendations.sort(
            key=lambda r: r["estimated_monthly_savings"], reverse=True
        )
        return recommendations
