"""
Recommendation and RecommendationResponse models.

Maps to the output schema defined in architecture.md §2.4.
The response includes a nested `metadata` dict containing filter and model info.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Recommendation:
    """A single ranked restaurant recommendation returned to the user."""

    rank: int
    name: str
    cuisine: str                                # joined cuisine string for display
    rating: Optional[float] = None
    estimated_cost: Optional[int] = None        # cost_for_two
    votes: int = 0
    budget_tier: str = "Unknown"
    rest_type: Optional[str] = None
    online_order: bool = False
    book_table: bool = False
    explanation: str = ""                        # LLM-generated rationale


@dataclass
class RecommendationResponse:
    """Full response payload for a recommendation request."""

    recommendations: List[Recommendation] = field(default_factory=list)
    summary: Optional[str] = None               # optional LLM summary paragraph
    metadata: Dict[str, Any] = field(default_factory=lambda: {
        "candidates_considered": 0,
        "filters_applied": {},
        "model": "",
    })
