"""Document upload and management endpoints."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth import get_current_user, require_role
from app.db import get_session
from app.models import Document, DocumentStatus, User, UserRole
from app.schemas import DocumentCreate, DocumentRead, DocumentReview

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    data: DocumentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Register a document for the current user.

    The file_url should point to the already-uploaded file
    (e.g. from Uploadcare, Cloudinary, or S3).
    OCR processing runs asynchronously via background task.
    """
    document = Document(
        user_id=user.id,
        doc_type=data.doc_type,
        file_url=data.file_url,
        original_filename=data.original_filename,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


@router.get("/", response_model=list[DocumentRead])
async def list_my_documents(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    """List all documents for the current user."""
    result = await session.execute(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())  # type: ignore[union-attr]
    )
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Get a specific document. Users can only see their own; admins can see any."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a document. Users can only delete their own pending documents."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    if document.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    if document.status != DocumentStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending documents can be deleted",
        )
    await session.delete(document)
    await session.commit()


# === Admin document review ===


@router.get("/review/pending", response_model=list[DocumentRead])
async def list_pending_documents(
    skip: int = 0,
    limit: int = 50,
    _admin: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> list[Document]:
    """List all pending documents for admin review."""
    result = await session.execute(
        select(Document)
        .where(Document.status == DocumentStatus.pending)
        .order_by(Document.created_at)  # type: ignore[union-attr]
        .offset(skip)
        .limit(min(limit, 100))
    )
    return list(result.scalars().all())


@router.patch("/{document_id}/review", response_model=DocumentRead)
async def review_document(
    document_id: uuid.UUID,
    data: DocumentReview,
    _admin: User = Depends(require_role(UserRole.admin)),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Approve or reject a document (admin only)."""
    result = await session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.status = data.status
    if data.reviewer_notes is not None:
        document.reviewer_notes = data.reviewer_notes
    document.updated_at = datetime.utcnow()
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document
