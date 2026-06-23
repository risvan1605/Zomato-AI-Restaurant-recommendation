"""
Canonical Restaurant model.

Maps directly to the schema defined in architecture.md §2.1 and context.md §5.3.
Every row in the preprocessed dataset is represented as one of these objects.

Fields cover all 17 columns from the Zomato HF dataset, with derived fields
(budget_tier, cuisines list) added during preprocessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Restaurant:
    """Domain model for a single restaurant record."""

    # ── Core identifiers ────────────────────────────────────────────────
    id: str                                         # stable identifier (row index)
    name: str                                       # restaurant name (2–159 chars)
    url: Optional[str] = None                       # Zomato listing URL

    # ── Location ────────────────────────────────────────────────────────
    location: str = ""                              # neighbourhood / locality (93 unique)
    address: Optional[str] = None                   # full street address
    listed_in_city: Optional[str] = None            # city grouping (30 unique)

    # ── Food & type ─────────────────────────────────────────────────────
    cuisines: List[str] = field(default_factory=list)  # e.g. ["Italian", "Continental"]
    rest_type: Optional[str] = None                 # casual dining, cafe, etc.
    listed_in_type: Optional[str] = None            # listing category (Buffet, Delivery …)
    dish_liked: Optional[str] = None                # popular dishes (nullable, up to 134 chars)

    # ── Pricing ─────────────────────────────────────────────────────────
    cost_for_two: Optional[int] = None              # numeric cost for two (INR)
    budget_tier: Optional[str] = None               # derived: "low" | "medium" | "high"

    # ── Ratings & popularity ────────────────────────────────────────────
    rating: Optional[float] = None                  # parsed float (e.g. 4.2)
    votes: int = 0                                  # number of user votes

    # ── Service flags ───────────────────────────────────────────────────
    online_order: bool = False                      # whether online ordering is available
    book_table: bool = False                        # whether table booking is available

    # ── Contact ─────────────────────────────────────────────────────────
    phone: Optional[str] = None                     # contact number(s)
