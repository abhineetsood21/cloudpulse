"""
Shared helpers for v2 API routes.

Token generation, pagination, and reusable CRUD utilities.
"""

import secrets
import uuid

from fastapi import HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


def generate_token(prefix: str = "cpls") -> str:
    """Generate a unique resource token like cpls_abc123..."""
    return f"{prefix}_{secrets.token_hex(16)}"


async def get_by_token(db: AsyncSession, model, token: str):
    """Fetch a single record by its token, or 404."""
    result = await db.execute(select(model).where(model.token == token))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail=f"{model.__tablename__} not found")
    return obj


async def get_workspace_by_token(db: AsyncSession, token: str):
    """Resolve workspace by token."""
    from app.models.v2 import Workspace
    return await get_by_token(db, Workspace, token)


async def paginated_query(
    db: AsyncSession,
    model,
    page: int = 1,
    limit: int = 25,
    filters: list | None = None,
):
    """Run a paginated query and return (items, total)."""
    query = select(model)
    count_query = select(func.count()).select_from(model)

    if filters:
        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return items, total


def pagination_links(base_url: str, page: int, limit: int, total: int) -> dict:
    """Build pagination links dict."""
    links = {"self": f"{base_url}?page={page}&limit={limit}"}
    if page * limit < total:
        links["next"] = f"{base_url}?page={page + 1}&limit={limit}"
    if page > 1:
        links["prev"] = f"{base_url}?page={page - 1}&limit={limit}"
    return links
