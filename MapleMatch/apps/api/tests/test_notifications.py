"""Tests for notification endpoints and service."""

import uuid

import pytest

from app.models import Notification, NotificationType


@pytest.mark.anyio
async def test_list_notifications_empty(client):
    resp = await client.get("/notifications/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_unread_count_empty(client):
    resp = await client.get("/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json() == {"unread_count": 0}


@pytest.mark.anyio
async def test_create_and_list_notification(client, test_session, mock_user):
    """Insert a notification directly and verify it appears via the endpoint."""
    notif = Notification(
        user_id=mock_user.id,
        notification_type=NotificationType.match_found,
        title="Test Match",
        body="You matched with Test Listing.",
    )
    test_session.add(notif)
    await test_session.commit()

    resp = await client.get("/notifications/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Match"
    assert data[0]["is_read"] is False


@pytest.mark.anyio
async def test_unread_count_after_insert(client, test_session, mock_user):
    for i in range(3):
        test_session.add(
            Notification(
                user_id=mock_user.id,
                notification_type=NotificationType.system,
                title=f"Notification {i}",
                body="body",
            )
        )
    await test_session.commit()

    resp = await client.get("/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 3


@pytest.mark.anyio
async def test_mark_read(client, test_session, mock_user):
    notif = Notification(
        user_id=mock_user.id,
        notification_type=NotificationType.listing_update,
        title="Update",
        body="Listing updated.",
    )
    test_session.add(notif)
    await test_session.commit()
    await test_session.refresh(notif)

    resp = await client.patch(
        "/notifications/mark-read",
        json={"notification_ids": [str(notif.id)]},
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] == 1

    # Unread count should now be 0
    resp = await client.get("/notifications/unread-count")
    assert resp.json()["unread_count"] == 0


@pytest.mark.anyio
async def test_delete_notification(client, test_session, mock_user):
    notif = Notification(
        user_id=mock_user.id,
        notification_type=NotificationType.document_reviewed,
        title="Doc Reviewed",
        body="Your document was approved.",
    )
    test_session.add(notif)
    await test_session.commit()
    await test_session.refresh(notif)

    resp = await client.delete(f"/notifications/{notif.id}")
    assert resp.status_code == 204

    resp = await client.get("/notifications/")
    assert resp.json() == []


@pytest.mark.anyio
async def test_delete_notification_not_found(client):
    resp = await client.delete(f"/notifications/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_filter_unread_only(client, test_session, mock_user):
    """Ensure unread_only filter works."""
    n1 = Notification(
        user_id=mock_user.id,
        notification_type=NotificationType.system,
        title="Read",
        body="Already read.",
        is_read=True,
    )
    n2 = Notification(
        user_id=mock_user.id,
        notification_type=NotificationType.system,
        title="Unread",
        body="Still unread.",
    )
    test_session.add_all([n1, n2])
    await test_session.commit()

    resp = await client.get("/notifications/?unread_only=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Unread"


@pytest.mark.anyio
async def test_notification_isolation(client, test_session, mock_user):
    """Notifications from other users should not appear."""
    other_user_id = uuid.uuid4()
    test_session.add(
        Notification(
            user_id=other_user_id,
            notification_type=NotificationType.match_found,
            title="Other User Match",
            body="This belongs to another user.",
        )
    )
    await test_session.commit()

    resp = await client.get("/notifications/")
    assert resp.json() == []


@pytest.mark.anyio
async def test_notification_service_helpers(test_session, mock_user):
    """Test convenience notification helpers directly."""
    from app.services.notifications import (
        notify_match_found,
        notify_document_reviewed,
        notify_listing_update,
    )

    n1 = await notify_match_found(test_session, mock_user.id, "Great Listing", uuid.uuid4())
    assert n1.notification_type == NotificationType.match_found

    n2 = await notify_document_reviewed(test_session, mock_user.id, "approved", uuid.uuid4())
    assert n2.notification_type == NotificationType.document_reviewed

    n3 = await notify_listing_update(test_session, mock_user.id, "Updated Listing", uuid.uuid4())
    assert n3.notification_type == NotificationType.listing_update
