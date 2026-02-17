"""
Cloud Connectors — AWS, GCP, Azure, Kubernetes

Wrap the existing ingestor/connector services into the BaseConnector
interface so they work through the unified connector factory.
"""

import logging
from datetime import date
from typing import Any

from app.services.connectors.base import (
    BaseConnector, FocusRecord, IngestResult, ValidationResult,
)

logger = logging.getLogger(__name__)


class AWSConnector(BaseConnector):
    """Wraps the existing CUR ingestor."""
    provider_key = "aws"

    def validate(self) -> ValidationResult:
        try:
            import boto3
            sts = boto3.client("sts")
            creds = sts.assume_role(
                RoleArn=self.config["role_arn"],
                RoleSessionName="CloudPulseValidation",
                ExternalId=self.config.get("external_id", ""),
            )
            account_id = creds["AssumedRoleUser"]["Arn"].split(":")[4]
            return ValidationResult(valid=True, account_identifier=account_id)
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        # Delegates to CUR ingestor which handles S3 download
        return []

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        """Override to use existing CUR ingestor pipeline."""
        try:
            from app.services.cur_ingestor import CURIngestor
            ingestor = CURIngestor(
                role_arn=self.config.get("role_arn"),
                external_id=self.config.get("external_id"),
                bucket=self.config.get("cur_bucket"),
                prefix=self.config.get("cur_prefix"),
                report_name=self.config.get("cur_report_name"),
            )
            result = ingestor.ingest()
            return IngestResult(
                status="success",
                rows_ingested=result.get("total_rows", 0),
                message=f"Ingested AWS CUR data.",
            )
        except Exception as e:
            return IngestResult(status="error", message=str(e))


class GCPConnector(BaseConnector):
    """Wraps the existing GCP billing connector."""
    provider_key = "gcp"

    def validate(self) -> ValidationResult:
        try:
            from google.oauth2 import service_account
            import json
            creds_info = json.loads(self.config["service_account_json"])
            creds = service_account.Credentials.from_service_account_info(creds_info)
            return ValidationResult(valid=True, account_identifier=creds_info.get("project_id"))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        return []

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        try:
            from app.services.gcp_connector import GCPBillingConnector
            connector = GCPBillingConnector(
                service_account_json=self.config.get("service_account_json"),
                billing_dataset=self.config.get("billing_dataset"),
            )
            result = connector.ingest(start_date=start_date.isoformat(), end_date=end_date.isoformat())
            return IngestResult(
                status="success",
                rows_ingested=result.get("rows_ingested", 0),
                message="Ingested GCP billing data.",
            )
        except Exception as e:
            return IngestResult(status="error", message=str(e))


class AzureConnector(BaseConnector):
    """Wraps the existing Azure cost connector."""
    provider_key = "azure"

    def validate(self) -> ValidationResult:
        try:
            from azure.identity import ClientSecretCredential
            credential = ClientSecretCredential(
                tenant_id=self.config["tenant_id"],
                client_id=self.config["client_id"],
                client_secret=self.config["client_secret"],
            )
            token = credential.get_token("https://management.azure.com/.default")
            return ValidationResult(valid=bool(token.token))
        except Exception as e:
            return ValidationResult(valid=False, error=str(e))

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        return []

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        try:
            from app.services.azure_connector import AzureCostConnector
            connector = AzureCostConnector(
                client_id=self.config.get("client_id"),
                client_secret=self.config.get("client_secret"),
                tenant_id=self.config.get("tenant_id"),
                storage_account=self.config.get("storage_account"),
                container=self.config.get("container"),
            )
            result = connector.ingest(start_date=start_date.isoformat(), end_date=end_date.isoformat())
            return IngestResult(
                status="success",
                rows_ingested=result.get("rows_ingested", 0),
                message="Ingested Azure billing data.",
            )
        except Exception as e:
            return IngestResult(status="error", message=str(e))


class KubernetesConnector(BaseConnector):
    """Kubernetes cost connector — works with the CloudPulse agent."""
    provider_key = "kubernetes"

    def validate(self) -> ValidationResult:
        # Agent-based: validation is just checking the token is non-empty
        if self.config.get("cluster_name") and self.config.get("agent_token"):
            return ValidationResult(valid=True, account_identifier=self.config["cluster_name"])
        return ValidationResult(valid=False, error="cluster_name and agent_token are required.")

    def fetch_costs(self, start_date: date, end_date: date) -> list[dict]:
        return []

    def normalize(self, raw: list[dict]) -> list[FocusRecord]:
        return []

    def ingest(self, start_date: date, end_date: date, output_dir: str | None = None) -> IngestResult:
        # Kubernetes costs are pushed by the agent, not pulled
        return IngestResult(
            status="success",
            rows_ingested=0,
            message="Kubernetes costs are ingested via the CloudPulse agent. Deploy with Helm.",
        )
