"""Tests for src.data.repository – Phase 2 coverage.

Validates that :class:`RestaurantRepository` correctly converts
preprocessed DataFrame rows into :class:`Restaurant` domain objects
and provides accurate unique-value lists for UI dropdowns.
"""

import pandas as pd
import pytest

from src.data.repository import RestaurantRepository
from src.models.restaurant import Restaurant


def _make_preprocessed_df() -> pd.DataFrame:
    """Build a small preprocessed DataFrame with diverse data for testing."""
    return pd.DataFrame(
        [
            {
                "name": "Spice Garden",
                "url": "https://zomato.com/spice-garden",
                "location": "Koramangala",
                "address": "4th Block, Koramangala",
                "listed_in_city": "Bangalore",
                "cuisines_list": ["North Indian", "Chinese"],
                "rest_type": "Casual Dining",
                "listed_in_type": "Delivery",
                "dish_liked": "Biryani",
                "cost_for_two": 800,
                "budget_tier": "medium",
                "rating": 4.3,
                "votes": 500,
                "online_order": True,
                "book_table": False,
                "phone": "080-1234",
            },
            {
                "name": "Pasta Place",
                "url": None,
                "location": "Indiranagar",
                "address": "12th Main, Indiranagar",
                "listed_in_city": "Bangalore",
                "cuisines_list": ["Italian"],
                "rest_type": "Fine Dining",
                "listed_in_type": "Dine-out",
                "dish_liked": None,
                "cost_for_two": 1800,
                "budget_tier": "high",
                "rating": 4.6,
                "votes": 300,
                "online_order": False,
                "book_table": True,
                "phone": None,
            },
            {
                "name": "Chai Point",
                "url": None,
                "location": "Koramangala",
                "address": None,
                "listed_in_city": "Bangalore",
                "cuisines_list": ["Beverages", "Chinese"],
                "rest_type": "Quick Bites",
                "listed_in_type": "Delivery",
                "dish_liked": "Masala Chai",
                "cost_for_two": 200,
                "budget_tier": "low",
                "rating": 3.8,
                "votes": 100,
                "online_order": True,
                "book_table": False,
                "phone": None,
            },
        ]
    )


class TestAllRestaurants:
    def test_returns_correct_count(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        assert len(repo.all_restaurants()) == 3

    def test_returns_restaurant_instances(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        for r in repo.all_restaurants():
            assert isinstance(r, Restaurant)

    def test_maps_all_fields(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        first = repo.all_restaurants()[0]

        assert first.name == "Spice Garden"
        assert first.location == "Koramangala"
        assert first.cuisines == ["North Indian", "Chinese"]
        assert first.cost_for_two == 800
        assert first.budget_tier == "medium"
        assert first.rating == 4.3
        assert first.votes == 500
        assert first.online_order is True
        assert first.book_table is False
        assert first.rest_type == "Casual Dining"
        assert first.listed_in_type == "Delivery"
        assert first.listed_in_city == "Bangalore"
        assert first.dish_liked == "Biryani"
        assert first.address == "4th Block, Koramangala"
        assert first.phone == "080-1234"
        assert first.url == "https://zomato.com/spice-garden"

    def test_caches_result(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        first_call = repo.all_restaurants()
        second_call = repo.all_restaurants()
        assert first_call is second_call  # same list object


class TestUniqueLocations:
    def test_sorted_unique(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        locs = repo.unique_locations()
        assert locs == ["Indiranagar", "Koramangala"]

    def test_empty_on_missing_column(self):
        df = pd.DataFrame({"name": ["X"]})
        repo = RestaurantRepository(df)
        assert repo.unique_locations() == []


class TestUniqueCities:
    def test_returns_cities(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        assert repo.unique_cities() == ["Bangalore"]


class TestUniqueCuisines:
    def test_flattened_and_sorted(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        cuisines = repo.unique_cuisines()
        assert cuisines == ["Beverages", "Chinese", "Italian", "North Indian"]

    def test_empty_on_missing_column(self):
        df = pd.DataFrame({"name": ["X"]})
        repo = RestaurantRepository(df)
        assert repo.unique_cuisines() == []


class TestUniqueRestTypes:
    def test_returns_rest_types(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        types = repo.unique_rest_types()
        assert types == ["Casual Dining", "Fine Dining", "Quick Bites"]


class TestUniqueListedTypes:
    def test_returns_listed_types(self):
        repo = RestaurantRepository(_make_preprocessed_df())
        types = repo.unique_listed_types()
        assert types == ["Delivery", "Dine-out"]
