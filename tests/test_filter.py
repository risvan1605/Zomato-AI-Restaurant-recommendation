"""Tests for src.services.filter – Phase 3 coverage.

Validates:
  • Location matching against both locality and listed_in_city.
  • Cuisine substring / contains matching.
  • Budget tier matching.
  • Min rating threshold.
  • online_order and book_table boolean flag filters.
  • rest_type filter.
  • Auto-relaxation (filters that would empty the pool are skipped).
  • Sort order (rating desc → votes desc).
  • Truncation to max_candidates.
  • FilterResult metadata (applied / relaxed lists).
"""

import pytest

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter import FilterResult, filter_restaurants


# ── Factory helper ──────────────────────────────────────────────────────


def _r(**overrides) -> Restaurant:
    """Build a Restaurant with sensible defaults; override any field."""
    defaults = {
        "id": "1",
        "name": "Test Restaurant",
        "location": "Koramangala",
        "listed_in_city": "Bangalore",
        "cuisines": ["North Indian"],
        "cost_for_two": 800,
        "rating": 4.0,
        "votes": 100,
        "rest_type": "Casual Dining",
        "budget_tier": "medium",
        "online_order": True,
        "book_table": False,
    }
    defaults.update(overrides)
    return Restaurant(**defaults)


def _prefs(**overrides) -> UserPreferences:
    """Build UserPreferences with sensible defaults."""
    defaults = {"location": "Koramangala", "budget": "medium"}
    defaults.update(overrides)
    return UserPreferences(**defaults)


# ════════════════════════════════════════════════════════════════════════
# Location filtering
# ════════════════════════════════════════════════════════════════════════


class TestLocationFilter:
    def test_matches_locality(self):
        pool = [_r(id="1", location="Koramangala"), _r(id="2", location="Indiranagar")]
        result = filter_restaurants(pool, _prefs(location="Koramangala"))
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "1"

    def test_matches_listed_in_city(self):
        """Location filter should also match against listed_in_city."""
        pool = [
            _r(id="1", location="Koramangala", listed_in_city="Bangalore"),
            _r(id="2", location="Andheri", listed_in_city="Mumbai"),
        ]
        result = filter_restaurants(pool, _prefs(location="Bangalore"))
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "1"

    def test_case_insensitive(self):
        pool = [_r(id="1", location="koramangala")]
        result = filter_restaurants(pool, _prefs(location="KORAMANGALA"))
        assert len(result.candidates) == 1

    def test_substring_match(self):
        """'Koramangala' should match 'Koramangala 5th Block'."""
        pool = [_r(id="1", location="Koramangala 5th Block")]
        result = filter_restaurants(pool, _prefs(location="Koramangala"))
        assert len(result.candidates) == 1

    def test_empty_on_no_match(self):
        pool = [_r(id="1", location="Mumbai")]
        result = filter_restaurants(pool, _prefs(location="Koramangala"))
        assert result.candidates == []

    def test_location_never_relaxed(self):
        """Location is a hard filter — should not be relaxed."""
        pool = [_r(id="1", location="Mumbai")]
        result = filter_restaurants(pool, _prefs(location="Koramangala"))
        assert "location" in result.filters_applied
        assert "location" not in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Cuisine filtering
# ════════════════════════════════════════════════════════════════════════


class TestCuisineFilter:
    def test_exact_match(self):
        pool = [
            _r(id="1", cuisines=["North Indian"]),
            _r(id="2", cuisines=["Italian"]),
        ]
        result = filter_restaurants(pool, _prefs(cuisine="North Indian"))
        assert all("North Indian" in r.cuisines for r in result.candidates)

    def test_substring_match(self):
        """'Indian' should match 'North Indian' via substring logic."""
        pool = [
            _r(id="1", cuisines=["North Indian"]),
            _r(id="2", cuisines=["Italian"]),
        ]
        result = filter_restaurants(pool, _prefs(cuisine="Indian"))
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "1"

    def test_case_insensitive(self):
        pool = [_r(id="1", cuisines=["CHINESE"])]
        result = filter_restaurants(pool, _prefs(cuisine="chinese"))
        assert len(result.candidates) == 1

    def test_relaxed_when_no_match(self):
        pool = [_r(id="1", cuisines=["Chinese"])]
        result = filter_restaurants(pool, _prefs(cuisine="Italian"))
        # Should relax cuisine rather than return empty
        assert len(result.candidates) >= 1
        assert "cuisine" in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Budget filtering
# ════════════════════════════════════════════════════════════════════════


class TestBudgetFilter:
    def test_exact_tier_match(self):
        pool = [
            _r(id="1", budget_tier="low"),
            _r(id="2", budget_tier="medium"),
            _r(id="3", budget_tier="high"),
        ]
        result = filter_restaurants(pool, _prefs(budget="medium"))
        assert all(r.budget_tier == "medium" for r in result.candidates)

    def test_relaxed_when_no_match(self):
        pool = [_r(id="1", budget_tier="high")]
        result = filter_restaurants(pool, _prefs(budget="low"))
        assert len(result.candidates) >= 1
        assert "budget" in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Rating filtering
# ════════════════════════════════════════════════════════════════════════


class TestRatingFilter:
    def test_filters_below_threshold(self):
        pool = [
            _r(id="1", rating=3.5),
            _r(id="2", rating=4.5),
        ]
        result = filter_restaurants(pool, _prefs(min_rating=4.0))
        assert all(r.rating >= 4.0 for r in result.candidates)

    def test_none_ratings_excluded(self):
        pool = [_r(id="1", rating=None), _r(id="2", rating=4.5)]
        result = filter_restaurants(pool, _prefs(min_rating=4.0))
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "2"

    def test_relaxed_when_no_match(self):
        pool = [_r(id="1", rating=2.0)]
        result = filter_restaurants(pool, _prefs(min_rating=4.5))
        assert len(result.candidates) >= 1
        assert "rating" in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Boolean flag filters
# ════════════════════════════════════════════════════════════════════════


class TestBooleanFlagFilters:
    def test_online_order_true(self):
        pool = [
            _r(id="1", online_order=True),
            _r(id="2", online_order=False),
        ]
        result = filter_restaurants(pool, _prefs(online_order=True))
        assert all(r.online_order for r in result.candidates)

    def test_online_order_none_skips_filter(self):
        """When online_order is None the filter should not be applied."""
        pool = [
            _r(id="1", online_order=True),
            _r(id="2", online_order=False),
        ]
        result = filter_restaurants(pool, _prefs(online_order=None))
        assert len(result.candidates) == 2

    def test_book_table_true(self):
        pool = [
            _r(id="1", book_table=True),
            _r(id="2", book_table=False),
        ]
        result = filter_restaurants(pool, _prefs(book_table=True))
        assert all(r.book_table for r in result.candidates)

    def test_relaxed_when_no_booking_available(self):
        pool = [_r(id="1", book_table=False)]
        result = filter_restaurants(pool, _prefs(book_table=True))
        assert len(result.candidates) >= 1
        assert "book_table" in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Restaurant type filter
# ════════════════════════════════════════════════════════════════════════


class TestRestTypeFilter:
    def test_filters_by_rest_type(self):
        pool = [
            _r(id="1", rest_type="Casual Dining"),
            _r(id="2", rest_type="Quick Bites"),
        ]
        result = filter_restaurants(pool, _prefs(rest_type="Casual Dining"))
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "1"

    def test_substring_match(self):
        pool = [_r(id="1", rest_type="Casual Dining, Bar")]
        result = filter_restaurants(pool, _prefs(rest_type="Casual"))
        assert len(result.candidates) == 1


# ════════════════════════════════════════════════════════════════════════
# Sorting and truncation
# ════════════════════════════════════════════════════════════════════════


class TestSortAndTruncate:
    def test_sorts_by_rating_desc_then_votes_desc(self):
        pool = [
            _r(id="1", rating=4.0, votes=50),
            _r(id="2", rating=4.5, votes=200),
            _r(id="3", rating=4.5, votes=100),
        ]
        result = filter_restaurants(pool, _prefs())
        assert result.candidates[0].id == "2"
        assert result.candidates[1].id == "3"
        assert result.candidates[2].id == "1"

    def test_respects_max_candidates(self):
        pool = [_r(id=str(i)) for i in range(50)]
        result = filter_restaurants(pool, _prefs(), max_candidates=5)
        assert len(result.candidates) == 5

    def test_none_ratings_sorted_to_bottom(self):
        pool = [
            _r(id="1", rating=None, votes=500),
            _r(id="2", rating=4.0, votes=100),
        ]
        result = filter_restaurants(pool, _prefs())
        assert result.candidates[0].id == "2"  # rated restaurant first
        assert result.candidates[1].id == "1"


# ════════════════════════════════════════════════════════════════════════
# FilterResult metadata
# ════════════════════════════════════════════════════════════════════════


class TestFilterResultMetadata:
    def test_contains_applied_filters(self):
        pool = [_r(id="1")]
        result = filter_restaurants(pool, _prefs(budget="medium", min_rating=3.0))
        assert "location" in result.filters_applied
        assert "budget" in result.filters_applied

    def test_total_after_location(self):
        pool = [_r(id="1"), _r(id="2"), _r(id="3", location="Indiranagar")]
        result = filter_restaurants(pool, _prefs())
        assert result.total_after_location == 2

    def test_relaxed_filters_tracked(self):
        pool = [_r(id="1", cuisines=["Chinese"], budget_tier="high")]
        result = filter_restaurants(
            pool, _prefs(budget="low", cuisine="Italian")
        )
        assert "cuisine" in result.filters_relaxed
        assert "budget" in result.filters_relaxed


# ════════════════════════════════════════════════════════════════════════
# Combined filter scenario
# ════════════════════════════════════════════════════════════════════════


class TestCombinedFilters:
    def test_full_pipeline(self):
        """All filters applied together on a diverse pool."""
        pool = [
            _r(id="1", cuisines=["North Indian"], budget_tier="medium",
               rating=4.5, online_order=True),
            _r(id="2", cuisines=["Italian"], budget_tier="medium",
               rating=4.0, online_order=True),
            _r(id="3", cuisines=["North Indian"], budget_tier="high",
               rating=4.8, online_order=False),
            _r(id="4", cuisines=["Chinese"], budget_tier="low",
               rating=3.0, online_order=True),
        ]
        result = filter_restaurants(
            pool,
            _prefs(
                budget="medium",
                cuisine="North Indian",
                min_rating=4.0,
                online_order=True,
            ),
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].id == "1"
