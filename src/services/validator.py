"""
Preference validator.

Sanitizes and validates raw user inputs before they enter the filtering
engine.  Covers:

* Text stripping and length limits (anti-injection).
* Rating bound clamping.
* Budget tier normalisation.
* Unknown option detection (location / cuisine not in catalogue).

Raises :class:`ValidationError` when hard constraints are violated.
"""

from __future__ import annotations

import re
from typing import List, Optional

from src.models.preferences import UserPreferences


class ValidationError(Exception):
    """Raised when user-supplied preferences fail validation."""


# ── Constants ───────────────────────────────────────────────────────────

_MAX_TEXT_LENGTH = 500          # max chars for the free-text field
_VALID_BUDGETS = {"low", "medium", "high"}
_RATING_MIN = 0.0
_RATING_MAX = 5.0

# Strips control chars but keeps common Unicode (accents, scripts, etc.)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ── Public API ──────────────────────────────────────────────────────────


def validate_preferences(
    *,
    location: str,
    budget: str,
    min_rating: float = 0.0,
    cuisine: Optional[str] = None,
    online_order: Optional[bool] = None,
    book_table: Optional[bool] = None,
    rest_type: Optional[str] = None,
    additional: Optional[str] = None,
    known_locations: Optional[List[str]] = None,
    known_cuisines: Optional[List[str]] = None,
) -> UserPreferences:
    """Build a :class:`UserPreferences` after sanitising every field.

    Args:
        location:       Raw location string from the UI.
        budget:         Raw budget tier string.
        min_rating:     Minimum rating (clamped to [0.0, 5.0]).
        cuisine:        Optional cuisine text.
        online_order:   Optional boolean flag.
        book_table:     Optional boolean flag.
        rest_type:      Optional restaurant type text.
        additional:     Free-form extra preferences.
        known_locations: If supplied, the location must be present in this
            list (case-insensitive).
        known_cuisines: If supplied, the cuisine (when given) must be
            present in this list (case-insensitive).

    Returns:
        A validated :class:`UserPreferences` instance.

    Raises:
        ValidationError: When a hard constraint is violated.
    """
    # ── Location ────────────────────────────────────────────────────────
    location = _sanitize_text(location)
    if not location:
        raise ValidationError("Location is required.")

    if known_locations is not None:
        _check_known_value(location, known_locations, "location")

    # ── Budget ──────────────────────────────────────────────────────────
    budget = _sanitize_text(budget).lower()
    if budget not in _VALID_BUDGETS:
        raise ValidationError(
            f"Invalid budget tier '{budget}'. Must be one of: {', '.join(sorted(_VALID_BUDGETS))}."
        )

    # ── Min rating ──────────────────────────────────────────────────────
    min_rating = max(_RATING_MIN, min(_RATING_MAX, float(min_rating)))

    # ── Cuisine ─────────────────────────────────────────────────────────
    clean_cuisine: Optional[str] = None
    if cuisine:
        clean_cuisine = _sanitize_text(cuisine)
        if clean_cuisine and known_cuisines is not None:
            _check_known_value(clean_cuisine, known_cuisines, "cuisine")

    # ── Rest type ───────────────────────────────────────────────────────
    clean_rest_type: Optional[str] = None
    if rest_type:
        clean_rest_type = _sanitize_text(rest_type) or None

    # ── Additional (free text) ──────────────────────────────────────────
    clean_additional: Optional[str] = None
    if additional:
        clean_additional = _sanitize_text(additional, max_length=_MAX_TEXT_LENGTH)

    return UserPreferences(
        location=location,
        budget=budget,
        min_rating=min_rating,
        cuisine=clean_cuisine or None,
        online_order=online_order,
        book_table=book_table,
        rest_type=clean_rest_type,
        additional=clean_additional,
    )


# ── Helpers ─────────────────────────────────────────────────────────────


def _sanitize_text(value: str, *, max_length: int = 200) -> str:
    """Strip whitespace, control characters, and enforce length limit."""
    text = _CONTROL_CHAR_RE.sub("", str(value)).strip()
    return text[:max_length]


def _check_known_value(
    value: str,
    known: List[str],
    label: str,
) -> None:
    """Raise :class:`ValidationError` if *value* is not in *known* (case-insensitive)."""
    lower_known = {k.lower() for k in known}
    if value.lower() not in lower_known:
        raise ValidationError(
            f"Unknown {label}: '{value}'. "
            f"Please select from the available options."
        )
