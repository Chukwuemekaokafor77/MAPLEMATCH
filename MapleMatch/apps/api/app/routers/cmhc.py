"""CMHC sync endpoints — trigger sync and view logs (admin only)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_role
from app.db import get_session
from app.models import User, UserRole
from app.schemas import CmhcSyncLogRead, CmhcSyncTrigger
from app.services import cmhc_sync

router = APIRouter(prefix="/cmhc", tags=["cmhc"])


@router.post("/sync", response_model=CmhcSyncLogRead, status_code=status.HTTP_201_CREATED)
async def trigger_sync(
    body: CmhcSyncTrigger | None = None,
    user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> object:
    """Trigger a CMHC data sync (admin only)."""
    province = body.province if body else None
    city = body.city if body else None
    return await cmhc_sync.run_sync(session, province=province, city=city)


@router.get("/sync/logs", response_model=list[CmhcSyncLogRead])
async def list_sync_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> list:
    return await cmhc_sync.get_sync_logs(session, skip=skip, limit=limit)


@router.post("/seed", response_model=CmhcSyncLogRead, status_code=status.HTTP_201_CREATED)
async def seed_listings(
    body: CmhcSyncTrigger | None = None,
    user: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> object:
    """Seed listings from all free open-data sources + built-in dataset (admin only).

    Unlike /sync, this endpoint explicitly combines:
      - Toronto Open Data CKAN (no API key)
      - Canada Open Government Portal CKAN (no API key)
      - Built-in curated dataset (75+ listings, all 13 provinces/territories)

    Safe to call repeatedly — existing listings are updated, not duplicated.
    """
    province = body.province if body else None
    city = body.city if body else None
    return await cmhc_sync.run_sync(session, province=province, city=city)
