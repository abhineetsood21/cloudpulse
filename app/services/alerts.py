"""
Alert Service

Sends notifications via email (SendGrid) and Slack webhooks.
"""

import json
import logging
from datetime import date

import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AlertService:
    """Sends alerts via email and Slack."""

    def __init__(self):
        self.sendgrid_client = None
        if settings.sendgrid_api_key:
            self.sendgrid_client = SendGridAPIClient(api_key=settings.sendgrid_api_key)

    # --- Email Alerts ---

    async def send_email_alert(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> bool:
        """Send an email alert via SendGrid."""
        if not self.sendgrid_client:
            logger.warning("SendGrid not configured, skipping email alert")
            return False

        message = Mail(
            from_email=Email(settings.sendgrid_from_email, "CloudPulse Alerts"),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content),
        )

        try:
            response = self.sendgrid_client.send(message)
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return response.status_code in (200, 201, 202)
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_anomaly_email(
        self,
        to_email: str,
        anomalies: list[dict],
        account_name: str = "AWS Account",
    ) -> bool:
        """Send a formatted anomaly alert email."""
        if not anomalies:
            return False

        severity_emoji = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }

        rows = ""
        for a in anomalies:
            emoji = severity_emoji.get(a["severity"], "⚪")
            rows += f"""
            <tr>
                <td>{emoji} {a['severity'].upper()}</td>
                <td>{a['service']}</td>
                <td>${a['expected_amount']:.2f}</td>
                <td>${a['actual_amount']:.2f}</td>
                <td>+{a['deviation_pct']*100:.0f}%</td>
            </tr>
            """

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>⚠️ CloudPulse Cost Alert</h2>
            <p>Anomalies detected for <strong>{account_name}</strong> on {anomalies[0]['date']}:</p>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f4f4f4;">
                        <th style="padding: 8px; text-align: left;">Severity</th>
                        <th style="padding: 8px; text-align: left;">Service</th>
                        <th style="padding: 8px; text-align: right;">Expected</th>
                        <th style="padding: 8px; text-align: right;">Actual</th>
                        <th style="padding: 8px; text-align: right;">Change</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                — CloudPulse | <a href="{settings.app_url}">View Dashboard</a>
            </p>
        </body>
        </html>
        """

        critical_count = sum(1 for a in anomalies if a["severity"] == "critical")
        warning_count = sum(1 for a in anomalies if a["severity"] == "warning")

        subject = f"CloudPulse Alert: {account_name}"
        if critical_count:
            subject += f" — {critical_count} CRITICAL"
        elif warning_count:
            subject += f" — {warning_count} warnings"

        return await self.send_email_alert(to_email, subject, html)

    async def send_daily_summary_email(
        self,
        to_email: str,
        total_spend: float,
        top_services: list[dict],
        anomaly_count: int,
        account_name: str = "AWS Account",
        report_date: date | None = None,
    ) -> bool:
        """Send a daily cost summary email."""
        report_date = report_date or date.today()

        service_rows = ""
        for svc in top_services[:10]:
            service_rows += f"""
            <tr>
                <td style="padding: 4px 8px;">{svc['service']}</td>
                <td style="padding: 4px 8px; text-align: right;">${svc['amount']:.2f}</td>
            </tr>
            """

        anomaly_notice = ""
        if anomaly_count > 0:
            anomaly_notice = f"""
            <p style="color: #e74c3c;">
                ⚠️ <strong>{anomaly_count} anomalies detected.</strong>
                <a href="{settings.app_url}">View details →</a>
            </p>
            """

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>📊 CloudPulse Daily Summary</h2>
            <p><strong>{account_name}</strong> — {report_date.isoformat()}</p>

            <div style="background: #f0f7ff; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <h3 style="margin: 0;">Total Spend: ${total_spend:.2f}</h3>
            </div>

            {anomaly_notice}

            <h3>Top Services</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tbody>{service_rows}</tbody>
            </table>

            <p style="margin-top: 20px; color: #666; font-size: 12px;">
                — CloudPulse | <a href="{settings.app_url}">View Dashboard</a>
            </p>
        </body>
        </html>
        """

        subject = f"CloudPulse Daily: ${total_spend:.2f} — {account_name} ({report_date})"
        return await self.send_email_alert(to_email, subject, html)

    # --- Slack Alerts ---

    async def send_slack_alert(
        self,
        webhook_url: str,
        message: dict,
    ) -> bool:
        """Send a message to a Slack webhook."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    logger.info("Slack alert sent successfully")
                    return True
                else:
                    logger.error(f"Slack webhook returned {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False

    async def send_anomaly_slack(
        self,
        webhook_url: str,
        anomalies: list[dict],
        account_name: str = "AWS Account",
    ) -> bool:
        """Send a formatted anomaly alert to Slack."""
        if not anomalies:
            return False

        severity_emoji = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "🔵",
        }

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"⚠️ CloudPulse Cost Alert — {account_name}",
                },
            },
            {"type": "divider"},
        ]

        for a in anomalies:
            emoji = severity_emoji.get(a["severity"], "⚪")
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"{emoji} *{a['severity'].upper()}*: {a['service']}\n"
                        f"Expected: ${a['expected_amount']:.2f} → "
                        f"Actual: ${a['actual_amount']:.2f} "
                        f"(*+{a['deviation_pct']*100:.0f}%*)"
                    ),
                },
            })

        message = {"blocks": blocks}
        return await self.send_slack_alert(webhook_url, message)

    async def send_daily_summary_slack(
        self,
        webhook_url: str,
        total_spend: float,
        top_services: list[dict],
        anomaly_count: int,
        account_name: str = "AWS Account",
    ) -> bool:
        """Send a daily summary to Slack."""
        services_text = "\n".join(
            f"• {svc['service']}: ${svc['amount']:.2f}"
            for svc in top_services[:5]
        )

        anomaly_text = ""
        if anomaly_count > 0:
            anomaly_text = f"\n\n⚠️ *{anomaly_count} anomalies detected*"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 CloudPulse Daily — {account_name}",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Total Spend:* ${total_spend:.2f}{anomaly_text}",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Services:*\n{services_text}",
                },
            },
        ]

        message = {"blocks": blocks}
        return await self.send_slack_alert(webhook_url, message)
