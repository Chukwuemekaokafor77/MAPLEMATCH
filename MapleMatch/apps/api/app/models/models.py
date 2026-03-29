import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


# === Enums ===


class UserRole(str, Enum):
    applicant = "applicant"
    admin = "admin"
    nonprofit = "nonprofit"


class DocumentType(str, Enum):
    income_proof = "income_proof"
    government_id = "government_id"
    residency_proof = "residency_proof"
    other = "other"


class DocumentStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class MatchStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    expired = "expired"


class ListingStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    waitlist = "waitlist"
    filled = "filled"


class PriorityGroup(str, Enum):
    none = "none"
    senior = "senior"
    veteran = "veteran"
    indigenous = "indigenous"
    newcomer = "newcomer"
    fleeing_violence = "fleeing_violence"
    disability = "disability"


class NotificationType(str, Enum):
    match_found = "match_found"
    listing_update = "listing_update"
    document_reviewed = "document_reviewed"
    waitlist_update = "waitlist_update"
    system = "system"


# === Models ===


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    clerk_id: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    first_name: str = ""
    last_name: str = ""
    role: UserRole = Field(default=UserRole.applicant, index=True)
    preferred_language: str = Field(default="en")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    profile: Optional["EligibilityProfile"] = Relationship(back_populates="user")
    documents: list["Document"] = Relationship(back_populates="user")
    matches: list["Match"] = Relationship(back_populates="user")
    notifications: list["Notification"] = Relationship(back_populates="user")


class EligibilityProfile(SQLModel, table=True):
    __tablename__ = "eligibility_profiles"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    annual_income: float | None = None
    household_size: int | None = None
    priority_group: PriorityGroup = Field(default=PriorityGroup.none)
    province: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    max_rent: float | None = None
    needs_accessible_unit: bool = Field(default=False)
    consent_given: bool = Field(default=False)
    consent_date: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="profile")


class Listing(SQLModel, table=True):
    __tablename__ = "listings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID | None = Field(
        default=None, foreign_key="users.id", index=True
    )
    title: str
    description: str = ""
    address: str = ""
    city: str = Field(index=True)
    province: str = Field(index=True)
    postal_code: str = ""
    latitude: float | None = None
    longitude: float | None = None
    rent_amount: float
    is_rgi: bool = Field(default=False)
    bedrooms: int = Field(default=1)
    bathrooms: int = Field(default=1)
    is_accessible: bool = Field(default=False)
    status: ListingStatus = Field(default=ListingStatus.active, index=True)
    amenities: str = ""  # JSON string for now; migrate to JSONB later
    max_income: float | None = None
    min_household_size: int | None = None
    max_household_size: int | None = None
    priority_groups: str = ""  # comma-separated PriorityGroup values
    estimated_wait_days: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    matches: list["Match"] = Relationship(back_populates="listing")


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    doc_type: DocumentType
    file_url: str
    original_filename: str = ""
    status: DocumentStatus = Field(default=DocumentStatus.pending)
    ocr_text: str | None = None
    reviewer_notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="documents")


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", index=True)
    score: float = Field(default=0.0)
    explanation: str = ""  # human-readable match reasoning
    status: MatchStatus = Field(default=MatchStatus.pending, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="matches")
    listing: Listing = Relationship(back_populates="matches")


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    notification_type: NotificationType = Field(index=True)
    title: str
    body: str = ""
    is_read: bool = Field(default=False, index=True)
    related_id: uuid.UUID | None = None  # optional link to match/listing/document
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="notifications")


class CmhcSyncLog(SQLModel, table=True):
    __tablename__ = "cmhc_sync_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source: str = "cmhc"  # cmhc, provincial, municipal
    records_fetched: int = 0
    records_created: int = 0
    records_updated: int = 0
    status: str = "success"  # success, partial, failed
    error_message: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    completed_at: datetime | None = None
