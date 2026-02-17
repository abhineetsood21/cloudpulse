#!/usr/bin/env python3
"""
Example: Connect a provider to CloudPulse using the Python SDK.

Usage:
    pip install -e sdk/python/
    python examples/connect_provider.py
"""

from cloudpulse import CloudPulseClient
from cloudpulse.client import CloudPulseError

CLOUDPULSE_URL = "http://localhost:8000"
API_TOKEN = "your-api-token"  # Create one via Settings > API Keys


def main():
    client = CloudPulseClient(CLOUDPULSE_URL, token=API_TOKEN)

    # 1. Browse available providers
    catalog = client.get_catalog()
    print("Available providers:")
    for category in catalog["categories"]:
        print(f"\n  {category['category_label']}:")
        for p in category["providers"]:
            status = "✓" if p["status"] == "active" else "◌"
            print(f"    {status} {p['display_name']} ({p['key']})")

    # 2. Connect Datadog (replace with your credentials)
    try:
        integration = client.connect(
            provider="datadog",
            credentials={
                "api_key": "your-datadog-api-key",
                "app_key": "your-datadog-app-key",
                "site": "datadoghq.com",
            },
            display_name="Production Datadog",
        )
        print(f"\nConnected: {integration['provider_display_name']} (ID: {integration['id']})")
    except CloudPulseError as e:
        print(f"\nConnection failed: {e.detail}")
        return

    # 3. Trigger a cost sync
    result = client.sync(integration["id"])
    print(f"Sync result: {result['status']} ({result['rows_ingested']} rows)")

    # 4. Query costs
    costs = client.query_costs(provider="datadog", granularity="daily")
    print(f"Cost rows: {len(costs.get('rows', []))}")


if __name__ == "__main__":
    main()
