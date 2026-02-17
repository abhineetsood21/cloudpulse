"""
Connector Factory

Maps every provider key to its connector class and provides
a single entry point: get_connector(provider_key, config).
"""

from typing import Any

from app.services.connectors.base import BaseConnector

# Cloud
from app.services.connectors.cloud_connectors import (
    AWSConnector, GCPConnector, AzureConnector, KubernetesConnector,
)
# API-key based (15 providers)
from app.services.connectors.api_key_connectors import (
    DatadogConnector, MongoDBConnector, ConfluentConnector, FastlyConnector,
    NewRelicConnector, CoralogixConnector, LinodeConnector, OpenAIConnector,
    AnthropicConnector, GrafanaCloudConnector, ClickHouseConnector,
    AnyscaleConnector, TemporalCloudConnector, TwilioConnector, CursorConnector,
)
# Database
from app.services.connectors.db_connectors import (
    SnowflakeConnector, DatabricksConnector,
)
# OAuth / Token
from app.services.connectors.oauth_connectors import (
    GitHubConnector, PlanetScaleConnector,
)
# Oracle
from app.services.connectors.oracle_connector import OracleConnector
# Custom + Stubs
from app.services.connectors.custom_connector import (
    CustomConnector, CloudflareConnector, VercelConnector,
)


# ── Registry ──────────────────────────────────────────────────────

CONNECTOR_MAP: dict[str, type[BaseConnector]] = {
    # Cloud
    "aws": AWSConnector,
    "azure": AzureConnector,
    "gcp": GCPConnector,
    "kubernetes": KubernetesConnector,
    "oracle": OracleConnector,
    "linode": LinodeConnector,
    # Observability
    "datadog": DatadogConnector,
    "new_relic": NewRelicConnector,
    "coralogix": CoralogixConnector,
    "grafana_cloud": GrafanaCloudConnector,
    # Database
    "mongodb": MongoDBConnector,
    "snowflake": SnowflakeConnector,
    "databricks": DatabricksConnector,
    "planetscale": PlanetScaleConnector,
    "clickhouse": ClickHouseConnector,
    # AI / ML
    "openai": OpenAIConnector,
    "anthropic": AnthropicConnector,
    "anyscale": AnyscaleConnector,
    "cursor": CursorConnector,
    # DevTools
    "github": GitHubConnector,
    "temporal_cloud": TemporalCloudConnector,
    "twilio": TwilioConnector,
    # CDN / Streaming
    "fastly": FastlyConnector,
    "confluent": ConfluentConnector,
    "cloudflare": CloudflareConnector,
    "vercel": VercelConnector,
    # Custom
    "custom": CustomConnector,
}


def get_connector(provider_key: str, config: dict[str, Any]) -> BaseConnector:
    """
    Factory: instantiate the correct connector for a provider.

    Args:
        provider_key: One of the keys in CONNECTOR_MAP (e.g. "datadog").
        config: Provider-specific credentials / connection config.

    Raises:
        ValueError: If the provider key is unknown.
    """
    cls = CONNECTOR_MAP.get(provider_key)
    if cls is None:
        raise ValueError(
            f"Unknown provider: {provider_key}. "
            f"Available: {', '.join(sorted(CONNECTOR_MAP.keys()))}"
        )
    return cls(config)
