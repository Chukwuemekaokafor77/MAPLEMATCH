"""CMHC Open Data sync service.

Fetches affordable-housing data from the CMHC API (or a mock for dev)
and upserts it into the local Listing table, logging each sync run.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models import CmhcSyncLog, Listing, ListingStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def run_sync(
    session: AsyncSession,
    *,
    province: str | None = None,
    city: str | None = None,
) -> CmhcSyncLog:
    """Fetch CMHC data and upsert listings. Returns the sync-log record."""
    source = "cmhc-open-data"
    log = CmhcSyncLog(source=source, started_at=datetime.now(UTC))
    session.add(log)

    try:
        records = await _fetch_cmhc_records(province=province, city=city)
        log.records_fetched = len(records)

        created, updated = await _upsert_listings(session, records)
        log.records_created = created
        log.records_updated = updated
        log.status = "success"
    except Exception as exc:
        logger.exception("CMHC sync failed")
        log.status = "error"
        log.error_message = str(exc)[:500]

    log.completed_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(log)
    return log


async def get_sync_logs(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
) -> list[CmhcSyncLog]:
    stmt = (
        select(CmhcSyncLog)
        .order_by(CmhcSyncLog.started_at.desc())  # type: ignore[union-attr]
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _fetch_cmhc_records(
    *,
    province: str | None = None,
    city: str | None = None,
) -> list[dict]:
    """Call the CMHC API and return normalised records.

    Falls back to a small set of sample records when no API key is configured,
    making local development possible without external credentials.
    """
    if not settings.cmhc_api_key:
        logger.info("No CMHC_API_KEY configured — using sample data for dev")
        return _sample_records(province=province, city=city)

    import httpx

    params: dict[str, str] = {}
    if province:
        params["province"] = province
    if city:
        params["city"] = city

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{settings.cmhc_api_url}/v1/affordable-housing",
            params=params,
            headers={"x-api-key": settings.cmhc_api_key},
        )
        resp.raise_for_status()
        data = resp.json()

    return [_normalise(r) for r in data.get("results", [])]


def _normalise(raw: dict) -> dict:
    """Map CMHC API fields to our Listing schema."""
    return {
        "title": raw.get("project_name", "CMHC Listing"),
        "description": raw.get("description", ""),
        "address": raw.get("address", ""),
        "city": raw.get("city", ""),
        "province": raw.get("province", ""),
        "postal_code": raw.get("postal_code", ""),
        "latitude": raw.get("latitude"),
        "longitude": raw.get("longitude"),
        "rent_amount": float(raw.get("average_rent", 0) or 0),
        "is_rgi": bool(raw.get("is_rgi", False)),
        "bedrooms": int(raw.get("bedrooms", 1) or 1),
        "bathrooms": 1,
        "is_accessible": bool(raw.get("is_accessible", False)),
        "amenities": "",
        "source": "cmhc",
        "source_id": raw.get("id", ""),
    }


async def _upsert_listings(
    session: AsyncSession,
    records: list[dict],
) -> tuple[int, int]:
    """Insert new or update existing listings based on source + source_id.

    Returns (created_count, updated_count).
    """
    created = 0
    updated = 0

    for rec in records:
        source_id = rec.pop("source", "") + ":" + rec.pop("source_id", "")
        # Dedup by title + address + city as a simple composite key
        stmt = select(Listing).where(
            Listing.title == rec["title"],
            Listing.address == rec["address"],
            Listing.city == rec["city"],
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for k, v in rec.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            updated += 1
        else:
            # Provide minimal required defaults
            if not rec.get("rent_amount") or rec["rent_amount"] <= 0:
                rec["rent_amount"] = 1.0  # placeholder
            listing = Listing(**rec, status=ListingStatus.active)
            session.add(listing)
            created += 1

    await session.flush()
    return created, updated


# ---------------------------------------------------------------------------
# Sample / dev data
# ---------------------------------------------------------------------------

_SAMPLE_LISTINGS: list[dict] = [
    {
        "project_name": "Toronto Community Housing - Regent Park",
        "description": "Affordable rental units in Regent Park revitalisation.",
        "address": "600 Dundas St E",
        "city": "Toronto",
        "province": "ON",
        "postal_code": "M5A 2B8",
        "latitude": 43.6590,
        "longitude": -79.3600,
        "average_rent": 950,
        "is_rgi": True,
        "bedrooms": 2,
        "is_accessible": True,
        "id": "cmhc-sample-001",
    },
    {
        "project_name": "Vancouver Affordable Housing - Olympic Village",
        "description": "Below-market rental apartments near False Creek.",
        "address": "77 Walter Hardwick Ave",
        "city": "Vancouver",
        "province": "BC",
        "postal_code": "V5Y 0C7",
        "latitude": 49.2700,
        "longitude": -123.1080,
        "average_rent": 1100,
        "is_rgi": False,
        "bedrooms": 1,
        "is_accessible": False,
        "id": "cmhc-sample-002",
    },
    {
        "project_name": "Ottawa Social Housing - Centretown",
        "description": "Geared-to-income housing in central Ottawa.",
        "address": "464 Metcalfe St",
        "city": "Ottawa",
        "province": "ON",
        "postal_code": "K2P 1R9",
        "latitude": 45.4100,
        "longitude": -75.6900,
        "average_rent": 800,
        "is_rgi": True,
        "bedrooms": 3,
        "is_accessible": True,
        "id": "cmhc-sample-003",
    },
    {
        "project_name": "Montréal Habitations communautaires",
        "description": "Logement abordable dans le Plateau Mont-Royal.",
        "address": "3600 Av du Parc",
        "city": "Montréal",
        "province": "QC",
        "postal_code": "H2X 3P9",
        "latitude": 45.5120,
        "longitude": -73.5740,
        "average_rent": 750,
        "is_rgi": True,
        "bedrooms": 2,
        "is_accessible": False,
        "id": "cmhc-sample-004",
    },
    {
        "project_name": "Calgary Affordable Residences",
        "description": "Mixed-income affordable units in Beltline.",
        "address": "1210 5 Ave SW",
        "city": "Calgary",
        "province": "AB",
        "postal_code": "T2P 0L6",
        "latitude": 51.0430,
        "longitude": -114.0760,
        "average_rent": 900,
        "is_rgi": False,
        "bedrooms": 1,
        "is_accessible": True,
        "id": "cmhc-sample-005",
    },
]


def _sample_records(
    *,
    province: str | None = None,
    city: str | None = None,
) -> list[dict]:
    """Return sample CMHC-like records, optionally filtered."""
    filtered = _SAMPLE_LISTINGS
    if province:
        filtered = [r for r in filtered if r.get("province", "").upper() == province.upper()]
    if city:
        filtered = [r for r in filtered if city.lower() in r.get("city", "").lower()]
    return [_normalise(r) for r in filtered]
