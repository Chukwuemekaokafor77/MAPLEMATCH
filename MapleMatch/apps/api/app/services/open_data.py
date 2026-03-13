"""Free Canadian open-data housing pipeline — no API keys required.

Sources attempted in order:
  1. Toronto Open Data (CKAN) — Affordable Rental Housing Register
  2. Canada Open Government Portal (CKAN) — CMHC rental data
  3. Built-in curated seed records (always succeeds)

All fetchers are async and return the same normalised list[dict] shape
that _upsert_listings() in cmhc_sync.py expects.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_TORONTO_CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
_CANADA_CKAN = "https://open.canada.ca/data/en/api/3/action"

# ─────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ─────────────────────────────────────────────────────────────────────────────


async def fetch_all_open_data(
    *,
    province: str | None = None,
    city: str | None = None,
) -> list[dict]:
    """Fetch listings from all free open-data sources.

    Returns a combined, de-duplicated list ready for upsert.
    Falls back to an empty list on any network error (the caller decides
    whether to supplement with built-in seed data).
    """
    records: list[dict] = []

    toronto = await _fetch_toronto()
    logger.info("Toronto Open Data: %d records fetched", len(toronto))
    records.extend(toronto)

    canada = await _fetch_canada_open()
    logger.info("Canada Open Data: %d records fetched", len(canada))
    records.extend(canada)

    # Simple province/city filter
    if province:
        records = [r for r in records if r.get("province", "").upper() == province.upper()]
    if city:
        records = [r for r in records if city.lower() in r.get("city", "").lower()]

    # De-duplicate by title+address+city
    seen: set[tuple[str, str, str]] = set()
    unique: list[dict] = []
    for r in records:
        key = (r.get("title", ""), r.get("address", ""), r.get("city", ""))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique


# ─────────────────────────────────────────────────────────────────────────────
# Toronto Open Data — Affordable Rental Housing Register
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_toronto() -> list[dict]:
    """Fetch Toronto affordable-housing register via the CKAN datastore API."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=20) as client:
            # Step 1: find the dataset package
            pkg_resp = await client.get(
                f"{_TORONTO_CKAN}/package_show",
                params={"id": "affordable-rental-housing-affordable-rental-housing"},
            )
            if not pkg_resp.is_success:
                # Try alternate slug
                pkg_resp = await client.get(
                    f"{_TORONTO_CKAN}/package_search",
                    params={"q": "affordable rental housing", "rows": 1},
                )
                pkg_resp.raise_for_status()
                results = pkg_resp.json().get("result", {}).get("results", [])
                if not results:
                    return []
                pkg = results[0]
            else:
                pkg = pkg_resp.json().get("result", {})

            resources = pkg.get("resources", [])

            # Step 2: find a datastore-backed resource
            ds_resource = next(
                (r for r in resources if r.get("datastore_active")),
                None,
            )
            if not ds_resource:
                # Fall back to any CSV resource
                ds_resource = next(
                    (r for r in resources if r.get("format", "").upper() == "CSV"),
                    None,
                )
            if not ds_resource:
                logger.warning("Toronto Open Data: no usable resource found")
                return []

            resource_id = ds_resource["id"]

            # Step 3: fetch records
            data_resp = await client.get(
                f"{_TORONTO_CKAN}/datastore_search",
                params={"resource_id": resource_id, "limit": 500},
            )
            data_resp.raise_for_status()
            rows = data_resp.json().get("result", {}).get("records", [])

        return [r for r in (_normalise_toronto(row) for row in rows) if r]

    except Exception as exc:
        logger.warning("Toronto Open Data fetch failed: %s", exc)
        return []


def _normalise_toronto(row: dict[str, Any]) -> dict | None:
    """Map Toronto SSHA Affordable Housing Register fields to Listing schema."""
    # Common field names in the Toronto dataset (case-insensitive check)
    lowered = {k.lower(): v for k, v in row.items()}

    address = (
        lowered.get("site_address")
        or lowered.get("address")
        or lowered.get("street_address")
        or ""
    )
    title = (
        lowered.get("proponent_name")
        or lowered.get("organization")
        or lowered.get("project_name")
        or ""
    )
    if not title and address:
        title = f"Toronto Affordable Housing – {address}"
    if not title:
        return None

    program_type = str(lowered.get("program_type") or lowered.get("tenure_type") or "")
    is_rgi = "rgi" in program_type.lower() or "rent-geared" in program_type.lower()

    bedroom_raw = str(lowered.get("bedroom_type") or lowered.get("unit_type") or "1")
    bedrooms = _parse_bedrooms(bedroom_raw)

    unit_count = int(lowered.get("unit_count") or lowered.get("total_units") or 0)
    description = (
        f"{program_type} housing in Toronto."
        if program_type
        else "Affordable rental housing in Toronto."
    )
    if unit_count:
        description = f"{unit_count}-unit {description}"

    # Toronto doesn't publish exact rents — use typical RGI/below-market estimates
    rent = 950.0 if is_rgi else 1400.0
    if bedrooms == 2:
        rent = 1050.0 if is_rgi else 1800.0
    elif bedrooms >= 3:
        rent = 1200.0 if is_rgi else 2100.0

    return {
        "title": str(title).strip()[:200],
        "description": description,
        "address": str(address).strip(),
        "city": "Toronto",
        "province": "ON",
        "postal_code": str(lowered.get("postal_code") or ""),
        "latitude": _safe_float(lowered.get("latitude") or lowered.get("lat")),
        "longitude": _safe_float(lowered.get("longitude") or lowered.get("lng") or lowered.get("lon")),
        "rent_amount": rent,
        "is_rgi": is_rgi,
        "bedrooms": bedrooms,
        "bathrooms": 1,
        "is_accessible": False,
        "amenities": "",
        "max_income": 58000.0 if is_rgi else None,
        "estimated_wait_days": 3650 if is_rgi else 365,
        "priority_groups": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Canada Open Government Portal — CMHC open datasets
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_canada_open() -> list[dict]:
    """Fetch CMHC rental data from the Canada Open Data portal (no API key)."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=20) as client:
            # Search for CMHC housing datasets
            resp = await client.get(
                f"{_CANADA_CKAN}/package_search",
                params={
                    "q": "affordable housing rental",
                    "fq": "organization:cmhc-schl",
                    "rows": 5,
                },
            )
            resp.raise_for_status()
            packages = resp.json().get("result", {}).get("results", [])

            all_records: list[dict] = []
            for pkg in packages[:2]:  # only first 2 datasets
                for resource in pkg.get("resources", [])[:1]:
                    if resource.get("format", "").upper() not in ("CSV", "JSON"):
                        continue
                    try:
                        data_resp = await client.get(
                            f"{_CANADA_CKAN}/datastore_search",
                            params={"resource_id": resource["id"], "limit": 200},
                        )
                        if data_resp.is_success:
                            rows = data_resp.json().get("result", {}).get("records", [])
                            normalised = [
                                n for n in (_normalise_canada(r) for r in rows) if n
                            ]
                            all_records.extend(normalised)
                    except Exception:
                        continue

            return all_records

    except Exception as exc:
        logger.warning("Canada Open Data fetch failed: %s", exc)
        return []


def _normalise_canada(row: dict[str, Any]) -> dict | None:
    """Normalise a Canada Open Data / CMHC row to Listing schema."""
    lowered = {k.lower(): v for k, v in row.items()}

    city = str(lowered.get("city") or lowered.get("municipality") or "").strip()
    province = str(lowered.get("province") or lowered.get("prov") or "").strip().upper()
    if not city or not province or len(province) > 2:
        return None

    title = str(
        lowered.get("project_name")
        or lowered.get("development_name")
        or lowered.get("name")
        or f"CMHC Affordable Housing – {city}"
    ).strip()[:200]

    rent = _safe_float(
        lowered.get("average_rent")
        or lowered.get("monthly_rent")
        or lowered.get("rent")
        or 900
    )
    if rent and rent < 1:  # sometimes stored as percentage
        rent = 900.0

    is_rgi = "rgi" in str(lowered.get("program_type") or "").lower()
    bedrooms = _parse_bedrooms(str(lowered.get("bedroom_type") or lowered.get("bedrooms") or "1"))

    return {
        "title": title,
        "description": str(lowered.get("description") or f"CMHC-funded affordable housing in {city}."),
        "address": str(lowered.get("address") or lowered.get("civic_address") or ""),
        "city": city,
        "province": province[:2],
        "postal_code": str(lowered.get("postal_code") or ""),
        "latitude": _safe_float(lowered.get("latitude") or lowered.get("lat")),
        "longitude": _safe_float(lowered.get("longitude") or lowered.get("long")),
        "rent_amount": rent or 900.0,
        "is_rgi": is_rgi,
        "bedrooms": bedrooms,
        "bathrooms": 1,
        "is_accessible": bool(lowered.get("is_accessible") or lowered.get("accessible")),
        "amenities": "",
        "max_income": _safe_float(lowered.get("max_income") or lowered.get("income_limit")),
        "estimated_wait_days": None,
        "priority_groups": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_bedrooms(raw: str) -> int:
    raw = raw.lower().strip()
    if "bachelor" in raw or "studio" in raw or raw in ("0", "s"):
        return 0
    if raw.startswith("1") or "1 bed" in raw:
        return 1
    if raw.startswith("2") or "2 bed" in raw:
        return 2
    if raw.startswith("3") or "3 bed" in raw:
        return 3
    if raw.startswith("4") or "4 bed" in raw:
        return 4
    try:
        return max(0, int(raw))
    except ValueError:
        return 1


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        f = float(val)
        return f if f != 0 else None
    except (ValueError, TypeError):
        return None
