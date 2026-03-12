"""Notification endpoints — list, mark-read, delete."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import User
from app.schemas import NotificationMarkRead, NotificationRead
from app.services import notifications as notif_svc

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationRead])
async def list_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list:
    return await notif_svc.get_user_notifications(
        session, user.id, unread_only=unread_only, skip=skip, limit=limit
    )


@router.get("/unread-count")
async def unread_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    count = await notif_svc.get_unread_count(session, user.id)
    return {"unread_count": count}


@router.patch("/mark-read")
async def mark_notifications_read(
    body: NotificationMarkRead,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    updated = await notif_svc.mark_read(session, user.id, body.notification_ids)
    return {"updated": updated}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await notif_svc.delete_notification(session, user.id, notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
