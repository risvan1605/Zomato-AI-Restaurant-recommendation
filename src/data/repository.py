"""
Restaurant data repository.

Provides high-level catalog operations on top of the preprocessed dataset:
  • Convert DataFrame rows to :class:`Restaurant` domain objects.
  • Supply unique locations, cities, cuisines, and restaurant types for
    frontend select dropdowns.

The repository is intentionally **read-only**; all write operations happen
during the preprocessing / caching stage in :mod:`src.data.loader`.
"""

from __future__ import annotations

import logging
from typing import List

import pandas as pd

from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


class RestaurantRepository:
    """In-memory repository backed by a preprocessed pandas DataFrame.

    Args:
        df: A preprocessed DataFrame produced by
            :func:`src.data.preprocessor.preprocess_dataframe`.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df
        self._restaurants: List[Restaurant] | None = None  # lazily built

    # ════════════════════════════════════════════════════════════════════
    # Catalog queries
    # ════════════════════════════════════════════════════════════════════

    def all_restaurants(self) -> List[Restaurant]:
        """Return every row as a :class:`Restaurant` domain object.

        Results are cached after the first call for O(1) subsequent access.
        """
        if self._restaurants is not None:
            return self._restaurants

        restaurants: List[Restaurant] = []
        for idx, row in self._df.iterrows():
            restaurants.append(self._row_to_restaurant(idx, row))

        self._restaurants = restaurants
        logger.info("Built %d Restaurant domain objects.", len(restaurants))
        return self._restaurants

    # ════════════════════════════════════════════════════════════════════
    # Dropdown helpers – unique values for the frontend UI
    # ════════════════════════════════════════════════════════════════════

    def unique_locations(self) -> List[str]:
        """Return sorted unique locality names (the ``location`` column)."""
        return self._sorted_unique("location")

    def unique_cities(self) -> List[str]:
        """Return sorted unique city names (``listed_in_city``)."""
        return self._sorted_unique("listed_in_city")

    def unique_cuisines(self) -> List[str]:
        """Return sorted unique cuisine names across all restaurants."""
        if "cuisines_list" not in self._df.columns:
            return []
        all_cuisines: set[str] = set()
        for lst in self._df["cuisines_list"].dropna():
            try:
                all_cuisines.update(c for c in lst if c)
            except TypeError:
                pass
        return sorted(all_cuisines)

    def unique_rest_types(self) -> List[str]:
        """Return sorted unique restaurant type labels."""
        return self._sorted_unique("rest_type")

    def unique_listed_types(self) -> List[str]:
        """Return sorted unique listing-type labels (Buffet, Delivery …)."""
        return self._sorted_unique("listed_in_type")

    # ════════════════════════════════════════════════════════════════════
    # Private helpers
    # ════════════════════════════════════════════════════════════════════

    def _sorted_unique(self, col: str) -> List[str]:
        """Generic helper: return sorted unique non-null values for *col*."""
        if col not in self._df.columns:
            return []
        values = self._df[col].dropna().unique().tolist()
        return sorted(v for v in values if v)

    @staticmethod
    def _row_to_restaurant(idx: object, row: pd.Series) -> Restaurant:
        """Map a single DataFrame row to a :class:`Restaurant` instance."""
        return Restaurant(
            id=str(idx),
            name=str(row.get("name", "")),
            url=row.get("url"),
            location=str(row.get("location", "")),
            address=row.get("address"),
            listed_in_city=row.get("listed_in_city"),
            cuisines=list(row.get("cuisines_list", [])) if hasattr(row.get("cuisines_list", []), "__iter__") else [],
            rest_type=row.get("rest_type"),
            listed_in_type=row.get("listed_in_type"),
            dish_liked=row.get("dish_liked"),
            cost_for_two=row.get("cost_for_two"),
            budget_tier=row.get("budget_tier"),
            rating=row.get("rating"),
            votes=int(row.get("votes", 0)),
            online_order=bool(row.get("online_order", False)),
            book_table=bool(row.get("book_table", False)),
            phone=row.get("phone"),
        )
