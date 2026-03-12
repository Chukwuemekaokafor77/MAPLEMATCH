"""Notification service — create, query, and manage user notifications."""

import uuid
import smtplib
from email.message import EmailMessage
from app.config import settings
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models import Notification, NotificationType


async def create_notification(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: NotificationType,
    title: str,
    body: str,
    related_id: uuid.UUID | None = None,
) -> Notification:
    """Persist a new notification for a user."""
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        related_id=related_id,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    # Send email if SMTP is configured and user email is available
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        try:
            # Fetch user email (requires user lookup, not available in args)
            from app.models import User
            user = await session.get(User, user_id)
            if user and user.email:
                msg = EmailMessage()
                msg["Subject"] = f"MapleMatch Notification: {title}"
                msg["From"] = settings.notification_from_email
                msg["To"] = user.email
                msg.set_content(body)
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                    server.starttls()
                    server.login(settings.smtp_user, settings.smtp_password)
                    server.send_message(msg)
        except Exception as e:
            # Log error, but don't block notification creation
            print(f"[Email Notification Error] {e}")

    return notification


async def get_user_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> list[Notification]:
    """Return notifications for a user, newest first."""
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)  # noqa: E712
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_unread_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Return the number of unread notifications."""
    from sqlalchemy import func

    stmt = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def mark_read(
    session: AsyncSession,
    user_id: uuid.UUID,
    notification_ids: list[uuid.UUID],
) -> int:
    """Mark specific notifications as read. Returns count updated."""
    from sqlalchemy import update

    stmt = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids),  # type: ignore[union-attr]
            Notification.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount  # type: ignore[return-value]


async def delete_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
) -> bool:
    """Delete a single notification owned by the user. Returns True if deleted."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )
    result = await session.execute(stmt)
    notification = result.scalar_one_or_none()
    if notification is None:
        return False
    await session.delete(notification)
    await session.commit()
    return True


# --- Convenience helpers called by other services ---


async def notify_match_found(
    session: AsyncSession,
    user_id: uuid.UUID,
    listing_title: str,
    match_id: uuid.UUID,
) -> Notification:
    return await create_notification(
        session,
        user_id=user_id,
        notification_type=NotificationType.match_found,
        title="New Housing Match",
        body=f'You matched with "{listing_title}". Review your matches to learn more.',
        related_id=match_id,
    )


async def notify_document_reviewed(
    session: AsyncSession,
    user_id: uuid.UUID,
    doc_status: str,
    document_id: uuid.UUID,
) -> Notification:
    return await create_notification(
        session,
        user_id=user_id,
        notification_type=NotificationType.document_reviewed,
        title="Document Review Update",
        body=f"Your document has been reviewed. Status: {doc_status}.",
        related_id=document_id,
    )


async def notify_listing_update(
    session: AsyncSession,
    user_id: uuid.UUID,
    listing_title: str,
    listing_id: uuid.UUID,
) -> Notification:
    return await create_notification(
        session,
        user_id=user_id,
        notification_type=NotificationType.listing_update,
        title="Listing Updated",
        body=f'The listing "{listing_title}" has been updated.',
        related_id=listing_id,
    )
