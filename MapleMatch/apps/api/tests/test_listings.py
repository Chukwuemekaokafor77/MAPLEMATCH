"""Tests for listings CRUD and search endpoints."""

import pytest
from httpx import AsyncClient


LISTING_PAYLOAD = {
    "title": "Affordable Studio Downtown",
    "description": "Cozy studio near transit",
    "address": "100 Queen St W",
    "city": "Toronto",
    "province": "ON",
    "postal_code": "M5H 2N2",
    "latitude": 43.6532,
    "longitude": -79.3832,
    "rent_amount": 1200.0,
    "is_rgi": False,
    "bedrooms": 0,
    "bathrooms": 1,
    "is_accessible": True,
    "max_income": 50000.0,
    "min_household_size": 1,
    "max_household_size": 2,
    "priority_groups": "newcomer,senior",
}


@pytest.mark.anyio
async def test_create_listing_as_admin(admin_client: AsyncClient):
    response = await admin_client.post("/listings/", json=LISTING_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Affordable Studio Downtown"
    assert data["city"] == "Toronto"
    assert data["rent_amount"] == 1200.0
    assert data["status"] == "active"


@pytest.mark.anyio
async def test_create_listing_as_nonprofit(nonprofit_client: AsyncClient):
    response = await nonprofit_client.post("/listings/", json=LISTING_PAYLOAD)
    assert response.status_code == 201


@pytest.mark.anyio
async def test_create_listing_forbidden_for_applicant(client: AsyncClient):
    response = await client.post("/listings/", json=LISTING_PAYLOAD)
    assert response.status_code == 403


@pytest.mark.anyio
async def test_list_listings(admin_client: AsyncClient):
    # Create a listing first
    await admin_client.post("/listings/", json=LISTING_PAYLOAD)

    response = await admin_client.get("/listings/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Affordable Studio Downtown"


@pytest.mark.anyio
async def test_search_listings_by_city(admin_client: AsyncClient):
    await admin_client.post("/listings/", json=LISTING_PAYLOAD)
    # Search by city
    response = await admin_client.get("/listings/", params={"city": "Toronto"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    # Search different city
    response = await admin_client.get("/listings/", params={"city": "Vancouver"})
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.anyio
async def test_search_listings_by_rent(admin_client: AsyncClient):
    await admin_client.post("/listings/", json=LISTING_PAYLOAD)

    response = await admin_client.get(
        "/listings/", params={"min_rent": 1000, "max_rent": 1500}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1

    response = await admin_client.get(
        "/listings/", params={"max_rent": 500}
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.anyio
async def test_search_listings_by_accessibility(admin_client: AsyncClient):
    await admin_client.post("/listings/", json=LISTING_PAYLOAD)

    response = await admin_client.get(
        "/listings/", params={"is_accessible": True}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1

    response = await admin_client.get(
        "/listings/", params={"is_accessible": False}
    )
    assert response.status_code == 200
    # The fixture listing is accessible, so searching for non-accessible should exclude it
    assert all(not item["is_accessible"] for item in response.json())


@pytest.mark.anyio
async def test_search_listings_geospatial(admin_client: AsyncClient):
    await admin_client.post("/listings/", json=LISTING_PAYLOAD)

    # Within 10km radius of downtown Toronto
    response = await admin_client.get(
        "/listings/",
        params={"latitude": 43.65, "longitude": -79.38, "radius_km": 10},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Far away — Ottawa coordinates
    response = await admin_client.get(
        "/listings/",
        params={"latitude": 45.42, "longitude": -75.69, "radius_km": 10},
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.anyio
async def test_get_listing_by_id(admin_client: AsyncClient):
    create_resp = await admin_client.post("/listings/", json=LISTING_PAYLOAD)
    listing_id = create_resp.json()["id"]

    response = await admin_client.get(f"/listings/{listing_id}")
    assert response.status_code == 200
    assert response.json()["id"] == listing_id


@pytest.mark.anyio
async def test_get_listing_not_found(admin_client: AsyncClient):
    response = await admin_client.get(
        "/listings/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_listing(admin_client: AsyncClient):
    create_resp = await admin_client.post("/listings/", json=LISTING_PAYLOAD)
    listing_id = create_resp.json()["id"]

    response = await admin_client.patch(
        f"/listings/{listing_id}",
        json={"rent_amount": 1100.0, "title": "Updated Studio"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rent_amount"] == 1100.0
    assert data["title"] == "Updated Studio"


@pytest.mark.anyio
async def test_delete_listing_soft(admin_client: AsyncClient):
    create_resp = await admin_client.post("/listings/", json=LISTING_PAYLOAD)
    listing_id = create_resp.json()["id"]

    response = await admin_client.delete(f"/listings/{listing_id}")
    assert response.status_code == 204

    # Verify it's inactive (not returned in active search)
    response = await admin_client.get("/listings/")
    listing_ids = [item["id"] for item in response.json()]
    assert listing_id not in listing_ids


@pytest.mark.anyio
async def test_delete_listing_forbidden_for_applicant(client: AsyncClient):
    # Applicants can't delete listings
    response = await client.delete(
        "/listings/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 403
