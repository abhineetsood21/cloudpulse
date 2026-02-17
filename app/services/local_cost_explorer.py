"""
Local Cost Explorer Service

Uses the default AWS credentials (from ~/.aws/credentials) instead of
cross-account STS AssumeRole. Intended for local development and
connecting your own AWS account.
"""

import logging
from datetime import date, timedelta
from typing import Optional
from calendar import monthrange

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class LocalCostExplorerService:
    """Fetches AWS cost data using local/default credentials."""

    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.session = boto3.Session(region_name=region)

    def validate_access(self) -> bool:
        """Test that we can access Cost Explorer."""
        try:
            ce_client = self.session.client("ce", region_name="us-east-1")
            today = date.today()
            ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": (today - timedelta(days=1)).isoformat(),
                    "End": today.isoformat(),
                },
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )
            return True
        except ClientError as e:
            logger.error(f"Access validation failed: {e}")
            return False

    def get_cost_by_service(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "DAILY",
    ) -> list[dict]:
        """Fetch cost data grouped by AWS service."""
        ce_client = self.session.client("ce", region_name="us-east-1")

        results = []
        next_token = None

        while True:
            kwargs = {
                "TimePeriod": {
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                "Granularity": granularity,
                "Metrics": ["UnblendedCost"],
                "GroupBy": [
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                ],
            }
            if next_token:
                kwargs["NextPageToken"] = next_token

            try:
                response = ce_client.get_cost_and_usage(**kwargs)
            except ClientError as e:
                logger.error(f"Failed to fetch cost data: {e}")
                raise

            for result_by_time in response.get("ResultsByTime", []):
                period_start = result_by_time["TimePeriod"]["Start"]
                for group in result_by_time.get("Groups", []):
                    service_name = group["Keys"][0]
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    currency = group["Metrics"]["UnblendedCost"]["Unit"]

                    if amount < 0.01:
                        continue

                    results.append({
                        "date": period_start,
                        "service": service_name,
                        "amount": round(amount, 4),
                        "currency": currency,
                    })

            next_token = response.get("NextPageToken")
            if not next_token:
                break

        logger.info(f"Fetched {len(results)} cost records from {start_date} to {end_date}")
        return results

    def get_cost_by_tag(
        self,
        start_date: date,
        end_date: date,
        tag_key: str = "Environment",
    ) -> list[dict]:
        """Fetch cost data grouped by a specific tag."""
        ce_client = self.session.client("ce", region_name="us-east-1")

        results = []
        next_token = None

        while True:
            kwargs = {
                "TimePeriod": {
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                "Granularity": "MONTHLY",
                "Metrics": ["UnblendedCost"],
                "GroupBy": [
                    {"Type": "TAG", "Key": tag_key},
                ],
            }
            if next_token:
                kwargs["NextPageToken"] = next_token

            try:
                response = ce_client.get_cost_and_usage(**kwargs)
            except ClientError as e:
                logger.error(f"Failed to fetch tag cost data: {e}")
                raise

            for result_by_time in response.get("ResultsByTime", []):
                period_start = result_by_time["TimePeriod"]["Start"]
                for group in result_by_time.get("Groups", []):
                    tag_value = group["Keys"][0]
                    # Format: "Environment$production" or "Environment$"
                    tag_value = tag_value.split("$", 1)[1] if "$" in tag_value else tag_value
                    if not tag_value:
                        tag_value = "(untagged)"
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    if amount < 0.01:
                        continue
                    results.append({
                        "date": period_start,
                        "tag_key": tag_key,
                        "tag_value": tag_value,
                        "amount": round(amount, 4),
                    })

            next_token = response.get("NextPageToken")
            if not next_token:
                break

        return results

    def get_available_tags(self, start_date: date, end_date: date) -> list[str]:
        """List all tag keys that have cost data."""
        ce_client = self.session.client("ce", region_name="us-east-1")
        try:
            response = ce_client.get_tags(
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
            )
            return response.get("Tags", [])
        except ClientError as e:
            logger.error(f"Failed to fetch tags: {e}")
            return []

    def get_cost_forecast(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """Get AWS cost forecast using local credentials."""
        ce_client = self.session.client("ce", region_name="us-east-1")

        if not start_date:
            start_date = date.today() + timedelta(days=1)
        if not end_date:
            if start_date.month == 12:
                end_date = date(start_date.year + 1, 1, 1)
            else:
                end_date = date(start_date.year, start_date.month + 1, 1)

        try:
            response = ce_client.get_cost_forecast(
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
            )
            total = response.get("Total", {})
            return {
                "total_forecast": round(float(total.get("Amount", 0)), 2),
                "currency": total.get("Unit", "USD"),
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            }
        except ClientError as e:
            logger.warning(f"AWS forecast API failed: {e}. Falling back to linear projection.")
            return None

    def get_total_cost(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "DAILY",
    ) -> list[dict]:
        """Fetch total cost (not grouped by service)."""
        ce_client = self.session.client("ce", region_name="us-east-1")

        try:
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Granularity=granularity,
                Metrics=["UnblendedCost"],
            )
        except ClientError as e:
            logger.error(f"Failed to fetch total cost: {e}")
            raise

        results = []
        for result_by_time in response.get("ResultsByTime", []):
            period_start = result_by_time["TimePeriod"]["Start"]
            total = result_by_time.get("Total", {})
            cost_info = total.get("UnblendedCost", {})
            amount = float(cost_info.get("Amount", 0))
            currency = cost_info.get("Unit", "USD")
            results.append({
                "date": period_start,
                "amount": round(amount, 4),
                "currency": currency,
            })

        return results
