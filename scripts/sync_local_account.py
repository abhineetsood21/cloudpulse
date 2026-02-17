"""
Sync local AWS account cost data into CloudPulse database.

Uses local AWS credentials (~/.aws/credentials) to pull cost data
and store it in the local PostgreSQL database.
"""

import asyncio
import sys
import os
import uuid
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from sqlalchemy import select, delete

from app.core.database import async_session
from app.models.models import AWSAccount, CostRecord, AccountStatus, User
from app.services.local_cost_explorer import LocalCostExplorerService
from app.services.anomaly_detector import AnomalyDetector
from app.models.models import Anomaly


async def sync():
    # --- Get AWS account ID ---
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    aws_account_id = identity["Account"]
    print(f"🔗 AWS Account: {aws_account_id}")

    async with async_session() as session:
        # --- Ensure a dev user exists ---
        result = await session.execute(
            select(User).where(User.email == "dev@cloudpulse.local")
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email="dev@cloudpulse.local",
                hashed_password="not-a-real-hash-local-dev-only",
                is_active=True,
            )
            session.add(user)
            await session.flush()
            print(f"👤 Created dev user: {user.id}")
        else:
            print(f"👤 Using existing dev user: {user.id}")

        # --- Ensure AWS account record exists ---
        result = await session.execute(
            select(AWSAccount).where(AWSAccount.aws_account_id == aws_account_id)
        )
        account = result.scalar_one_or_none()

        if not account:
            account = AWSAccount(
                user_id=user.id,
                aws_account_id=aws_account_id,
                role_arn=f"arn:aws:iam::{aws_account_id}:user/local",
                external_id="local-dev",
                account_name="Local Dev Account",
                status=AccountStatus.ACTIVE,
            )
            session.add(account)
            await session.flush()
            print(f"☁️  Created account record: {account.id}")
        else:
            print(f"☁️  Using existing account: {account.id}")

        # --- Fetch cost data (last 30 days) ---
        svc = LocalCostExplorerService()
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        print(f"📊 Fetching costs from {start_date} to {end_date}...")
        cost_data = svc.get_cost_by_service(start_date, end_date)
        print(f"   Found {len(cost_data)} cost records")

        # --- Clear old records for this period ---
        await session.execute(
            delete(CostRecord)
            .where(CostRecord.aws_account_id == account.id)
            .where(CostRecord.date >= start_date)
            .where(CostRecord.date <= end_date)
        )

        # --- Insert new records ---
        total_spend = 0
        services_seen = set()

        for record in cost_data:
            cr = CostRecord(
                aws_account_id=account.id,
                date=date.fromisoformat(record["date"]),
                service=record["service"],
                amount=record["amount"],
                currency=record["currency"],
            )
            session.add(cr)
            total_spend += record["amount"]
            services_seen.add(record["service"])

        # --- Run anomaly detection ---
        print("🔍 Running anomaly detection...")
        detector = AnomalyDetector()
        anomalies = detector.detect(cost_data)

        # Clear old anomalies for the target date
        if anomalies:
            target_date = date.fromisoformat(anomalies[0]["date"])
            await session.execute(
                delete(Anomaly)
                .where(Anomaly.aws_account_id == account.id)
                .where(Anomaly.date == target_date)
            )

        for a in anomalies:
            anomaly = Anomaly(
                aws_account_id=account.id,
                date=date.fromisoformat(a["date"]),
                service=a["service"],
                expected_amount=a["expected_amount"],
                actual_amount=a["actual_amount"],
                deviation_pct=a["deviation_pct"],
                severity=a["severity"],
            )
            session.add(anomaly)

        # --- Update account sync time ---
        account.last_sync_at = datetime.utcnow()

        await session.commit()

        # --- Summary ---
        print(f"\n✅ Sync complete!")
        print(f"   📅 Period: {start_date} → {end_date}")
        print(f"   💰 Total spend: ${total_spend:.2f}")
        print(f"   🏷️  Services: {len(services_seen)}")
        print(f"   📝 Cost records stored: {len(cost_data)}")
        print(f"   ⚠️  Anomalies detected: {len(anomalies)}")

        if anomalies:
            print(f"\n   Anomaly details:")
            for a in anomalies:
                print(f"   {a['severity'].upper():>8} | {a['service'][:40]:<40} | "
                      f"expected ${a['expected_amount']:.2f} → actual ${a['actual_amount']:.2f} "
                      f"(+{a['deviation_pct']*100:.0f}%)")

        print(f"\n   Account ID (for API queries): {account.id}")


if __name__ == "__main__":
    asyncio.run(sync())
