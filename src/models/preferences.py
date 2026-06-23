"""
User preferences model.

Maps to the UserPreferences schema defined in architecture.md §2.2
and context.md §6.1–6.2.

Captures both structured filter inputs and optional free-form text for LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UserPreferences:
    """Validated, normalized user preferences for a recommendation request.

    Attributes:
        location:       Required – city or locality name (matched against
                        both ``location`` and ``listed_in_city`` columns).
        budget:         Budget tier: ``"low"`` | ``"medium"`` | ``"high"``.
        min_rating:     Minimum acceptable rating (0.0–5.0, default 0.0).
        cuisine:        Optional single primary cuisine for filtering.
        online_order:   If ``True``, restrict to restaurants that accept
                        online orders.
        book_table:     If ``True``, restrict to restaurants that accept
                        table bookings.
        rest_type:      Optional restaurant type filter
                        (e.g. ``"Casual Dining"``, ``"Quick Bites"``).
        additional:     Free-text soft preferences forwarded to the LLM.
    """

    location: str                               # required – city or locality
    budget: str                                 # "low" | "medium" | "high"
    min_rating: float = 0.0                     # minimum acceptable rating (0.0–5.0)
    cuisine: Optional[str] = None               # optional single primary cuisine
    online_order: Optional[bool] = None         # None = don't filter
    book_table: Optional[bool] = None           # None = don't filter
    rest_type: Optional[str] = None             # optional restaurant type
    additional: Optional[str] = None            # free-text soft preferences for the LLM
