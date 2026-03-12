"""Tests for CMHC sync endpoints and service."""

import pytest


@pytest.mark.anyio
async def test_cmhc_sync_requires_admin(client):
    """Regular users cannot trigger a sync."""
    resp = await client.post("/cmhc/sync", json={})
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_cmhc_sync_logs_requires_admin(client):
    resp = await client.get("/cmhc/sync/logs")
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_cmhc_sync_success(admin_client):
    """Admin can trigger CMHC sync with sample data (no API key configured)."""
    resp = await admin_client.post("/cmhc/sync", json={})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["records_fetched"] >= 1
    assert data["records_created"] >= 1


@pytest.mark.anyio
async def test_cmhc_sync_with_province_filter(admin_client):
    resp = await admin_client.post("/cmhc/sync", json={"province": "ON"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"


@pytest.mark.anyio
async def test_cmhc_sync_with_city_filter(admin_client):
    resp = await admin_client.post("/cmhc/sync", json={"city": "Toronto"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["records_fetched"] >= 1


@pytest.mark.anyio
async def test_cmhc_sync_logs_empty(admin_client):
    resp = await admin_client.get("/cmhc/sync/logs")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_cmhc_sync_logs_after_sync(admin_client):
    """After a sync, the log appears in the list."""
    await admin_client.post("/cmhc/sync", json={})
    resp = await admin_client.get("/cmhc/sync/logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) >= 1
    assert logs[0]["source"] == "cmhc-open-data"


@pytest.mark.anyio
async def test_cmhc_sync_idempotent(admin_client):
    """Running sync twice should update rather than duplicate listings."""
    resp1 = await admin_client.post("/cmhc/sync", json={})
    data1 = resp1.json()

    resp2 = await admin_client.post("/cmhc/sync", json={})
    data2 = resp2.json()

    # Second run should update (not re-create) the same listings
    assert data2["records_created"] == 0
    assert data2["records_updated"] == data1["records_created"]


@pytest.mark.anyio
async def test_cmhc_sync_creates_listings(admin_client):
    """Synced listings should appear in the listings endpoint."""
    await admin_client.post("/cmhc/sync", json={})
    resp = await admin_client.get("/listings/")
    assert resp.status_code == 200
    listings = resp.json()
    assert len(listings) >= 1
    # At least one listing from sample data
    titles = [l["title"] for l in listings]
    assert any("Toronto" in t or "Regent Park" in t for t in titles)


@pytest.mark.anyio
async def test_cmhc_sample_data_filter_no_match(admin_client):
    """Province with no sample data should still succeed with 0 records."""
    resp = await admin_client.post("/cmhc/sync", json={"province": "NL"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["records_fetched"] == 0
    assert data["records_created"] == 0
