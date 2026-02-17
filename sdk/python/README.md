# CloudPulse Python SDK

Python client for the [CloudPulse](https://github.com/abhineetsood21/cloudpulse) cost management API.

## Install

```bash
pip install cloudpulse-sdk
# or from source
pip install -e sdk/python/
```

## Quick Start

```python
from cloudpulse import CloudPulseClient

client = CloudPulseClient("http://localhost:8000", token="your-api-token")

# Browse available providers
catalog = client.get_catalog()
for category in catalog["categories"]:
    print(f"\n{category['category_label']}:")
    for p in category["providers"]:
        print(f"  {p['display_name']} ({p['key']}) - {p['status']}")

# Connect Datadog
integration = client.connect("datadog", credentials={
    "api_key": "your-dd-api-key",
    "app_key": "your-dd-app-key",
    "site": "datadoghq.com",
})
print(f"Connected: {integration['id']}")

# Trigger a cost sync
result = client.sync(integration["id"])
print(f"Synced {result['rows_ingested']} rows")

# Query costs
costs = client.query_costs(provider="datadog", granularity="daily")
for row in costs.get("rows", []):
    print(row)

# Disconnect
client.disconnect(integration["id"])
```

## Available Methods

| Category | Methods |
|---|---|
| **Integrations** | `get_catalog()`, `list_integrations()`, `connect()`, `validate()`, `sync()`, `disconnect()` |
| **Cost Queries** | `query_costs()`, `get_billing_stats()` |
| **Budgets** | `list_budgets()`, `create_budget()` |
| **API Tokens** | `list_tokens()`, `create_token()`, `revoke_token()` |
| **Webhooks** | `list_webhooks()`, `create_webhook()`, `delete_webhook()` |

## Error Handling

```python
from cloudpulse.client import CloudPulseError

try:
    client.connect("invalid_provider", credentials={})
except CloudPulseError as e:
    print(f"API error {e.status_code}: {e.detail}")
```
