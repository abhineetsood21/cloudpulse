"""Team and Access Grant endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.models.v2 import Team, AccessGrant, Workspace
from app.api.v2.schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    AccessGrantCreate, AccessGrantResponse, AccessGrantListResponse,
    MessageResponse,
)
from app.api.v2.helpers import generate_token, get_by_token, paginated_query, pagination_links

router = APIRouter(tags=["Teams"])


# --- Teams ---

@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    workspace_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if workspace_token:
        ws = await get_by_token(db, Workspace, workspace_token)
        filters.append(Team.workspace_id == ws.id)
    items, total = await paginated_query(db, Team, page, limit, filters=filters)
    return TeamListResponse(
        teams=[TeamResponse.model_validate(t) for t in items],
        links=pagination_links("/v2/teams", page, limit, total),
    )


@router.post("/teams", response_model=TeamResponse, status_code=201)
async def create_team(
    payload: TeamCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ws = await get_by_token(db, Workspace, payload.workspace_token)
    team = Team(
        token=generate_token("team"), workspace_id=ws.id,
        name=payload.name, description=payload.description,
    )
    db.add(team)
    await db.flush()
    await db.refresh(team)
    return TeamResponse.model_validate(team)


@router.get("/teams/{token}", response_model=TeamResponse)
async def get_team(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return TeamResponse.model_validate(await get_by_token(db, Team, token))


@router.put("/teams/{token}", response_model=TeamResponse)
async def update_team(token: str, payload: TeamUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = await get_by_token(db, Team, token)
    if payload.name is not None:
        team.name = payload.name
    if payload.description is not None:
        team.description = payload.description
    await db.flush()
    await db.refresh(team)
    return TeamResponse.model_validate(team)


@router.delete("/teams/{token}", response_model=MessageResponse)
async def delete_team(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = await get_by_token(db, Team, token)
    await db.delete(team)
    await db.flush()
    return MessageResponse(message="Team deleted")


# --- Access Grants ---

@router.get("/access_grants", response_model=AccessGrantListResponse)
async def list_access_grants(
    team_token: str | None = None, page: int = 1, limit: int = 25,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    filters = []
    if team_token:
        team = await get_by_token(db, Team, team_token)
        filters.append(AccessGrant.team_id == team.id)
    items, total = await paginated_query(db, AccessGrant, page, limit, filters=filters)
    return AccessGrantListResponse(
        access_grants=[AccessGrantResponse(
            token=ag.token, team_token=ag.team.token if ag.team else None,
            resource_type=ag.resource_type, resource_token=ag.resource_token,
            access_level=ag.access_level, created_at=ag.created_at,
        ) for ag in items],
        links=pagination_links("/v2/access_grants", page, limit, total),
    )


@router.post("/access_grants", response_model=AccessGrantResponse, status_code=201)
async def create_access_grant(
    payload: AccessGrantCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = await get_by_token(db, Team, payload.team_token)
    ag = AccessGrant(
        token=generate_token("ag"), team_id=team.id,
        resource_type=payload.resource_type,
        resource_token=payload.resource_token,
        access_level=payload.access_level,
    )
    db.add(ag)
    await db.flush()
    await db.refresh(ag)
    return AccessGrantResponse(
        token=ag.token, team_token=team.token,
        resource_type=ag.resource_type, resource_token=ag.resource_token,
        access_level=ag.access_level, created_at=ag.created_at,
    )


@router.delete("/access_grants/{token}", response_model=MessageResponse)
async def delete_access_grant(token: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    ag = await get_by_token(db, AccessGrant, token)
    await db.delete(ag)
    await db.flush()
    return MessageResponse(message="Access grant deleted")
