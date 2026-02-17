"""
Provider Registry — Single Source of Truth for All Integrations

Defines the complete catalog of supported cost providers.  Each entry
drives:
  • Backend validation logic (required_fields → connector)
  • Frontend form rendering (field defs → dynamic inputs)
  • Catalog API response (display metadata)
"""

PROVIDER_CATALOG: dict[str, dict] = {
    # ─── Cloud ────────────────────────────────────────────────────
    "aws": {
        "display_name": "AWS",
        "category": "cloud",
        "auth_type": "iam_role",
        "auth_type_label": "Cross Account IAM Role",
        "status": "active",
        "color": "#FF9900",
        "docs_url": "https://docs.aws.amazon.com/cur/latest/userguide/what-is-cur.html",
        "required_fields": [
            {"name": "role_arn", "label": "Role ARN", "input_type": "text", "placeholder": "arn:aws:iam::123456789012:role/CloudPulseCostReader", "help_text": "IAM role ARN created by the CloudFormation template.", "secret": False},
            {"name": "external_id", "label": "External ID", "input_type": "text", "placeholder": "Auto-generated", "help_text": "External ID for STS AssumeRole.", "secret": False},
            {"name": "cur_bucket", "label": "CUR S3 Bucket", "input_type": "text", "placeholder": "my-cur-bucket", "help_text": "S3 bucket containing Cost and Usage Reports (optional).", "secret": False},
            {"name": "cur_prefix", "label": "CUR S3 Prefix", "input_type": "text", "placeholder": "reports/", "help_text": "Prefix path inside the CUR bucket.", "secret": False},
        ],
    },
    "azure": {
        "display_name": "Azure",
        "category": "cloud",
        "auth_type": "service_principal",
        "auth_type_label": "Service Principal",
        "status": "active",
        "color": "#0078D4",
        "docs_url": "https://learn.microsoft.com/en-us/azure/cost-management-billing/",
        "required_fields": [
            {"name": "tenant_id", "label": "Tenant ID", "input_type": "text", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "help_text": "Azure AD tenant ID.", "secret": False},
            {"name": "client_id", "label": "Client ID", "input_type": "text", "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "help_text": "App registration client ID.", "secret": False},
            {"name": "client_secret", "label": "Client Secret", "input_type": "password", "placeholder": "", "help_text": "App registration client secret.", "secret": True},
            {"name": "storage_account", "label": "Storage Account", "input_type": "text", "placeholder": "billingexports", "help_text": "Storage account for billing exports.", "secret": False},
            {"name": "container", "label": "Container", "input_type": "text", "placeholder": "exports", "help_text": "Blob container with cost export data.", "secret": False},
        ],
    },
    "gcp": {
        "display_name": "Google Cloud",
        "category": "cloud",
        "auth_type": "billing_export",
        "auth_type_label": "Cloud Billing Export",
        "status": "active",
        "color": "#4285F4",
        "docs_url": "https://cloud.google.com/billing/docs/how-to/export-data-bigquery",
        "required_fields": [
            {"name": "service_account_json", "label": "Service Account Key (JSON)", "input_type": "textarea", "placeholder": '{"type": "service_account", ...}', "help_text": "Paste the full JSON key for a service account with BigQuery read access.", "secret": True},
            {"name": "billing_dataset", "label": "Billing Dataset", "input_type": "text", "placeholder": "project.dataset.gcp_billing_export_v1_XXXXXX", "help_text": "Fully-qualified BigQuery table for billing export.", "secret": False},
        ],
    },
    "oracle": {
        "display_name": "Oracle Cloud",
        "category": "cloud",
        "auth_type": "iam_user",
        "auth_type_label": "IAM User",
        "status": "active",
        "color": "#F80000",
        "docs_url": "https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/billingoverview.htm",
        "required_fields": [
            {"name": "tenancy_ocid", "label": "Tenancy OCID", "input_type": "text", "placeholder": "ocid1.tenancy.oc1...", "help_text": "OCI tenancy identifier.", "secret": False},
            {"name": "user_ocid", "label": "User OCID", "input_type": "text", "placeholder": "ocid1.user.oc1...", "help_text": "OCI user identifier.", "secret": False},
            {"name": "fingerprint", "label": "API Key Fingerprint", "input_type": "text", "placeholder": "aa:bb:cc:...", "help_text": "Fingerprint of the uploaded API signing key.", "secret": False},
            {"name": "private_key", "label": "Private Key (PEM)", "input_type": "textarea", "placeholder": "-----BEGIN RSA PRIVATE KEY-----", "help_text": "PEM-encoded private key for API signing.", "secret": True},
            {"name": "region", "label": "Region", "input_type": "text", "placeholder": "us-ashburn-1", "help_text": "OCI home region.", "secret": False},
        ],
    },
    "linode": {
        "display_name": "Linode by Akamai",
        "category": "cloud",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#00A95C",
        "docs_url": "https://www.linode.com/docs/api/account/",
        "required_fields": [
            {"name": "api_key", "label": "Personal Access Token", "input_type": "password", "placeholder": "", "help_text": "Linode API token with account:read_only scope.", "secret": True},
        ],
    },

    # ─── Kubernetes ───────────────────────────────────────────────
    "kubernetes": {
        "display_name": "Kubernetes",
        "category": "kubernetes",
        "auth_type": "agent",
        "auth_type_label": "CloudPulse Agent",
        "status": "active",
        "color": "#326CE5",
        "docs_url": "https://kubernetes.io/docs/concepts/overview/",
        "required_fields": [
            {"name": "cluster_name", "label": "Cluster Name", "input_type": "text", "placeholder": "production-us-east", "help_text": "Human-readable cluster identifier.", "secret": False},
            {"name": "agent_token", "label": "Agent Token", "input_type": "password", "placeholder": "Auto-generated on save", "help_text": "Token the Helm-deployed agent uses to push metrics.", "secret": True},
        ],
    },

    # ─── Observability ────────────────────────────────────────────
    "datadog": {
        "display_name": "Datadog",
        "category": "observability",
        "auth_type": "api_key",
        "auth_type_label": "API Key + App Key",
        "status": "active",
        "color": "#632CA6",
        "docs_url": "https://docs.datadoghq.com/api/latest/usage-metering/",
        "required_fields": [
            {"name": "api_key", "label": "API Key", "input_type": "password", "placeholder": "", "help_text": "Datadog API key.", "secret": True},
            {"name": "app_key", "label": "Application Key", "input_type": "password", "placeholder": "", "help_text": "Datadog Application key with usage_read scope.", "secret": True},
            {"name": "site", "label": "Datadog Site", "input_type": "text", "placeholder": "datadoghq.com", "help_text": "e.g. datadoghq.com, datadoghq.eu, us5.datadoghq.com", "secret": False},
        ],
    },
    "new_relic": {
        "display_name": "New Relic",
        "category": "observability",
        "auth_type": "api_key",
        "auth_type_label": "User API Key",
        "status": "active",
        "color": "#008C99",
        "docs_url": "https://docs.newrelic.com/docs/apis/nerdgraph/get-started/introduction-new-relic-nerdgraph/",
        "required_fields": [
            {"name": "api_key", "label": "User API Key", "input_type": "password", "placeholder": "NRAK-...", "help_text": "New Relic User API key for NerdGraph.", "secret": True},
            {"name": "account_id", "label": "Account ID", "input_type": "text", "placeholder": "1234567", "help_text": "Numeric New Relic account ID.", "secret": False},
        ],
    },
    "coralogix": {
        "display_name": "Coralogix",
        "category": "observability",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#FC5108",
        "docs_url": "https://coralogix.com/docs/billing-api/",
        "required_fields": [
            {"name": "api_key", "label": "API Key", "input_type": "password", "placeholder": "", "help_text": "Coralogix Logs/Data API key.", "secret": True},
            {"name": "domain", "label": "Cluster Domain", "input_type": "text", "placeholder": "coralogix.com", "help_text": "e.g. coralogix.com, eu2.coralogix.com, coralogix.in", "secret": False},
        ],
    },
    "grafana_cloud": {
        "display_name": "Grafana Cloud",
        "category": "observability",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#F46800",
        "docs_url": "https://grafana.com/docs/grafana-cloud/cost-management-and-billing/",
        "required_fields": [
            {"name": "api_key", "label": "Cloud Access Policy Token", "input_type": "password", "placeholder": "glc_...", "help_text": "Grafana Cloud access policy token with billing:read.", "secret": True},
            {"name": "org_slug", "label": "Organization Slug", "input_type": "text", "placeholder": "myorg", "help_text": "Grafana Cloud organization slug.", "secret": False},
        ],
    },

    # ─── Database ─────────────────────────────────────────────────
    "mongodb": {
        "display_name": "MongoDB Atlas",
        "category": "database",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#00ED64",
        "docs_url": "https://www.mongodb.com/docs/atlas/reference/api-resources-spec/v2/",
        "required_fields": [
            {"name": "public_key", "label": "Public Key", "input_type": "text", "placeholder": "", "help_text": "MongoDB Atlas API public key.", "secret": False},
            {"name": "private_key", "label": "Private Key", "input_type": "password", "placeholder": "", "help_text": "MongoDB Atlas API private key.", "secret": True},
            {"name": "org_id", "label": "Organization ID", "input_type": "text", "placeholder": "", "help_text": "Atlas organization identifier.", "secret": False},
        ],
    },
    "snowflake": {
        "display_name": "Snowflake",
        "category": "database",
        "auth_type": "db_user",
        "auth_type_label": "Snowflake User",
        "status": "active",
        "color": "#29B5E8",
        "docs_url": "https://docs.snowflake.com/en/sql-reference/account-usage",
        "required_fields": [
            {"name": "account", "label": "Account Identifier", "input_type": "text", "placeholder": "xy12345.us-east-1", "help_text": "Snowflake account identifier.", "secret": False},
            {"name": "username", "label": "Username", "input_type": "text", "placeholder": "", "help_text": "Snowflake user with ACCOUNT_USAGE access.", "secret": False},
            {"name": "password", "label": "Password", "input_type": "password", "placeholder": "", "help_text": "Snowflake user password.", "secret": True},
            {"name": "warehouse", "label": "Warehouse", "input_type": "text", "placeholder": "COMPUTE_WH", "help_text": "Warehouse to use for queries.", "secret": False},
        ],
    },
    "databricks": {
        "display_name": "Databricks",
        "category": "database",
        "auth_type": "api_key",
        "auth_type_label": "Personal Access Token",
        "status": "active",
        "color": "#FF3621",
        "docs_url": "https://docs.databricks.com/en/admin/system-tables/billing.html",
        "required_fields": [
            {"name": "workspace_url", "label": "Workspace URL", "input_type": "text", "placeholder": "https://adb-1234567890.12.azuredatabricks.net", "help_text": "Databricks workspace URL.", "secret": False},
            {"name": "access_token", "label": "Personal Access Token", "input_type": "password", "placeholder": "dapi...", "help_text": "PAT with access to system.billing tables.", "secret": True},
        ],
    },
    "planetscale": {
        "display_name": "PlanetScale",
        "category": "database",
        "auth_type": "oauth",
        "auth_type_label": "OAuth",
        "status": "active",
        "color": "#000000",
        "docs_url": "https://api-docs.planetscale.com/",
        "required_fields": [
            {"name": "service_token_id", "label": "Service Token ID", "input_type": "text", "placeholder": "", "help_text": "PlanetScale service token ID.", "secret": False},
            {"name": "service_token", "label": "Service Token", "input_type": "password", "placeholder": "", "help_text": "PlanetScale service token secret.", "secret": True},
            {"name": "organization", "label": "Organization", "input_type": "text", "placeholder": "", "help_text": "PlanetScale organization name.", "secret": False},
        ],
    },
    "clickhouse": {
        "display_name": "ClickHouse Cloud",
        "category": "database",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#FFCC21",
        "docs_url": "https://clickhouse.com/docs/en/cloud/manage/api/api-overview",
        "required_fields": [
            {"name": "api_key_id", "label": "API Key ID", "input_type": "text", "placeholder": "", "help_text": "ClickHouse Cloud API key ID.", "secret": False},
            {"name": "api_key_secret", "label": "API Key Secret", "input_type": "password", "placeholder": "", "help_text": "ClickHouse Cloud API key secret.", "secret": True},
            {"name": "org_id", "label": "Organization ID", "input_type": "text", "placeholder": "", "help_text": "ClickHouse Cloud organization ID.", "secret": False},
        ],
    },

    # ─── AI / ML ──────────────────────────────────────────────────
    "openai": {
        "display_name": "OpenAI",
        "category": "ai_ml",
        "auth_type": "api_key",
        "auth_type_label": "Admin API Key",
        "status": "active",
        "color": "#412991",
        "docs_url": "https://platform.openai.com/docs/api-reference/usage",
        "required_fields": [
            {"name": "api_key", "label": "Admin API Key", "input_type": "password", "placeholder": "sk-admin-...", "help_text": "OpenAI admin key with usage/billing read access.", "secret": True},
            {"name": "org_id", "label": "Organization ID", "input_type": "text", "placeholder": "org-...", "help_text": "OpenAI organization ID (optional).", "secret": False},
        ],
    },
    "anthropic": {
        "display_name": "Anthropic",
        "category": "ai_ml",
        "auth_type": "api_key",
        "auth_type_label": "Admin API Key",
        "status": "active",
        "color": "#D4A574",
        "docs_url": "https://docs.anthropic.com/en/api/admin-api",
        "required_fields": [
            {"name": "api_key", "label": "Admin API Key", "input_type": "password", "placeholder": "sk-ant-admin-...", "help_text": "Anthropic admin API key with billing read access.", "secret": True},
        ],
    },
    "anyscale": {
        "display_name": "Anyscale",
        "category": "ai_ml",
        "auth_type": "api_key",
        "auth_type_label": "Platform API Key",
        "status": "active",
        "color": "#1B65F0",
        "docs_url": "https://docs.anyscale.com/reference/",
        "required_fields": [
            {"name": "api_key", "label": "API Key", "input_type": "password", "placeholder": "", "help_text": "Anyscale platform API key.", "secret": True},
        ],
    },
    "cursor": {
        "display_name": "Cursor",
        "category": "ai_ml",
        "auth_type": "api_key",
        "auth_type_label": "Admin API Key",
        "status": "active",
        "color": "#000000",
        "docs_url": "https://docs.cursor.com/account/usage",
        "required_fields": [
            {"name": "api_key", "label": "Admin API Key", "input_type": "password", "placeholder": "", "help_text": "Cursor admin/team API key.", "secret": True},
            {"name": "team_id", "label": "Team ID", "input_type": "text", "placeholder": "", "help_text": "Cursor team identifier.", "secret": False},
        ],
    },

    # ─── DevTools ─────────────────────────────────────────────────
    "github": {
        "display_name": "GitHub",
        "category": "devtools",
        "auth_type": "oauth",
        "auth_type_label": "GitHub App",
        "status": "active",
        "color": "#181717",
        "docs_url": "https://docs.github.com/en/rest/billing",
        "required_fields": [
            {"name": "access_token", "label": "Personal Access Token", "input_type": "password", "placeholder": "ghp_...", "help_text": "GitHub PAT with read:org and admin:billing scope.", "secret": True},
            {"name": "org", "label": "Organization", "input_type": "text", "placeholder": "my-org", "help_text": "GitHub organization name.", "secret": False},
        ],
    },
    "temporal_cloud": {
        "display_name": "Temporal Cloud",
        "category": "devtools",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#000000",
        "docs_url": "https://docs.temporal.io/cloud/api-keys",
        "required_fields": [
            {"name": "api_key", "label": "API Key", "input_type": "password", "placeholder": "", "help_text": "Temporal Cloud API key with billing read.", "secret": True},
            {"name": "namespace", "label": "Namespace", "input_type": "text", "placeholder": "prod.xxxxx", "help_text": "Temporal Cloud namespace.", "secret": False},
        ],
    },
    "twilio": {
        "display_name": "Twilio",
        "category": "devtools",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#F22F46",
        "docs_url": "https://www.twilio.com/docs/usage/api",
        "required_fields": [
            {"name": "account_sid", "label": "Account SID", "input_type": "text", "placeholder": "AC...", "help_text": "Twilio Account SID.", "secret": False},
            {"name": "auth_token", "label": "Auth Token", "input_type": "password", "placeholder": "", "help_text": "Twilio auth token.", "secret": True},
        ],
    },

    # ─── CDN / Streaming ──────────────────────────────────────────
    "fastly": {
        "display_name": "Fastly",
        "category": "cdn_streaming",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "active",
        "color": "#FF282D",
        "docs_url": "https://www.fastly.com/documentation/reference/api/account/billing/",
        "required_fields": [
            {"name": "api_key", "label": "API Token", "input_type": "password", "placeholder": "", "help_text": "Fastly API token with billing read scope.", "secret": True},
        ],
    },
    "confluent": {
        "display_name": "Confluent",
        "category": "cdn_streaming",
        "auth_type": "api_key",
        "auth_type_label": "Cloud API Key",
        "status": "active",
        "color": "#1D2C4D",
        "docs_url": "https://docs.confluent.io/cloud/current/billing/overview.html",
        "required_fields": [
            {"name": "api_key", "label": "Cloud API Key", "input_type": "text", "placeholder": "", "help_text": "Confluent Cloud API key.", "secret": False},
            {"name": "api_secret", "label": "Cloud API Secret", "input_type": "password", "placeholder": "", "help_text": "Confluent Cloud API secret.", "secret": True},
        ],
    },
    "cloudflare": {
        "display_name": "Cloudflare",
        "category": "cdn_streaming",
        "auth_type": "api_key",
        "auth_type_label": "API Key",
        "status": "coming_soon",
        "color": "#F38020",
        "docs_url": "https://developers.cloudflare.com/api/",
        "required_fields": [
            {"name": "api_token", "label": "API Token", "input_type": "password", "placeholder": "", "help_text": "Cloudflare API token with billing read.", "secret": True},
        ],
    },
    "vercel": {
        "display_name": "Vercel",
        "category": "cdn_streaming",
        "auth_type": "api_key",
        "auth_type_label": "API Token",
        "status": "coming_soon",
        "color": "#000000",
        "docs_url": "https://vercel.com/docs/rest-api",
        "required_fields": [
            {"name": "api_token", "label": "API Token", "input_type": "password", "placeholder": "", "help_text": "Vercel personal/team API token.", "secret": True},
            {"name": "team_id", "label": "Team ID", "input_type": "text", "placeholder": "team_...", "help_text": "Vercel team ID (optional for personal).", "secret": False},
        ],
    },

    # ─── Custom ───────────────────────────────────────────────────
    "custom": {
        "display_name": "Custom Provider",
        "category": "custom",
        "auth_type": "focus_import",
        "auth_type_label": "FOCUS Spec CSV/Parquet",
        "status": "active",
        "color": "#6B7280",
        "docs_url": "https://focus.finops.org/",
        "required_fields": [
            {"name": "provider_name", "label": "Provider Name", "input_type": "text", "placeholder": "Internal Platform", "help_text": "Display name for this custom provider.", "secret": False},
            {"name": "import_path", "label": "Data Path", "input_type": "text", "placeholder": "/data/billing/custom/", "help_text": "Path to FOCUS-compliant CSV or Parquet files.", "secret": False},
        ],
    },
}


# ── Helpers ────────────────────────────────────────────────────────

CATEGORY_LABELS = {
    "cloud": "Cloud Providers",
    "kubernetes": "Kubernetes",
    "observability": "Observability",
    "database": "Databases",
    "ai_ml": "AI / ML",
    "devtools": "Developer Tools",
    "cdn_streaming": "CDN & Streaming",
    "custom": "Custom",
}

CATEGORY_ORDER = list(CATEGORY_LABELS.keys())


def get_catalog_grouped() -> list[dict]:
    """Return the catalog grouped by category, ordered."""
    groups: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}
    for key, entry in PROVIDER_CATALOG.items():
        cat = entry["category"]
        groups.setdefault(cat, []).append({"key": key, **entry})
    return [
        {"category": cat, "category_label": CATEGORY_LABELS.get(cat, cat), "providers": providers}
        for cat, providers in groups.items()
        if providers
    ]


def get_provider(key: str) -> dict | None:
    """Look up a single provider by key."""
    entry = PROVIDER_CATALOG.get(key)
    if entry:
        return {"key": key, **entry}
    return None


def get_required_field_names(key: str) -> list[str]:
    """Return the required credential field names for a provider."""
    entry = PROVIDER_CATALOG.get(key, {})
    return [f["name"] for f in entry.get("required_fields", [])]
