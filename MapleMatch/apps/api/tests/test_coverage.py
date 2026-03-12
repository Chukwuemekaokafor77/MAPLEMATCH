"""Additional coverage tests — direct service calls and more endpoint paths."""

import uuid
from datetime import UTC, datetime

import pytest
from sqlmodel import select

from app.models import (
    Document,
    DocumentStatus,
    DocumentType,
    EligibilityProfile,
    Listing,
    ListingStatus,
    Match,
    MatchStatus,
    PriorityGroup,
    User,
    UserRole,
)


# ===== Direct service-level tests =====


@pytest.mark.anyio
async def test_eligibility_all_paths(test_session, mock_user):
    """Hit every branch in the eligibility engine."""
    from app.services.eligibility import check_eligibility

    profile = EligibilityProfile(
        user_id=mock_user.id,
        annual_income=40000,
        household_size=3,
        priority_group=PriorityGroup.newcomer,
        province="ON",
        city="Toronto",
        latitude=43.65,
        longitude=-79.38,
        max_rent=1200,
        needs_accessible_unit=True,
        consent_given=True,
    )

    # Listing with all restrictions
    listing = Listing(
        title="Restricted Listing",
        city="Toronto",
        province="ON",
        rent_amount=900,
        max_income=60000,
        min_household_size=2,
        max_household_size=5,
        is_rgi=True,
        is_accessible=True,
        priority_groups="newcomer,senior",
        latitude=43.66,
        longitude=-79.37,
        estimated_wait_days=200,
    )
    result = check_eligibility(profile, listing)
    assert result.eligible is True
    assert result.score > 0

    # Listing where income is too high
    listing2 = Listing(
        title="Low Income Only",
        city="Toronto",
        province="ON",
        rent_amount=500,
        max_income=30000,
    )
    result2 = check_eligibility(profile, listing2)
    assert result2.eligible is False

    # Listing where household is too small
    listing3 = Listing(
        title="Large Family Only",
        city="Toronto",
        province="ON",
        rent_amount=800,
        min_household_size=5,
    )
    result3 = check_eligibility(profile, listing3)
    assert result3.eligible is False

    # Listing where household too large
    listing4 = Listing(
        title="Singles Only",
        city="Toronto",
        province="ON",
        rent_amount=600,
        max_household_size=1,
    )
    result4 = check_eligibility(profile, listing4)
    assert result4.eligible is False

    # Profile without income on RGI listing
    no_income_profile = EligibilityProfile(
        user_id=mock_user.id,
        annual_income=None,
        household_size=2,
        province="ON",
    )
    rgi_listing = Listing(
        title="RGI Only",
        city="Toronto",
        province="ON",
        rent_amount=500,
        is_rgi=True,
        max_income=50000,
    )
    result5 = check_eligibility(no_income_profile, rgi_listing)
    assert result5.eligible is False

    # Rent over budget
    over_budget = Listing(
        title="Expensive",
        city="Toronto",
        province="ON",
        rent_amount=2000,
    )
    result6 = check_eligibility(profile, over_budget)
    assert len(result6.reasons) > 0

    # Accessibility mismatch but not disqualifying
    not_accessible = Listing(
        title="Stairs Only",
        city="Toronto",
        province="ON",
        rent_amount=800,
        is_accessible=False,
    )
    result7 = check_eligibility(profile, not_accessible)
    assert any("accessible" in r.lower() for r in result7.reasons)

    # Listing with no restrictions at all
    open_listing = Listing(
        title="Open",
        city="Vancouver",
        province="BC",
        rent_amount=1000,
    )
    result8 = check_eligibility(profile, open_listing)
    assert result8.eligible is True


@pytest.mark.anyio
async def test_recommender_all_branches(test_session, mock_user):
    """Hit branches in the hybrid recommender."""
    from app.services.recommender import hybrid_match, batch_hybrid_match

    profile = EligibilityProfile(
        user_id=mock_user.id,
        annual_income=45000,
        household_size=2,
        priority_group=PriorityGroup.none,
        province="ON",
        city="Toronto",
        max_rent=1500,
        needs_accessible_unit=False,
        consent_given=True,
    )

    listing = Listing(
        id=uuid.uuid4(),
        title="Toronto Affordable",
        description="Nice 2-bed in downtown Toronto with great transit access.",
        city="Toronto",
        province="ON",
        rent_amount=1000,
        bedrooms=2,
        bathrooms=1,
        is_rgi=False,
        is_accessible=False,
        max_income=60000,
    )

    # Rules only
    r1 = hybrid_match(profile, listing, use_semantic=False, use_ml=False)
    assert r1.eligible is True
    assert r1.semantic_score == 0.0
    assert r1.ml_score == 0.0

    # With ML features
    r2 = hybrid_match(profile, listing, use_semantic=False, use_ml=True)
    assert r2.ml_score >= 0.0

    # Batch matching
    listings = [listing]
    batch = batch_hybrid_match(profile, listings, use_semantic=False, use_ml=False)
    assert len(batch) == 1

    # Ineligible listing
    bad_listing = Listing(
        id=uuid.uuid4(),
        title="Too Expensive",
        city="Toronto",
        province="ON",
        rent_amount=500,
        max_income=10000,  # income cap too low
    )
    r3 = hybrid_match(profile, bad_listing, use_semantic=False, use_ml=False)
    assert r3.eligible is False


@pytest.mark.anyio
async def test_wait_time_all_branches():
    """Hit branches in wait-time prediction."""
    from app.services.wait_time import predict_wait_time

    profile = EligibilityProfile(
        user_id=uuid.uuid4(),
        annual_income=35000,
        household_size=4,
        priority_group=PriorityGroup.senior,
        province="BC",
        max_rent=1200,
        needs_accessible_unit=True,
    )

    # With custom wait days
    listing = Listing(
        id=uuid.uuid4(),
        title="BC Housing",
        city="Vancouver",
        province="BC",
        rent_amount=1000,
        is_rgi=True,
        is_accessible=True,
        estimated_wait_days=365,
        bedrooms=3,
    )
    wt = predict_wait_time(profile, listing)
    assert wt.estimated_days > 0
    assert wt.lower_bound_days < wt.upper_bound_days
    assert wt.confidence > 0

    # Without custom wait days
    listing2 = Listing(
        id=uuid.uuid4(),
        title="AB Housing",
        city="Calgary",
        province="AB",
        rent_amount=800,
        is_rgi=False,
        bedrooms=1,
    )
    wt2 = predict_wait_time(profile, listing2)
    assert wt2.estimated_days > 0

    # Different provinces for coverage
    for prov in ["ON", "QC", "MB", "NS", "SK"]:
        p = EligibilityProfile(
            user_id=uuid.uuid4(),
            province=prov,
            household_size=1,
        )
        l = Listing(
            id=uuid.uuid4(), title="Test", city="Test",
            province=prov, rent_amount=500,
        )
        wt3 = predict_wait_time(p, l)
        assert wt3.estimated_days >= 0


@pytest.mark.anyio
async def test_embeddings_text_generation():
    """Test profile and listing text generation."""
    from app.services.embeddings import profile_to_text, listing_to_text

    profile = EligibilityProfile(
        user_id=uuid.uuid4(),
        annual_income=50000,
        household_size=3,
        priority_group=PriorityGroup.veteran,
        province="ON",
        city="Ottawa",
        max_rent=1400,
        needs_accessible_unit=True,
    )
    text = profile_to_text(profile)
    assert "veteran" in text.lower()
    assert "Ottawa" in text
    assert "accessible" in text.lower()

    listing = Listing(
        id=uuid.uuid4(),
        title="Test Listing",
        description="Great unit near transit",
        city="Ottawa",
        province="ON",
        rent_amount=1200,
        bedrooms=3,
        is_rgi=True,
        is_accessible=True,
        amenities="parking,laundry",
    )
    text2 = listing_to_text(listing)
    assert "Ottawa" in text2
    assert "parking" in text2.lower() or "laundry" in text2.lower()


@pytest.mark.anyio
async def test_cmhc_sync_service_direct(test_session):
    """Test CMHC sync service directly."""
    from app.services.cmhc_sync import run_sync, get_sync_logs

    log = await run_sync(test_session, province="ON")
    assert log.status == "success"
    assert log.records_fetched >= 1
    assert log.completed_at is not None

    logs = await get_sync_logs(test_session)
    assert len(logs) >= 1


@pytest.mark.anyio
async def test_notification_service_full(test_session, mock_user):
    """Test all notification service functions."""
    from app.services.notifications import (
        create_notification,
        get_user_notifications,
        get_unread_count,
        mark_read,
        delete_notification,
    )
    from app.models import NotificationType

    n = await create_notification(
        test_session,
        user_id=mock_user.id,
        notification_type=NotificationType.system,
        title="System Alert",
        body="Platform update available.",
    )
    assert n.id is not None

    notifs = await get_user_notifications(test_session, mock_user.id)
    assert len(notifs) == 1

    count = await get_unread_count(test_session, mock_user.id)
    assert count == 1

    updated = await mark_read(test_session, mock_user.id, [n.id])
    assert updated == 1

    count = await get_unread_count(test_session, mock_user.id)
    assert count == 0

    deleted = await delete_notification(test_session, mock_user.id, n.id)
    assert deleted is True

    deleted2 = await delete_notification(test_session, mock_user.id, uuid.uuid4())
    assert deleted2 is False


# ===== Additional HTTP endpoint tests =====


@pytest.mark.anyio
async def test_update_eligibility_profile(client, test_session, mock_user):
    """Create and then update eligibility profile."""
    # Create first
    resp = await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "consent_given": True,
        },
    )
    assert resp.status_code == 201

    # Update
    resp = await client.patch(
        "/users/me/eligibility",
        json={"annual_income": 45000, "max_rent": 1500},
    )
    assert resp.status_code == 200
    assert resp.json()["annual_income"] == 45000
    assert resp.json()["max_rent"] == 1500


@pytest.mark.anyio
async def test_create_profile_duplicate(client, test_session, mock_user):
    """Creating eligibility profile twice should return 409."""
    payload = {"annual_income": 30000, "household_size": 1, "province": "BC"}
    resp = await client.post("/users/me/eligibility", json=payload)
    assert resp.status_code == 201

    resp2 = await client.post("/users/me/eligibility", json=payload)
    assert resp2.status_code == 409


@pytest.mark.anyio
async def test_update_profile_not_found(client):
    """Updating non-existent profile should return 404."""
    resp = await client.patch(
        "/users/me/eligibility",
        json={"annual_income": 50000},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_full_matching_flow(client, admin_client, test_session, mock_user):
    """End-to-end: create profile + listing, generate matches, update status."""
    # Create eligibility profile
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "consent_given": True,
        },
    )

    # Create listing as admin
    await admin_client.post(
        "/listings/",
        json={
            "title": "Match Test Listing",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 900,
            "max_income": 60000,
        },
    )

    # Generate matches
    resp = await client.post("/matches/generate")
    assert resp.status_code == 201
    matches = resp.json()
    assert len(matches) >= 1

    # Get matches
    resp = await client.get("/matches")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Update match status
    match_id = matches[0]["id"]
    resp = await client.patch(
        f"/matches/{match_id}",
        json={"status": "accepted"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


@pytest.mark.anyio
async def test_check_eligibility_endpoint_extended(client, admin_client, test_session, mock_user):
    """Test eligibility check endpoint with profile."""
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 35000,
            "household_size": 2,
            "province": "ON",
        },
    )

    listing_resp = await admin_client.post(
        "/listings/",
        json={
            "title": "Eligibility Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 800,
            "max_income": 50000,
        },
    )
    listing_id = listing_resp.json()["id"]

    resp = await client.post(
        "/eligibility/check",
        json={"listing_id": listing_id},
    )
    assert resp.status_code == 200
    assert resp.json()["eligible"] is True


@pytest.mark.anyio
async def test_smart_match_endpoint_extended(client, admin_client, test_session, mock_user):
    """Test smart match with listings present."""
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
            "city": "Toronto",
            "consent_given": True,
        },
    )

    await admin_client.post(
        "/listings/",
        json={
            "title": "Smart Match Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 950,
            "max_income": 60000,
        },
    )

    resp = await client.post("/matches/smart?use_semantic=false&use_ml=false")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) >= 1
    assert "factors" in results[0]


@pytest.mark.anyio
async def test_smart_match_and_save_extended(client, admin_client, test_session, mock_user):
    """Test smart match and save endpoint."""
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
            "consent_given": True,
        },
    )

    await admin_client.post(
        "/listings/",
        json={
            "title": "Save Match Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 900,
            "max_income": 60000,
        },
    )

    resp = await client.post("/matches/smart/save?use_semantic=false&use_ml=false")
    assert resp.status_code == 201
    matches = resp.json()
    assert len(matches) >= 1


@pytest.mark.anyio
async def test_wait_time_endpoint_extended(client, admin_client, test_session, mock_user):
    """Test wait-time estimate endpoint."""
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
        },
    )

    listing_resp = await admin_client.post(
        "/listings/",
        json={
            "title": "Wait Time Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 800,
        },
    )
    listing_id = listing_resp.json()["id"]

    resp = await client.post(
        "/wait-time/estimate",
        json={"listing_id": listing_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "estimated_days" in data
    assert "confidence" in data


@pytest.mark.anyio
async def test_listing_update_by_nonprofit(nonprofit_client, test_session, mock_nonprofit):
    """Nonprofit can update its own listing."""
    resp = await nonprofit_client.post(
        "/listings/",
        json={
            "title": "NP Listing",
            "city": "Ottawa",
            "province": "ON",
            "rent_amount": 700,
        },
    )
    assert resp.status_code == 201
    listing_id = resp.json()["id"]

    resp = await nonprofit_client.patch(
        f"/listings/{listing_id}",
        json={"title": "Updated NP Listing", "rent_amount": 750},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated NP Listing"


@pytest.mark.anyio
async def test_listing_search_filters(admin_client):
    """Test all individual search filters."""
    await admin_client.post(
        "/listings/",
        json={
            "title": "Filter Test A",
            "city": "Montreal",
            "province": "QC",
            "rent_amount": 600,
            "bedrooms": 2,
            "is_accessible": True,
            "is_rgi": True,
        },
    )
    await admin_client.post(
        "/listings/",
        json={
            "title": "Filter Test B",
            "city": "Vancouver",
            "province": "BC",
            "rent_amount": 1200,
            "bedrooms": 1,
            "is_accessible": False,
            "is_rgi": False,
        },
    )

    # Province filter
    resp = await admin_client.get("/listings/?province=QC")
    assert all(l["province"] == "QC" for l in resp.json())

    # Min rent filter
    resp = await admin_client.get("/listings/?min_rent=1000")
    assert all(l["rent_amount"] >= 1000 for l in resp.json())

    # Bedrooms filter
    resp = await admin_client.get("/listings/?bedrooms=2")
    assert all(l["bedrooms"] == 2 for l in resp.json())

    # Boolean filters
    resp = await admin_client.get("/listings/?is_accessible=true")
    assert all(l["is_accessible"] for l in resp.json())

    resp = await admin_client.get("/listings/?is_rgi=true")
    assert all(l["is_rgi"] for l in resp.json())


@pytest.mark.anyio
async def test_match_not_found(client):
    resp = await client.patch(
        f"/matches/{uuid.uuid4()}",
        json={"status": "accepted"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_listing_update_not_found(admin_client):
    resp = await admin_client.patch(
        f"/listings/{uuid.uuid4()}",
        json={"title": "Nope"},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_listing_delete_not_found(admin_client):
    resp = await admin_client.delete(f"/listings/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_document_not_found(client):
    resp = await client.get(f"/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_document_delete_not_found(client):
    resp = await client.delete(f"/documents/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_matches_status_filter(client, admin_client, test_session, mock_user):
    """Filter matches by status."""
    await client.post(
        "/users/me/eligibility",
        json={
            "annual_income": 40000,
            "household_size": 2,
            "province": "ON",
            "consent_given": True,
        },
    )
    await admin_client.post(
        "/listings/",
        json={
            "title": "Status Filter Test",
            "city": "Toronto",
            "province": "ON",
            "rent_amount": 800,
            "max_income": 60000,
        },
    )

    await client.post("/matches/generate")

    resp = await client.get("/matches?status_filter=pending")
    assert resp.status_code == 200
    assert all(m["status"] == "pending" for m in resp.json())
