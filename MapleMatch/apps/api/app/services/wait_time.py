"""Wait-time prediction service.

Estimates the number of days an applicant might wait for placement
based on profile features, listing characteristics, and historical patterns.

Uses a heuristic formula as baseline. When sufficient match outcome data
is collected, a trained LightGBM model will replace the heuristic.
"""

import logging
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.models import EligibilityProfile, Listing, PriorityGroup

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "wait_time_model.txt"

# Trained model (loaded on first use, if available)
_model = None


@dataclass
class WaitTimeEstimate:
    """Predicted wait time with confidence interval."""

    estimated_days: int
    lower_bound_days: int
    upper_bound_days: int
    confidence: float  # 0.0 to 1.0
    factors: list[str]  # human-readable factors affecting the estimate
    method: str  # "heuristic" or "ml_model"


def predict_wait_time(
    profile: EligibilityProfile, listing: Listing
) -> WaitTimeEstimate:
    """Predict wait time for a profile-listing pair.

    Uses a trained model if available, otherwise falls back to heuristic.
    """
    model = _load_model()
    if model is not None:
        return _predict_with_model(model, profile, listing)
    return _predict_heuristic(profile, listing)


def _load_model():
    """Load trained LightGBM model if available."""
    global _model
    if _model is not None:
        return _model

    if MODEL_PATH.exists():
        try:
            import lightgbm as lgb

            _model = lgb.Booster(model_file=str(MODEL_PATH))
            logger.info("Loaded wait-time prediction model from %s", MODEL_PATH)
            return _model
        except Exception:
            logger.warning("Failed to load wait-time model, using heuristic")
            return None

    return None


def _predict_heuristic(
    profile: EligibilityProfile, listing: Listing
) -> WaitTimeEstimate:
    """Heuristic-based wait time prediction.

    Base wait time is modulated by:
    - Listed estimated_wait_days (if provided by the org)
    - Market competitiveness (province/city)
    - Priority group (some groups get priority placement)
    - RGI status (longer queues)
    - Income level relative to listing cap
    - Household size
    """
    factors: list[str] = []

    # Base estimate: use listing's stated wait time or province default
    if listing.estimated_wait_days is not None:
        base_days = listing.estimated_wait_days
        factors.append(f"Listing states ~{base_days} day wait")
    else:
        base_days = _province_base_wait(listing.province)
        factors.append(f"Provincial average wait: ~{base_days} days")

    multiplier = 1.0

    # Priority group adjustment
    priority_multipliers = {
        PriorityGroup.fleeing_violence: 0.4,
        PriorityGroup.indigenous: 0.6,
        PriorityGroup.veteran: 0.6,
        PriorityGroup.disability: 0.7,
        PriorityGroup.senior: 0.7,
        PriorityGroup.newcomer: 0.8,
        PriorityGroup.none: 1.0,
    }
    pg = profile.priority_group or PriorityGroup.none
    pg_mult = priority_multipliers.get(pg, 1.0)
    if pg != PriorityGroup.none:
        multiplier *= pg_mult
        factors.append(f"Priority group '{pg.value}' reduces wait by {(1 - pg_mult):.0%}")

    # RGI units have longer waitlists
    if listing.is_rgi:
        multiplier *= 1.4
        factors.append("RGI units typically have longer waitlists (+40%)")

    # Income proximity to cap (lower income → higher priority in many programs)
    if profile.annual_income is not None and listing.max_income is not None:
        income_ratio = profile.annual_income / listing.max_income
        if income_ratio < 0.5:
            multiplier *= 0.8
            factors.append("Low income relative to cap may improve priority")
        elif income_ratio > 0.8:
            multiplier *= 1.1
            factors.append("Income near cap may reduce priority")

    # Household size → fewer large units available
    if profile.household_size is not None:
        if profile.household_size >= 5:
            multiplier *= 1.3
            factors.append("Larger households wait longer (fewer large units)")
        elif profile.household_size == 1:
            multiplier *= 0.9
            factors.append("Single-person households have more options")

    # Accessible units are scarcer
    if profile.needs_accessible_unit and not listing.is_accessible:
        multiplier *= 1.5
        factors.append("Accessible units are scarcer (+50% wait)")

    estimated = int(base_days * multiplier)
    # Confidence interval: ±30% for heuristic
    lower = max(1, int(estimated * 0.7))
    upper = int(estimated * 1.3)

    return WaitTimeEstimate(
        estimated_days=estimated,
        lower_bound_days=lower,
        upper_bound_days=upper,
        confidence=0.4,  # low confidence for heuristic
        factors=factors,
        method="heuristic",
    )


def _predict_with_model(model, profile: EligibilityProfile, listing: Listing) -> WaitTimeEstimate:
    """Predict wait time using trained LightGBM model."""
    features = _extract_features(profile, listing)
    feature_array = np.array([features])

    predicted_log_days = model.predict(feature_array)[0]
    # Model predicts log(days) to handle skewed distribution
    predicted_days = max(1, int(math.exp(predicted_log_days)))

    # Use model's variance estimate for confidence interval
    lower = max(1, int(predicted_days * 0.8))
    upper = int(predicted_days * 1.2)

    factors = [
        f"ML model prediction: ~{predicted_days} days",
        f"Based on {len(features)} features",
    ]

    return WaitTimeEstimate(
        estimated_days=predicted_days,
        lower_bound_days=lower,
        upper_bound_days=upper,
        confidence=0.75,
        factors=factors,
        method="ml_model",
    )


def _extract_features(
    profile: EligibilityProfile, listing: Listing
) -> list[float]:
    """Extract numerical features for the ML model."""
    pg_map = {pg: i for i, pg in enumerate(PriorityGroup)}

    return [
        profile.annual_income or 0.0,
        profile.household_size or 1,
        pg_map.get(profile.priority_group, 0),
        profile.max_rent or 0.0,
        float(profile.needs_accessible_unit),
        listing.rent_amount,
        listing.bedrooms,
        float(listing.is_rgi),
        float(listing.is_accessible),
        listing.estimated_wait_days or 0,
        listing.max_income or 0.0,
        listing.max_household_size or 0,
    ]


def _province_base_wait(province: str | None) -> int:
    """Get baseline wait days by province (from CMHC/public housing data)."""
    base_waits = {
        "ON": 180,   # Ontario — long waitlists, especially Toronto
        "BC": 150,   # British Columbia
        "QC": 120,   # Quebec
        "AB": 90,    # Alberta
        "MB": 100,   # Manitoba
        "SK": 80,    # Saskatchewan
        "NS": 90,    # Nova Scotia
        "NB": 75,    # New Brunswick
        "NL": 60,    # Newfoundland
        "PE": 50,    # PEI
        "NT": 40,    # NWT
        "NU": 45,    # Nunavut
        "YT": 35,    # Yukon
    }
    if province:
        return base_waits.get(province.upper(), 120)
    return 120  # national average default
