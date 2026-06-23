"""
Candidate mapper.

Converts :class:`Restaurant` domain objects into compact JSON-serialisable
dictionaries (``CandidateDTO`` dicts) suitable for injection into the LLM
prompt.

Only the fields useful for ranking and explanation are included; oversized
columns (``reviews_list``, ``menu_item``) are deliberately excluded to stay
within token budgets.

See context.md §7.2 for the target schema.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.models.restaurant import Restaurant


# Type alias – a CandidateDTO is just a plain dict.
CandidateDTO = Dict[str, Any]


def restaurant_to_dto(restaurant: Restaurant) -> CandidateDTO:
    """Map a single :class:`Restaurant` to a compact LLM-friendly dict.

    The output schema matches context.md §7.2::

        {
          "id":                "42",
          "name":              "Jalsa",
          "location":          "Banashankari",
          "cuisines":          "North Indian, Chinese",
          "rate":              4.2,
          "votes":             800,
          "approx_cost_for_two": 600,
          "rest_type":         "Casual Dining",
          "dish_liked":        "Paneer Butter Masala, Biryani",
          "online_order":      true,
          "book_table":        false
        }

    Args:
        restaurant: A domain model instance.

    Returns:
        A JSON-serialisable dict with only the fields needed by the LLM.
    """
    return {
        "id": restaurant.id,
        "name": restaurant.name,
        "location": restaurant.location,
        "cuisines": ", ".join(restaurant.cuisines) if (restaurant.cuisines is not None and len(restaurant.cuisines) > 0) else "",
        "rate": restaurant.rating,
        "votes": restaurant.votes,
        "approx_cost_for_two": restaurant.cost_for_two,
        "rest_type": restaurant.rest_type or "",
        "dish_liked": restaurant.dish_liked or "",
        "online_order": restaurant.online_order,
        "book_table": restaurant.book_table,
    }


def restaurants_to_dtos(restaurants: List[Restaurant]) -> List[CandidateDTO]:
    """Batch-convert a list of restaurants to candidate DTOs.

    Args:
        restaurants: List of :class:`Restaurant` domain objects
            (typically the filtered candidate set).

    Returns:
        A list of compact dicts ready for JSON serialisation into the
        LLM prompt.
    """
    return [restaurant_to_dto(r) for r in restaurants]
