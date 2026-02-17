"""Saved Filter endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import SavedFilter, Workspace
from app.api.v2.schemas import (
    SavedFilterCreate, SavedFilterUpdate, SavedFilterResponse,
    SavedFilterListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/saved_filters", tags=["Saved Filters"])


@router.get("", response_model=SavedFilterListResponse)
async def list_saved_filters(
    workspace_token: str | None = None,
    page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(SavedFilter.workspace_id == ws.id)
    items, total = await paginated_query(db, SavedFilter, page, limit, filters=filters)
    return SavedFilterListResponse(
        saved_filters=[SavedFilterResponse.model_validate(sf) for sf in items],
        links=pagination_links("/v2/saved_filters", page, limit, total),
    )


@router.post("", response_model=SavedFilterResponse, status_code=201)
async def create_saved_filter(
    payload: SavedFilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    sf = SavedFilter(
        token=generate_token("sf"),
        workspace_id=ws.id,
        title=payload.title,
        filter=payload.filter,
    )
    db.add(sf)
    await db.flush()
    await db.refresh(sf)
    return SavedFilterResponse.model_validate(sf)


@router.get("/{token}", response_model=SavedFilterResponse)
async def get_saved_filter(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SavedFilterResponse.model_validate(await get_by_token(db, SavedFilter, token))


@router.put("/{token}", response_model=SavedFilterResponse)
async def update_saved_filter(token: str, payload: SavedFilterUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    sf = await get_by_token(db, SavedFilter, token)
    if payload.title is not None:
        sf.title = payload.title
    if payload.filter is not None:
        sf.filter = payload.filter
    await db.flush()
    await db.refresh(sf)
    return SavedFilterResponse.model_validate(sf)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_saved_filter(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    sf = await get_by_token(db, SavedFilter, token)
    await db.delete(sf)
    await db.flush()
    return MessageResponse(message="Saved filter deleted")
