"""Virtual Tag endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import VirtualTag, Workspace
from app.api.v2.schemas import (
    VirtualTagCreate, VirtualTagUpdate, VirtualTagResponse,
    VirtualTagListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/virtual_tags", tags=["Virtual Tags"])


@router.get("", response_model=VirtualTagListResponse)
async def list_virtual_tags(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(VirtualTag.workspace_id == ws.id)
    items, total = await paginated_query(db, VirtualTag, page, limit, filters=filters)
    return VirtualTagListResponse(
        virtual_tags=[VirtualTagResponse.model_validate(vt) for vt in items],
        links=pagination_links("/v2/virtual_tags", page, limit, total),
    )


@router.post("", response_model=VirtualTagResponse, status_code=201)
async def create_virtual_tag(
    payload: VirtualTagCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    vt = VirtualTag(
        token=generate_token("vtag"), workspace_id=ws.id,
        key=payload.key, description=payload.description,
        overridable=payload.overridable, backfill_until=payload.backfill_until,
        values=[v.model_dump() for v in payload.values],
    )
    db.add(vt)
    await db.flush()
    await db.refresh(vt)
    return VirtualTagResponse.model_validate(vt)


@router.get("/{token}", response_model=VirtualTagResponse)
async def get_virtual_tag(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return VirtualTagResponse.model_validate(await get_by_token(db, VirtualTag, token))


@router.put("/{token}", response_model=VirtualTagResponse)
async def update_virtual_tag(
    token: str, payload: VirtualTagUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    vt = await get_by_token(db, VirtualTag, token)
    update = payload.model_dump(exclude_unset=True)
    if "values" in update and update["values"] is not None:
        update["values"] = [v.model_dump() if hasattr(v, "model_dump") else v for v in payload.values]
    for key, val in update.items():
        setattr(vt, key, val)
    await db.flush()
    await db.refresh(vt)
    return VirtualTagResponse.model_validate(vt)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_virtual_tag(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    vt = await get_by_token(db, VirtualTag, token)
    await db.delete(vt)
    await db.flush()
    return MessageResponse(message="Virtual tag deleted")
