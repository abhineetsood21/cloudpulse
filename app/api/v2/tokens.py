"""API Token management endpoints."""

import hashlib
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import APIToken
from app.api.v2.schemas import (
    APITokenCreate, APITokenResponse, APITokenCreatedResponse,
    APITokenListResponse, MessageResponse,
)
from app.api.v2.helpers import paginated_query, pagination_links

router = APIRouter(prefix="/api_tokens", tags=["API Tokens"])


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


@router.get("", response_model=APITokenListResponse)
async def list_api_tokens(
    page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await paginated_query(
        db, APIToken, page, limit,
        filters=[APIToken.user_id == current_user.id, APIToken.is_active == True],
    )
    return APITokenListResponse(
        api_tokens=[APITokenResponse.model_validate(t) for t in items],
        links=pagination_links("/v2/api_tokens", page, limit, total),
    )


@router.post("", response_model=APITokenCreatedResponse, status_code=201)
async def create_api_token(
    payload: APITokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw_token = f"cpls_{secrets.token_hex(32)}"
    token_prefix = raw_token[:12]

    api_token = APIToken(
        user_id=current_user.id,
        name=payload.name,
        token_hash=_hash_token(raw_token),
        token_prefix=token_prefix,
        scopes=payload.scopes,
    )
    db.add(api_token)
    await db.flush()
    await db.refresh(api_token)

    return APITokenCreatedResponse(
        token=raw_token,
        token_prefix=token_prefix,
        name=api_token.name,
        scopes=api_token.scopes,
        is_active=api_token.is_active,
        last_used_at=api_token.last_used_at,
        created_at=api_token.created_at,
    )


@router.delete("/{token_prefix}", response_model=MessageResponse)
async def revoke_api_token(
    token_prefix: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIToken).where(
            APIToken.token_prefix == token_prefix,
            APIToken.user_id == current_user.id,
            APIToken.is_active == True,
        )
    )
    token = result.scalar_one_or_none()
    if not token:
        raise HTTPException(status_code=404, detail="API token not found")

    token.is_active = False
    token.revoked_at = datetime.utcnow()
    await db.flush()
    return MessageResponse(message="API token revoked")
