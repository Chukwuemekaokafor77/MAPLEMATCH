"""Tests for document upload, listing, and review endpoints."""

import pytest
from httpx import AsyncClient


DOC_PAYLOAD = {
    "doc_type": "income_proof",
    "file_url": "https://storage.example.com/docs/income_2025.pdf",
    "original_filename": "income_2025.pdf",
}


@pytest.mark.anyio
async def test_upload_document(client: AsyncClient):
    response = await client.post("/documents/", json=DOC_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["doc_type"] == "income_proof"
    assert data["status"] == "pending"
    assert data["original_filename"] == "income_2025.pdf"


@pytest.mark.anyio
async def test_list_my_documents(client: AsyncClient):
    await client.post("/documents/", json=DOC_PAYLOAD)
    response = await client.get("/documents/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.anyio
async def test_get_document(client: AsyncClient):
    create_resp = await client.post("/documents/", json=DOC_PAYLOAD)
    doc_id = create_resp.json()["id"]

    response = await client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json()["id"] == doc_id


@pytest.mark.anyio
async def test_get_document_not_found(client: AsyncClient):
    response = await client.get(
        "/documents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_pending_document(client: AsyncClient):
    create_resp = await client.post("/documents/", json=DOC_PAYLOAD)
    doc_id = create_resp.json()["id"]

    response = await client.delete(f"/documents/{doc_id}")
    assert response.status_code == 204


@pytest.mark.anyio
async def test_list_pending_documents_admin(admin_client: AsyncClient):
    response = await admin_client.get("/documents/review/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_list_pending_documents_forbidden_for_applicant(
    client: AsyncClient,
):
    response = await client.get("/documents/review/pending")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_review_document_approve(
    client: AsyncClient, admin_client: AsyncClient
):
    # Create doc as regular user
    create_resp = await client.post("/documents/", json=DOC_PAYLOAD)
    doc_id = create_resp.json()["id"]

    # Admin approves
    response = await admin_client.patch(
        f"/documents/{doc_id}/review",
        json={"status": "verified", "reviewer_notes": "Looks good"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"
    assert data["reviewer_notes"] == "Looks good"


@pytest.mark.anyio
async def test_review_document_reject(
    client: AsyncClient, admin_client: AsyncClient
):
    create_resp = await client.post("/documents/", json=DOC_PAYLOAD)
    doc_id = create_resp.json()["id"]

    response = await admin_client.patch(
        f"/documents/{doc_id}/review",
        json={"status": "rejected", "reviewer_notes": "Illegible scan"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


@pytest.mark.anyio
async def test_cannot_delete_verified_document(
    client: AsyncClient, admin_client: AsyncClient
):
    create_resp = await client.post("/documents/", json=DOC_PAYLOAD)
    doc_id = create_resp.json()["id"]

    # Admin verifies
    await admin_client.patch(
        f"/documents/{doc_id}/review",
        json={"status": "verified"},
    )

    # User tries to delete — should fail
    response = await client.delete(f"/documents/{doc_id}")
    assert response.status_code == 400
