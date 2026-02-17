"""
FinOps-as-Code: Automated Cost Alert Pipeline

This example shows how to use the CloudPulse Python SDK to:
1. Create a workspace and cost report
2. Set up virtual tags for team cost allocation
3. Build segments for budget tracking
4. Automate daily cost threshold alerts

Requirements:
    pip install cloudpulse-sdk
"""

import os
from cloudpulse import CloudPulseClient

# --- Configuration ---
API_TOKEN = os.environ["CLOUDPULSE_API_TOKEN"]
MONTHLY_BUDGET = 50_000  # $50k/month
ALERT_THRESHOLD = 0.80   # Alert at 80%

client = CloudPulseClient(api_token=API_TOKEN)


def setup_workspace():
    """Create workspace with team-based cost allocation."""
    # Create workspace
    ws = client.workspaces.create(name="FinOps Automation")
    print(f"Workspace: {ws.token}")

    # Set up virtual tags for team allocation
    client.virtual_tags.create(
        key="cost_center",
        workspace_token=ws.token,
        description="Map AWS costs to cost centers",
        values=[
            {"name": "engineering", "filter": 'tags.team = "engineering" OR tags.department = "eng"'},
            {"name": "data", "filter": 'tags.team = "data" OR costs.service = "Amazon Redshift"'},
            {"name": "platform", "filter": 'tags.team = "platform" OR costs.service = "Amazon EKS"'},
        ],
    )

    # Create segments for each team
    for team in ["engineering", "data", "platform"]:
        client.segments.create(
            title=f"{team.title()} Costs",
            workspace_token=ws.token,
            filter=f'virtual_tags.cost_center = "{team}"',
            priority=1,
        )

    # Create cost report with daily granularity
    report = client.cost_reports.create(
        title="Daily Cost Tracker",
        workspace_token=ws.token,
        groupings="service",
        date_interval="this_month",
        date_bucket="day",
    )

    print(f"Report: {report.token}")
    return ws


def check_budget_threshold():
    """Check if current month spend exceeds threshold."""
    reports = client.cost_reports.list()
    for report in reports.cost_reports:
        if report.title == "Daily Cost Tracker":
            # In production, you'd query the cost data from the report
            # and compare against the budget threshold
            print(f"Checking report: {report.token}")
            print(f"Budget: ${MONTHLY_BUDGET:,}")
            print(f"Alert threshold: {ALERT_THRESHOLD:.0%} (${MONTHLY_BUDGET * ALERT_THRESHOLD:,.0f})")
            break


if __name__ == "__main__":
    ws = setup_workspace()
    check_budget_threshold()
    print("\nFinOps automation setup complete!")
    client.close()
