"""
AWS Cost Explorer Service

Handles cross-account access via STS AssumeRole and fetches cost data
from the AWS Cost Explorer API.
"""

import logging
from datetime import date, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CostExplorerService:
    """Fetches AWS cost data via cross-account role assumption."""

    def __init__(self, role_arn: str, external_id: str, region: str = "us-east-1"):
        self.role_arn = role_arn
        self.external_id = external_id
        self.region = region
        self._session = None

    def _get_session(self) -> boto3.Session:
        """Assume the customer's IAM role and return a boto3 session."""
        if self._session:
            return self._session

        sts_client = boto3.client(
            "sts",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=self.region,
        )

        try:
            response = sts_client.assume_role(
                RoleArn=self.role_arn,
                RoleSessionName="cloudpulse-cost-reader",
                ExternalId=self.external_id,
                DurationSeconds=3600,
            )
        except ClientError as e:
            logger.error(f"Failed to assume role {self.role_arn}: {e}")
            raise

        credentials = response["Credentials"]
        self._session = boto3.Session(
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            region_name=self.region,
        )
        return self._session

    def validate_access(self) -> bool:
        """Test that we can assume the role and access Cost Explorer."""
        try:
            session = self._get_session()
            ce_client = session.client("ce", region_name="us-east-1")
            # Make a minimal API call to verify access
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
            logger.error(f"Access validation failed for {self.role_arn}: {e}")
            return False

    def get_cost_by_service(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "DAILY",
    ) -> list[dict]:
        """
        Fetch cost data grouped by AWS service.

        Returns a list of dicts:
        [
            {
                "date": "2026-02-15",
                "service": "Amazon Elastic Compute Cloud - Compute",
                "amount": 12.34,
                "currency": "USD"
            },
            ...
        ]
        """
        session = self._get_session()
        ce_client = session.client("ce", region_name="us-east-1")

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

                    # Skip negligible amounts
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

        logger.info(
            f"Fetched {len(results)} cost records for {self.role_arn} "
            f"from {start_date} to {end_date}"
        )
        return results

    def get_total_cost(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "DAILY",
    ) -> list[dict]:
        """
        Fetch total cost (not grouped by service).

        Returns:
        [
            {"date": "2026-02-15", "amount": 45.67, "currency": "USD"},
            ...
        ]
        """
        session = self._get_session()
        ce_client = session.client("ce", region_name="us-east-1")

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

    def get_cost_forecast(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> dict:
        """
        Get AWS cost forecast for the upcoming period.

        Returns:
        {"total_forecast": 1234.56, "currency": "USD", "start": "...", "end": "..."}
        """
        session = self._get_session()
        ce_client = session.client("ce", region_name="us-east-1")

        if not start_date:
            start_date = date.today() + timedelta(days=1)
        if not end_date:
            # Forecast to end of current month
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
        except ClientError as e:
            logger.error(f"Failed to get cost forecast: {e}")
            raise

        total = response.get("Total", {})
        return {
            "total_forecast": round(float(total.get("Amount", 0)), 2),
            "currency": total.get("Unit", "USD"),
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }
