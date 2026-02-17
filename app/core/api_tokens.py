"""
API Token Management

Provides API token authentication for the CloudPulse v2 API.
Supports user tokens and service tokens with read/write scopes,
modeled after Vantage's API token system.
"""

import hashlib
import logging
import secrets
from datetime import datetime
from enum import Enum

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


class TokenScope(str, Enum):
    READ = "read"
    WRITE = "write"


class TokenType(str, Enum):
    USER = "user"       # Personal access token
    SERVICE = "service"  # Service/automation token


def generate_api_token(prefix: str = "cpat") -> tuple[str, str]:
    """
    Generate a new API token.
    Returns (raw_token, hashed_token).
    The raw token is shown once to the user; we store only the hash.

    Token format: cpat_<32 hex chars> (CloudPulse API Token)
    """
    raw = secrets.token_hex(32)
    token = f"{prefix}_{raw}"
    hashed = hash_token(token)
    return token, hashed


def hash_token(token: str) -> str:
    """Hash an API token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_api_token_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency that authenticates via API token (Bearer header).
    Falls back to None if no token provided (allows JWT fallback).
    """
    if credentials is None:
        return None

    token = credentials.credentials
    if not token.startswith(("cpat_", "cpst_")):
        return None  # Not an API token, let JWT handler try

    # Import here to avoid circular dependency
    from app.models.v2 import APIToken

    hashed = hash_token(token)
    result = await db.execute(
        select(APIToken).where(
            APIToken.token_hash == hashed,
            APIToken.is_active == True,
            APIToken.revoked_at == None,
        )
    )
    api_token = result.scalar_one_or_none()

    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API token",
        )

    # Update last used timestamp
    api_token.last_used_at = datetime.utcnow()
    await db.flush()

    return api_token


def require_scope(scope: TokenScope):
    """Dependency that checks if the API token has the required scope."""
    async def _check_scope(
        api_token=Depends(get_api_token_user),
    ):
        if api_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API token required",
            )
        if scope == TokenScope.WRITE and TokenScope.WRITE not in api_token.scopes_list:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Write scope required for this operation",
            )
        return api_token
    return _check_scope
