"""
AI Cost Insights Service

Generates plain-English explanations of cost data using an LLM.
Supports Amazon Bedrock (Claude) and OpenAI-compatible APIs.
"""

import json
import logging
from datetime import date

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AICostInsightsService:
    """Generates narrative cost insights from structured data."""

    def __init__(self):
        self.session = boto3.Session(region_name="us-east-1")

    def generate_insight(self, cost_context: dict) -> str:
        """
        Given structured cost data, generate a plain-English insight.

        cost_context should include keys like:
        - total_spend, period, top_services, changes, anomalies, etc.
        """
        prompt = self._build_prompt(cost_context)

        # Try Bedrock first
        try:
            return self._call_bedrock(prompt)
        except Exception as e:
            logger.warning(f"Bedrock failed: {e}")

        # Fallback: generate a basic template-based summary
        return self._fallback_summary(cost_context)

    def _build_prompt(self, ctx: dict) -> str:
        return f"""You are a cloud cost analyst. Given the following AWS cost data, write a concise 3-5 sentence summary explaining the spending patterns, highlighting any notable changes or concerns, and suggesting one actionable optimization.

Cost Data:
{json.dumps(ctx, indent=2, default=str)}

Write in a professional but conversational tone. Be specific about dollar amounts and percentages. Start directly with the analysis, no preamble."""

    def _call_bedrock(self, prompt: str) -> str:
        """Call Amazon Bedrock (Claude) for insight generation."""
        client = self.session.client("bedrock-runtime", region_name="us-east-1")

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        })

        response = client.invoke_model(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _fallback_summary(self, ctx: dict) -> str:
        """Generate a basic template-based summary when LLM is unavailable."""
        lines = []

        total = ctx.get("total_spend", 0)
        period = ctx.get("period", "this period")
        lines.append(f"Your AWS spend for {period} totals ${total:.2f}.")

        top_services = ctx.get("top_services", [])
        if top_services:
            top = top_services[0]
            lines.append(
                f"The largest cost driver is {top['service']} "
                f"at ${top['amount']:.2f} ({top.get('pct', 0):.0f}% of total)."
            )

        change = ctx.get("change_pct")
        if change is not None:
            direction = "increased" if change > 0 else "decreased"
            lines.append(
                f"Costs have {direction} by {abs(change):.1f}% compared to the previous period."
            )

        anomaly_count = ctx.get("anomaly_count", 0)
        if anomaly_count > 0:
            lines.append(f"There are {anomaly_count} active cost anomalies to review.")

        if not lines:
            lines.append("No significant cost patterns detected for this period.")

        return " ".join(lines)

    def generate_drill_down_insight(self, drill_down_data: dict) -> str:
        """Generate an insight specifically for the drill-down/Why? view."""
        ctx = {
            "current_total": drill_down_data.get("current_period", {}).get("total", 0),
            "previous_total": drill_down_data.get("previous_period", {}).get("total", 0),
            "total_change": drill_down_data.get("total_change", 0),
            "total_change_pct": drill_down_data.get("total_change_pct", 0),
            "direction": drill_down_data.get("direction", "unchanged"),
            "top_increases": drill_down_data.get("top_increases", [])[:3],
            "top_decreases": drill_down_data.get("top_decreases", [])[:3],
            "new_services": drill_down_data.get("new_services", []),
        }
        return self.generate_insight(ctx)
