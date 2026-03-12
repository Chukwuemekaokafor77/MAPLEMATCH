"""Rule-based eligibility engine for matching applicants to affordable housing listings."""

from dataclasses import dataclass

from app.models import EligibilityProfile, Listing, PriorityGroup


@dataclass
class EligibilityResult:
    """Result of an eligibility check."""

    eligible: bool
    score: float  # 0.0 to 1.0
    reasons: list[str]  # human-readable explanations


def check_eligibility(profile: EligibilityProfile, listing: Listing) -> EligibilityResult:
    """Evaluate whether a profile is eligible for a listing and compute a match score.

    Rules:
    1. Income must not exceed listing's max_income (if set).
    2. Household size must be within min/max range (if set).
    3. If listing requires RGI, income is required.
    4. Accessibility match.
    5. Priority group bonus.
    6. Geographic proximity bonus.
    7. Rent affordability (rent <= max_rent preference).
    """
    reasons: list[str] = []
    score = 0.0
    max_score = 0.0
    disqualified = False

    # --- Hard eligibility rules ---

    # Rule 1: Income cap
    if listing.max_income is not None:
        max_score += 20
        if profile.annual_income is None:
            reasons.append("Income information required but not provided.")
            disqualified = True
        elif profile.annual_income > listing.max_income:
            reasons.append(
                f"Annual income (${profile.annual_income:,.0f}) exceeds "
                f"listing maximum (${listing.max_income:,.0f})."
            )
            disqualified = True
        else:
            # Score higher if income is further below the cap
            ratio = profile.annual_income / listing.max_income
            score += 20 * (1 - ratio * 0.5)  # 10-20 points
            reasons.append("Income within eligible range.")

    # Rule 2: Household size
    if listing.min_household_size is not None or listing.max_household_size is not None:
        max_score += 15
        if profile.household_size is None:
            reasons.append("Household size required but not provided.")
            disqualified = True
        else:
            min_hs = listing.min_household_size or 0
            max_hs = listing.max_household_size or 999
            if profile.household_size < min_hs or profile.household_size > max_hs:
                reasons.append(
                    f"Household size ({profile.household_size}) outside "
                    f"required range ({min_hs}-{max_hs})."
                )
                disqualified = True
            else:
                score += 15
                reasons.append("Household size meets requirements.")

    # Rule 3: RGI requires income
    if listing.is_rgi:
        max_score += 10
        if profile.annual_income is None:
            reasons.append("Income information required for rent-geared-to-income unit.")
            disqualified = True
        else:
            score += 10
            reasons.append("Income provided for RGI assessment.")

    # --- Soft scoring factors ---

    # Rule 4: Accessibility match
    max_score += 10
    if profile.needs_accessible_unit and listing.is_accessible:
        score += 10
        reasons.append("Accessible unit matches accessibility needs.")
    elif profile.needs_accessible_unit and not listing.is_accessible:
        reasons.append("Unit is not accessible; applicant requires accessibility.")
    elif not profile.needs_accessible_unit:
        score += 5  # neutral match
        reasons.append("No accessibility requirement.")

    # Rule 5: Priority group match
    max_score += 20
    listing_groups = _parse_priority_groups(listing.priority_groups)
    if listing_groups and profile.priority_group != PriorityGroup.none:
        if profile.priority_group in listing_groups:
            score += 20
            reasons.append(f"Priority group '{profile.priority_group.value}' is eligible for this listing.")
        else:
            score += 5
            reasons.append(f"Priority group '{profile.priority_group.value}' not specifically targeted by listing.")
    elif not listing_groups:
        score += 10  # no restriction
        reasons.append("Listing has no priority group restrictions.")
    else:
        score += 5
        reasons.append("No priority group claimed.")

    # Rule 6: Geographic proximity (province/city match)
    max_score += 15
    if profile.province and listing.province:
        if profile.province.upper() == listing.province.upper():
            score += 8
            reasons.append("Same province.")
            if profile.city and listing.city:
                if profile.city.lower() == listing.city.lower():
                    score += 7
                    reasons.append("Same city.")
                else:
                    reasons.append("Different city within same province.")
        else:
            reasons.append("Different province.")
    else:
        score += 5  # no location preference
        reasons.append("Location match not assessed (incomplete data).")

    # Rule 7: Rent affordability
    max_score += 10
    if profile.max_rent is not None:
        if listing.rent_amount <= profile.max_rent:
            score += 10
            reasons.append(f"Rent (${listing.rent_amount:,.0f}) within budget (${profile.max_rent:,.0f}).")
        else:
            overage = ((listing.rent_amount - profile.max_rent) / profile.max_rent) * 100
            if overage <= 10:
                score += 5
                reasons.append(f"Rent slightly above budget ({overage:.0f}% over).")
            else:
                reasons.append(f"Rent exceeds budget by {overage:.0f}%.")
    else:
        score += 5  # no preference set
        reasons.append("No rent budget specified.")

    if disqualified:
        return EligibilityResult(eligible=False, score=0.0, reasons=reasons)

    normalized_score = score / max_score if max_score > 0 else 0.0
    return EligibilityResult(
        eligible=True,
        score=round(normalized_score, 3),
        reasons=reasons,
    )


def _parse_priority_groups(groups_str: str) -> list[PriorityGroup]:
    """Parse comma-separated priority group string into list."""
    if not groups_str:
        return []
    result = []
    for g in groups_str.split(","):
        g = g.strip()
        if g:
            try:
                result.append(PriorityGroup(g))
            except ValueError:
                continue
    return result
