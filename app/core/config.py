from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me-in-production"
    app_url: str = "http://localhost:8000"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/cloudpulse"

    # AWS
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    cloudpulse_external_id: str = "cloudpulse-default-external-id"

    # SendGrid
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "alerts@cloudpulse.io"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # JWT Auth
    jwt_secret_key: str = "change-me-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # Anomaly Detection Thresholds
    anomaly_threshold_info: float = 0.25
    anomaly_threshold_warning: float = 0.50
    anomaly_threshold_critical: float = 1.00

    # DuckDB Analytics
    duckdb_path: str = "data/cloudpulse.duckdb"
    billing_data_dir: str = "data/billing"

    # CUR Ingestion
    cur_s3_bucket: str = ""
    cur_s3_prefix: str = "cur/"
    cur_report_name: str = ""

    # GCP
    gcp_service_account_json: str = ""
    gcp_billing_dataset: str = ""  # e.g. "project.dataset.table"

    # Azure
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""
    azure_storage_account: str = ""
    azure_cost_export_container: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
