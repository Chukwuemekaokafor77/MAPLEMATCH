#!/usr/bin/env python3
"""Standalone database seeder for MapleMatch listings.

Run this script directly to populate the database with real Canadian
affordable housing data without needing admin API credentials:

    cd apps/api
    python scripts/seed_listings.py

    # Filter to a single province:
    python scripts/seed_listings.py --province ON

    # Filter to a city:
    python scripts/seed_listings.py --city Toronto

Environment variables (same as the FastAPI app):
    DATABASE_URL  — PostgreSQL connection string (required)
    CMHC_API_KEY  — optional; uses free open-data sources when absent

Sources (in priority order):
  1. Toronto Open Data CKAN — Affordable Rental Housing Register (no auth)
  2. Canada Open Government Portal CKAN — CMHC datasets (no auth)
  3. Built-in curated dataset — 75+ listings across all 13 provinces/territories
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

# Allow running from the repo root or from apps/api/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_listings")


async def _run(province: str | None, city: str | None) -> None:
    from app.config import settings
    from app.db import async_session
    from app.services.cmhc_sync import _fetch_cmhc_records, _upsert_listings

    if not settings.database_url:
        logger.error("DATABASE_URL is not set. Aborting.")
        sys.exit(1)

    logger.info("Connecting to database…")

    async with async_session() as session:
        logger.info("Fetching listings (province=%s, city=%s)…", province, city)
        records = await _fetch_cmhc_records(province=province, city=city)
        logger.info("Fetched %d records total", len(records))

        created, updated = await _upsert_listings(session, records)
        await session.commit()

    logger.info("Done — created: %d, updated: %d", created, updated)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MapleMatch listings database")
    parser.add_argument("--province", metavar="XX", help="Two-letter province/territory code (e.g. ON, BC)")
    parser.add_argument("--city", metavar="NAME", help="City name filter (partial match)")
    args = parser.parse_args()

    asyncio.run(_run(province=args.province, city=args.city))


if __name__ == "__main__":
    main()
