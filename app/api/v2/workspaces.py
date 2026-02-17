"""Workspace endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import Workspace
from app.api.v2.schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    page: int = 1,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await paginated_query(
        db, Workspace, page, limit,
        filters=[Workspace.created_by == current_user.id],
    )
    return WorkspaceListResponse(
        workspaces=[WorkspaceResponse.model_validate(w) for w in items],
        links=pagination_links("/v2/workspaces", page, limit, total),
    )


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = Workspace(
        name=payload.name,
        token=generate_token("ws"),
        created_by=current_user.id,
    )
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)
    return WorkspaceResponse.model_validate(workspace)


@router.get("/{token}", response_model=WorkspaceResponse)
async def get_workspace(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, token)
    return WorkspaceResponse.model_validate(ws)


@router.put("/{token}", response_model=WorkspaceResponse)
async def update_workspace(
    token: str,
    payload: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, token)
    if payload.name is not None:
        ws.name = payload.name
    await db.flush()
    await db.refresh(ws)
    return WorkspaceResponse.model_validate(ws)


@router.delete("/{token}", response_model=MessageResponse)
async def delete_workspace(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, token)
    await db.delete(ws)
    await db.flush()
    return MessageResponse(message="Workspace deleted")
