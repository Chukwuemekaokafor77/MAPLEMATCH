import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import (
    DocumentStatus,
    DocumentType,
    ListingStatus,
    MatchStatus,
    NotificationType,
    PriorityGroup,
    UserRole,
)


# === User Schemas ===


class UserCreate(BaseModel):
    clerk_id: str
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    role: UserRole = UserRole.applicant
    preferred_language: str = "en"


class UserRead(BaseModel):
    id: uuid.UUID
    clerk_id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    preferred_language: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    preferred_language: str | None = None


# === Eligibility Profile Schemas ===


class EligibilityProfileCreate(BaseModel):
    annual_income: float | None = None
    household_size: int | None = None
    priority_group: PriorityGroup = PriorityGroup.none
    province: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    max_rent: float | None = None
    needs_accessible_unit: bool = False
    consent_given: bool = False


class EligibilityProfileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    annual_income: float | None
    household_size: int | None
    priority_group: PriorityGroup
    province: str | None
    city: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    max_rent: float | None
    needs_accessible_unit: bool
    consent_given: bool
    consent_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EligibilityProfileUpdate(BaseModel):
    annual_income: float | None = None
    household_size: int | None = None
    priority_group: PriorityGroup | None = None
    province: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    max_rent: float | None = None
    needs_accessible_unit: bool | None = None
    consent_given: bool | None = None


# === Listing Schemas ===


class ListingCreate(BaseModel):
    title: str
    description: str = ""
    address: str = ""
    city: str
    province: str
    postal_code: str = ""
    latitude: float | None = None
    longitude: float | None = None
    rent_amount: float = Field(gt=0)
    is_rgi: bool = False
    bedrooms: int = Field(default=1, ge=0)
    bathrooms: int = Field(default=1, ge=0)
    is_accessible: bool = False
    amenities: str = ""
    max_income: float | None = None
    min_household_size: int | None = None
    max_household_size: int | None = None
    priority_groups: str = ""
    estimated_wait_days: int | None = None


class ListingRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None
    title: str
    description: str
    address: str
    city: str
    province: str
    postal_code: str
    latitude: float | None
    longitude: float | None
    rent_amount: float
    is_rgi: bool
    bedrooms: int
    bathrooms: int
    is_accessible: bool
    status: ListingStatus
    amenities: str
    max_income: float | None
    min_household_size: int | None
    max_household_size: int | None
    priority_groups: str
    estimated_wait_days: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    city: str | None = None
    province: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    rent_amount: float | None = Field(default=None, gt=0)
    is_rgi: bool | None = None
    bedrooms: int | None = Field(default=None, ge=0)
    bathrooms: int | None = Field(default=None, ge=0)
    is_accessible: bool | None = None
    status: ListingStatus | None = None
    amenities: str | None = None
    max_income: float | None = None
    min_household_size: int | None = None
    max_household_size: int | None = None
    priority_groups: str | None = None
    estimated_wait_days: int | None = None


class ListingSearchParams(BaseModel):
    """Query parameters for listing search."""
    city: str | None = None
    province: str | None = None
    min_rent: float | None = None
    max_rent: float | None = None
    bedrooms: int | None = None
    is_accessible: bool | None = None
    is_rgi: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = Field(default=None, gt=0, le=500)
    skip: int = 0
    limit: int = Field(default=20, ge=1, le=100)


# === Document Schemas ===


class DocumentCreate(BaseModel):
    doc_type: DocumentType
    file_url: str
    original_filename: str = ""


class DocumentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    doc_type: DocumentType
    file_url: str
    original_filename: str
    status: DocumentStatus
    ocr_text: str | None
    reviewer_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentReview(BaseModel):
    """Admin review of a document."""
    status: DocumentStatus
    reviewer_notes: str | None = None


# === Match Schemas ===


class MatchRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    listing_id: uuid.UUID
    score: float
    explanation: str
    status: MatchStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MatchStatusUpdate(BaseModel):
    status: MatchStatus


# === Eligibility Check Schemas ===


class EligibilityCheckRequest(BaseModel):
    listing_id: uuid.UUID


class EligibilityCheckResult(BaseModel):
    eligible: bool
    score: float
    reasons: list[str]
    listing_id: uuid.UUID
    listing_title: str


# === AI Matching Schemas ===


class MatchFactorRead(BaseModel):
    """A single scoring factor contributing to a match."""
    name: str
    score: float
    weight: float
    details: str


class SmartMatchResult(BaseModel):
    """Result from the hybrid AI matching engine."""
    listing_id: uuid.UUID
    listing_title: str
    eligible: bool
    final_score: float
    rule_score: float
    semantic_score: float
    ml_score: float
    factors: list[MatchFactorRead]
    explanation: str
    wait_time_days: int | None = None
    wait_time_lower: int | None = None
    wait_time_upper: int | None = None
    wait_time_confidence: float | None = None
    wait_time_factors: list[str] = []


class WaitTimeResponse(BaseModel):
    """Wait-time prediction for a single listing."""
    listing_id: uuid.UUID
    listing_title: str
    estimated_days: int
    lower_bound_days: int
    upper_bound_days: int
    confidence: float
    factors: list[str]
    method: str


# === Notification Schemas ===


class NotificationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: NotificationType
    title: str
    body: str
    is_read: bool
    related_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    notification_ids: list[uuid.UUID]


# === CMHC Sync Schemas ===


class CmhcSyncTrigger(BaseModel):
    province: str | None = None
    city: str | None = None


class CmhcSyncLogRead(BaseModel):
    id: uuid.UUID
    source: str
    records_fetched: int
    records_created: int
    records_updated: int
    status: str
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}
