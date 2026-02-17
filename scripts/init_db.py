"""Initialize the database by creating all tables."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models.models import (
    User, AWSAccount, CostRecord, Anomaly, Recommendation, AlertConfig, Budget, SharedReport
)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All database tables created successfully!")

    # Print table names
    async with engine.begin() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: list(Base.metadata.tables.keys())
        )
    print(f"📋 Tables: {', '.join(tables)}")


if __name__ == "__main__":
    asyncio.run(init_db())
