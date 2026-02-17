"""Segment endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import Segment, Workspace
from app.api.v2.schemas import (
    SegmentCreate, SegmentUpdate, SegmentResponse,
    SegmentListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/segments", tags=["Segments"])


@router.get("", response_model=SegmentListResponse)
async def list_segments(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(Segment.workspace_id == ws.id)
    items, total = await paginated_query(db, Segment, page, limit, filters=filters)
    return SegmentListResponse(
        segments=[SegmentResponse.model_validate(s) for s in items],
        links=pagination_links("/v2/segments", page, limit, total),
    )


@router.post("", response_model=SegmentResponse, status_code=201)
async def create_segment(
    payload: SegmentCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    parent_id = None
    if payload.parent_segment_token:
        parent = await get_by_token(db, Segment, payload.parent_segment_token)
        parent_id = parent.id

    seg = Segment(
        token=generate_token("seg"), workspace_id=ws.id,
        parent_segment_id=parent_id, title=payload.title,
        description=payload.description, filter=payload.filter,
        priority=payload.priority, track_unallocated=payload.track_unallocated,
    )
    db.add(seg)
    await db.flush()
    await db.refresh(seg)
    return SegmentResponse.model_validate(seg)


@router.get("/{token}", response_model=SegmentResponse)
async def get_segment(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SegmentResponse.model_validate(await get_by_token(db, Segment, token))


@router.put("/{token}", response_model=SegmentResponse)
async def update_segment(
    token: str, payload: SegmentUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    seg = await get_by_token(db, Segment, token)
    update = payload.model_dump(exclude_unset=True)
    for key, val in update.items():
        setattr(seg, key, val)
    await db.flush()
    await db.refresh(seg)
    return SegmentResponse.model_validate(seg)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_segment(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    seg = await get_by_token(db, Segment, token)
    await db.delete(seg)
    await db.flush()
    return MessageResponse(message="Segment deleted")
