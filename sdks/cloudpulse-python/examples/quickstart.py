"""
CloudPulse Python SDK — Quick Start Example.

pip install cloudpulse-sdk
"""

import os

from cloudpulse import CloudPulseClient

# Initialize client with your API token
client = CloudPulseClient(
    api_token=os.environ["CLOUDPULSE_API_TOKEN"],
    base_url=os.environ.get("CLOUDPULSE_API_URL", "https://api.cloudpulse.dev"),
)

# --- Workspaces ---
print("=== Workspaces ===")
workspace = client.workspaces.create(name="Production")
print(f"Created workspace: {workspace.token}")

workspaces = client.workspaces.list()
for ws in workspaces.workspaces:
    print(f"  - {ws.name} ({ws.token})")

# --- Cost Reports ---
print("\n=== Cost Reports ===")
report = client.cost_reports.create(
    title="Monthly EC2 Costs",
    workspace_token=workspace.token,
    filter='costs.provider = "aws" AND costs.service = "Amazon EC2"',
    groupings="service",
    date_interval="last_30_days",
)
print(f"Created report: {report.token} — {report.title}")

# --- Folders ---
print("\n=== Folders ===")
folder = client.folders.create(
    title="Engineering",
    workspace_token=workspace.token,
)
print(f"Created folder: {folder.token}")

# --- Segments ---
print("\n=== Segments ===")
segment = client.segments.create(
    title="Backend Services",
    workspace_token=workspace.token,
    filter='costs.service = "Amazon EC2" OR costs.service = "Amazon RDS"',
)
print(f"Created segment: {segment.token}")

# --- Virtual Tags ---
print("\n=== Virtual Tags ===")
vtag = client.virtual_tags.create(
    key="team",
    workspace_token=workspace.token,
    description="Map costs to engineering teams",
    values=[
        {"name": "platform", "filter": 'tags.team = "platform"'},
        {"name": "frontend", "filter": 'tags.team = "frontend"'},
    ],
)
print(f"Created virtual tag: {vtag.token} ({vtag.key})")

# --- Clean up ---
print("\n=== Cleanup ===")
client.virtual_tags.delete(vtag.token)
client.segments.delete(segment.token)
client.folders.delete(folder.token)
client.cost_reports.delete(report.token)
client.workspaces.delete(workspace.token)
print("All resources cleaned up.")

client.close()
