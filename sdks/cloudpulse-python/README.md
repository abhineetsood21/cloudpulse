# cloudpulse-python

Python SDK for the [CloudPulse](https://cloudpulse.dev) Cloud Cost Management API.

## Installation

```bash
pip install cloudpulse-sdk
```

## Quick Start

```python
from cloudpulse import CloudPulseClient

client = CloudPulseClient(api_token="cpls_...")

# List workspaces
workspaces = client.workspaces.list()

# Create a cost report
report = client.cost_reports.create(
    title="Monthly AWS Costs",
    workspace_token="ws_abc123",
    filter='costs.provider = "aws"',
    date_interval="last_30_days",
)

# Create a segment
segment = client.segments.create(
    title="Backend Services",
    workspace_token="ws_abc123",
    filter='costs.service = "Amazon EC2"',
)

client.close()
```

## Resources

| Resource | Methods |
|---|---|
| `client.workspaces` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.cost_reports` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.folders` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.saved_filters` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.dashboards` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.segments` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.teams` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.access_grants` | `list()`, `create()`, `delete()` |
| `client.virtual_tags` | `list()`, `get()`, `create()`, `update()`, `delete()` |
| `client.api_tokens` | `list()`, `create()`, `revoke()` |
| `client.resource_reports` | `list()`, `get()`, `create()`, `update()`, `delete()` |

## Authentication

Get an API token from Settings → API Keys in the CloudPulse dashboard.

```python
import os
client = CloudPulseClient(api_token=os.environ["CLOUDPULSE_API_TOKEN"])
```

## License

MIT
