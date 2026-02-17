"""
Daily Digest Cron Job

Run daily (e.g. 8am UTC) to send cost summary + anomaly alerts
to all users with daily_summary enabled.

Usage:
    python scripts/daily_digest.py

Schedule via cron:
    0 8 * * * cd /path/to/cloudpulse && python scripts/daily_digest.py
"""

import asyncio
import logging
import sys
import os
from datetime import date, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, func
from app.core.database import async_session as async_session_factory, engine
from app.models.models import (
    AWSAccount, CostRecord, Anomaly, AlertConfig,
    AccountStatus, AlertChannel, Budget,
)
from app.services.alerts import AlertService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def run_daily_digest():
    """Main digest loop: for each account, gather data and send notifications."""
    alert_service = AlertService()
    yesterday = date.today() - timedelta(days=1)

    async with async_session_factory() as db:
        # Get all active accounts
        result = await db.execute(
            select(AWSAccount).where(AWSAccount.status == AccountStatus.ACTIVE)
        )
        accounts = result.scalars().all()

        if not accounts:
            logger.info("No active accounts. Nothing to digest.")
            return

        # Get all alert configs with daily_summary enabled
        alert_result = await db.execute(
            select(AlertConfig).where(AlertConfig.daily_summary == True)
        )
        alert_configs = alert_result.scalars().all()

        if not alert_configs:
            logger.info("No alert configs with daily summary enabled.")
            return

        for account in accounts:
            account_name = account.account_name or account.aws_account_id
            logger.info(f"Processing digest for account: {account_name}")

            # --- Yesterday's spend by service ---
            cost_result = await db.execute(
                select(
                    CostRecord.service,
                    func.sum(CostRecord.amount).label("total"),
                )
                .where(CostRecord.aws_account_id == account.id)
                .where(CostRecord.date == yesterday)
                .group_by(CostRecord.service)
                .order_by(func.sum(CostRecord.amount).desc())
            )
            service_rows = cost_result.all()
            top_services = [
                {"service": row.service, "amount": round(row.total, 2)}
                for row in service_rows
            ]
            total_spend = sum(s["amount"] for s in top_services)

            # --- Recent anomalies (last 24h) ---
            anomaly_result = await db.execute(
                select(func.count(Anomaly.id))
                .where(Anomaly.aws_account_id == account.id)
                .where(Anomaly.date >= yesterday)
                .where(Anomaly.acknowledged == False)
            )
            anomaly_count = anomaly_result.scalar() or 0

            # --- Budget alerts ---
            budget_result = await db.execute(
                select(Budget)
                .where(Budget.aws_account_id == account.id)
                .where(Budget.is_active == True)
            )
            budgets = budget_result.scalars().all()
            budget_warnings = []
            for b in budgets:
                if b.amount > 0 and b.current_spend / b.amount >= b.alert_at_pct:
                    pct = round(b.current_spend / b.amount * 100)
                    budget_warnings.append(
                        f"⚠️ Budget '{b.name}': ${b.current_spend:.2f}/${b.amount:.2f} ({pct}%)"
                    )

            # --- Send to all configured channels ---
            for config in alert_configs:
                # Only send for accounts owned by this user
                if config.user_id != account.user_id:
                    continue

                if config.channel == AlertChannel.EMAIL and config.email_address:
                    success = await alert_service.send_daily_summary_email(
                        to_email=config.email_address,
                        total_spend=total_spend,
                        top_services=top_services,
                        anomaly_count=anomaly_count,
                        account_name=account_name,
                        report_date=yesterday,
                    )
                    logger.info(
                        f"Email digest to {config.email_address}: "
                        f"{'sent' if success else 'FAILED'}"
                    )

                elif config.channel == AlertChannel.SLACK and config.slack_webhook_url:
                    success = await alert_service.send_daily_summary_slack(
                        webhook_url=config.slack_webhook_url,
                        total_spend=total_spend,
                        top_services=top_services,
                        anomaly_count=anomaly_count,
                        account_name=account_name,
                    )
                    logger.info(
                        f"Slack digest for {account_name}: "
                        f"{'sent' if success else 'FAILED'}"
                    )

            logger.info(
                f"Digest complete for {account_name}: "
                f"${total_spend:.2f} spend, {anomaly_count} anomalies, "
                f"{len(budget_warnings)} budget warnings"
            )

    logger.info("Daily digest complete.")


if __name__ == "__main__":
    asyncio.run(run_daily_digest())
