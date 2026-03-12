"""Tests for auth middleware, security headers, and edge cases."""

import uuid

import pytest

from app.models import Notification, NotificationType


# --- Security Headers ---


@pytest.mark.anyio
async def test_security_headers_present(client):
    """Every response should include security headers."""
    resp = await client.get("/health")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["x-xss-protection"] == "1; mode=block"
    assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in resp.headers


# --- Auth / RBAC Guards ---


@pytest.mark.anyio
async def test_users_me_requires_auth(test_engine, test_session):
    """Endpoints should reject unauthenticated requests."""
    from httpx import ASGITransport, AsyncClient
    from app.db import get_session
    from app.main import app

    async def _override():
        yield test_session

    app.dependency_overrides[get_session] = _override
    # Don't override get_current_user — let it fail naturally
    app.dependency_overrides.pop(
        __import__("app.auth", fromlist=["get_current_user"]).get_current_user,
        None,
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/users/me")
    assert resp.status_code in (401, 403)
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_admin_endpoint_rejected_for_applicant(client):
    """Applicant (default mock_user) should be forbidden from admin routes."""
    resp = await client.get("/cmhc/sync/logs")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_admin_endpoint_rejected_for_nonprofit(nonprofit_client):
    resp = await nonprofit_client.post("/cmhc/sync", json={})
    assert resp.status_code == 403


# --- Input Validation Edge Cases ---


@pytest.mark.anyio
async def test_create_listing_invalid_rent(admin_client):
    """Rent must be positive."""
    resp = await admin_client.post(
        "/listings/",
        json={
            "title": "Bad Listing",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": -100,
        },
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_listing_missing_required_fields(admin_client):
    resp = await admin_client.post("/listings/", json={"title": "Only Title"})
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_get_listing_invalid_uuid(client):
    resp = await client.get("/listings/not-a-uuid")
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_register_user_invalid_email(client):
    resp = await client.post(
        "/users/register",
        json={"clerk_id": "c_123", "email": "notanemail"},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_listing_search_bad_radius(client):
    """Radius must be > 0 and <= 500."""
    resp = await client.get("/listings/?radius_km=-5&latitude=43.6&longitude=-79.3")
    assert resp.status_code == 422


# --- Pagination Edge Cases ---


@pytest.mark.anyio
async def test_listings_pagination(admin_client):
    """Create several listings, then paginate."""
    for i in range(3):
        await admin_client.post(
            "/listings/",
            json={
                "title": f"Listing {i}",
                "city": "Toronto",
                "province": "ON",
                "rent_amount": 800 + i,
            },
        )

    resp = await admin_client.get("/listings/?limit=2")
    assert len(resp.json()) == 2

    resp = await admin_client.get("/listings/?skip=2&limit=10")
    assert len(resp.json()) == 1


@pytest.mark.anyio
async def test_notifications_pagination(client, test_session, mock_user):
    for i in range(5):
        test_session.add(
            Notification(
                user_id=mock_user.id,
                notification_type=NotificationType.system,
                title=f"N{i}",
                body="body",
            )
        )
    await test_session.commit()

    resp = await client.get("/notifications/?limit=2")
    assert len(resp.json()) == 2

    resp = await client.get("/notifications/?skip=4&limit=10")
    assert len(resp.json()) == 1


# --- Duplicate Registration ---


@pytest.mark.anyio
async def test_register_duplicate_clerk_id(client, test_session, mock_user):
    """Registering with the same clerk_id should fail."""
    test_session.add(mock_user)
    await test_session.commit()

    resp = await client.post(
        "/users/register",
        json={
            "clerk_id": mock_user.clerk_id,
            "email": "other@example.com",
        },
    )
    assert resp.status_code == 409


# --- Health endpoint ---


@pytest.mark.anyio
async def test_health_response_format(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


# --- Match status update invalid ---


@pytest.mark.anyio
async def test_update_match_invalid_status(client):
    resp = await client.patch(
        f"/matches/{uuid.uuid4()}",
        json={"status": "invalid_status_value"},
    )
    assert resp.status_code == 422


# --- OCR service (unit) ---


@pytest.mark.anyio
async def test_ocr_nonexistent_file():
    from app.services.ocr import extract_text_from_file

    result = await extract_text_from_file("/nonexistent/path/file.png")
    assert result is None


@pytest.mark.anyio
async def test_ocr_unsupported_format(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("some content")
    from app.services.ocr import extract_text_from_file

    result = await extract_text_from_file(str(f))
    assert result is None
