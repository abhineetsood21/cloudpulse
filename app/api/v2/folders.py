"""Folder endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import Folder, Workspace
from app.api.v2.schemas import (
    FolderCreate, FolderUpdate, FolderResponse, FolderListResponse, MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(prefix="/folders", tags=["Folders"])


@router.get("", response_model=FolderListResponse)
async def list_folders(
    workspace_token: str | None = None,
    page: int = 1,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(Folder.workspace_id == ws.id)

    items, total = await paginated_query(db, Folder, page, limit, filters=filters)
    return FolderListResponse(
        folders=[FolderResponse(
            token=f.token, title=f.title,
            workspace_token=f.workspace.token if f.workspace else None,
            parent_folder_token=f.parent.token if f.parent else None,
            created_at=f.created_at,
        ) for f in items],
        links=pagination_links("/v2/folders", page, limit, total),
    )


@router.post("", response_model=FolderResponse, status_code=201)
async def create_folder(
    payload: FolderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    parent_id = None
    if payload.parent_folder_token:
        parent = await get_by_token(db, Folder, payload.parent_folder_token)
        parent_id = parent.id

    folder = Folder(
        token=generate_token("fldr"),
        workspace_id=ws.id,
        parent_folder_id=parent_id,
        title=payload.title,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return FolderResponse(
        token=folder.token, title=folder.title,
        workspace_token=ws.token,
        parent_folder_token=payload.parent_folder_token,
        created_at=folder.created_at,
    )


@router.get("/{token}", response_model=FolderResponse)
async def get_folder(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    f = await get_by_token(db, Folder, token)
    return FolderResponse(
        token=f.token, title=f.title,
        workspace_token=f.workspace.token if f.workspace else None,
        parent_folder_token=f.parent.token if f.parent else None,
        created_at=f.created_at,
    )


@router.put("/{token}", response_model=FolderResponse)
async def update_folder(
    token: str, payload: FolderUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    f = await get_by_token(db, Folder, token)
    if payload.title is not None:
        f.title = payload.title
    if payload.parent_folder_token is not None:
        parent = await get_by_token(db, Folder, payload.parent_folder_token)
        f.parent_folder_id = parent.id
    await db.flush()
    await db.refresh(f)
    return FolderResponse(
        token=f.token, title=f.title,
        workspace_token=f.workspace.token if f.workspace else None,
        parent_folder_token=f.parent.token if f.parent else None,
        created_at=f.created_at,
    )


@router.delete("/{token}", response_model=MessageResponse)
async def delete_folder(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    f = await get_by_token(db, Folder, token)
    await db.delete(f)
    await db.flush()
    return MessageResponse(message="Folder deleted")
