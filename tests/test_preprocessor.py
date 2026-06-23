"""Tests for src.data.preprocessor – Phase 2 coverage.

Tests cover every helper parser and the end-to-end
:func:`preprocess_dataframe` pipeline against a synthetic DataFrame
that mirrors the real Zomato dataset schema.
"""

import math

import pandas as pd
import pytest

from src.data.preprocessor import (
    _classify_budget,
    _clean_text,
    _normalize_name,
    _parse_bool_flag,
    _parse_cost,
    _parse_rating,
    _parse_votes,
    _split_cuisines,
    preprocess_dataframe,
)


# ════════════════════════════════════════════════════════════════════════
# _parse_rating
# ════════════════════════════════════════════════════════════════════════


class TestParseRating:
    def test_normal_fraction(self):
        assert _parse_rating("4.1/5") == 4.1

    def test_new_label(self):
        assert _parse_rating("NEW") is None

    def test_dash(self):
        assert _parse_rating("-") is None

    def test_nan(self):
        assert _parse_rating(float("nan")) is None

    def test_plain_float_string(self):
        assert _parse_rating("3.8") == 3.8

    def test_integer_string(self):
        assert _parse_rating("4") == 4.0

    def test_none_label(self):
        assert _parse_rating("None") is None

    def test_empty_string(self):
        assert _parse_rating("") is None

    def test_numeric_input(self):
        assert _parse_rating(4.5) == 4.5

    def test_whitespace_padding(self):
        assert _parse_rating("  3.9/5  ") == 3.9


# ════════════════════════════════════════════════════════════════════════
# _parse_cost
# ════════════════════════════════════════════════════════════════════════


class TestParseCost:
    def test_numeric_string(self):
        assert _parse_cost("800") == 800

    def test_comma_separated(self):
        assert _parse_cost("1,200") == 1200

    def test_nan(self):
        assert _parse_cost(float("nan")) is None

    def test_currency_symbol(self):
        assert _parse_cost("₹1,200") == 1200

    def test_empty_string(self):
        assert _parse_cost("") is None

    def test_non_numeric_garbage(self):
        assert _parse_cost("N/A") is None

    def test_integer_input(self):
        assert _parse_cost(500) == 500


# ════════════════════════════════════════════════════════════════════════
# _classify_budget
# ════════════════════════════════════════════════════════════════════════


class TestClassifyBudget:
    def test_low(self):
        assert _classify_budget(300) == "low"

    def test_medium(self):
        assert _classify_budget(1000) == "medium"

    def test_high(self):
        assert _classify_budget(2000) == "high"

    def test_boundary_low(self):
        assert _classify_budget(500) == "low"

    def test_boundary_medium(self):
        assert _classify_budget(1500) == "medium"

    def test_boundary_medium_plus_one(self):
        assert _classify_budget(1501) == "high"

    def test_none(self):
        assert _classify_budget(None) is None

    def test_zero(self):
        assert _classify_budget(0) == "low"


# ════════════════════════════════════════════════════════════════════════
# _split_cuisines
# ════════════════════════════════════════════════════════════════════════


class TestSplitCuisines:
    def test_comma_separated(self):
        assert _split_cuisines("Italian, Chinese, Thai") == [
            "Italian",
            "Chinese",
            "Thai",
        ]

    def test_single(self):
        assert _split_cuisines("North Indian") == ["North Indian"]

    def test_nan(self):
        assert _split_cuisines(float("nan")) == []

    def test_empty_string(self):
        assert _split_cuisines("") == []

    def test_trailing_comma(self):
        assert _split_cuisines("Pizza, ") == ["Pizza"]


# ════════════════════════════════════════════════════════════════════════
# _parse_bool_flag
# ════════════════════════════════════════════════════════════════════════


class TestParseBoolFlag:
    def test_yes(self):
        assert _parse_bool_flag("Yes") is True

    def test_no(self):
        assert _parse_bool_flag("No") is False

    def test_case_insensitive(self):
        assert _parse_bool_flag("YES") is True
        assert _parse_bool_flag("yes") is True

    def test_nan(self):
        assert _parse_bool_flag(float("nan")) is False

    def test_empty(self):
        assert _parse_bool_flag("") is False


# ════════════════════════════════════════════════════════════════════════
# _clean_text
# ════════════════════════════════════════════════════════════════════════


class TestCleanText:
    def test_normal(self):
        assert _clean_text("  hello  ") == "hello"

    def test_nan(self):
        assert _clean_text(float("nan")) is None

    def test_empty(self):
        assert _clean_text("") is None

    def test_whitespace_only(self):
        assert _clean_text("   ") is None


# ════════════════════════════════════════════════════════════════════════
# _normalize_name
# ════════════════════════════════════════════════════════════════════════


class TestNormalizeName:
    def test_lowercase(self):
        assert _normalize_name("koramangala") == "Koramangala"

    def test_mixed_case(self):
        assert _normalize_name("  INDIRANAGAR  ") == "Indiranagar"

    def test_nan(self):
        assert _normalize_name(float("nan")) == ""


# ════════════════════════════════════════════════════════════════════════
# _parse_votes
# ════════════════════════════════════════════════════════════════════════


class TestParseVotes:
    def test_normal(self):
        assert _parse_votes("500") == 500

    def test_comma(self):
        assert _parse_votes("16,800") == 16800

    def test_nan(self):
        assert _parse_votes(float("nan")) == 0

    def test_float_string(self):
        assert _parse_votes("123.0") == 123

    def test_garbage(self):
        assert _parse_votes("abc") == 0


# ════════════════════════════════════════════════════════════════════════
# preprocess_dataframe – end-to-end integration
# ════════════════════════════════════════════════════════════════════════


def _make_raw_dataframe(**overrides) -> pd.DataFrame:
    """Build a single-row DataFrame mimicking the raw HF dataset schema."""
    row = {
        "url": "https://www.zomato.com/bangalore/test-cafe",
        "address": "123, 4th Block, Koramangala",
        "name": "Test Cafe",
        "online_order": "Yes",
        "book_table": "No",
        "rate": "4.1/5",
        "votes": "500",
        "phone": "080 1234 5678",
        "location": "koramangala",
        "rest_type": "Casual Dining",
        "dish_liked": "Paneer Butter Masala",
        "cuisines": "Italian, Mexican",
        "approx_cost(for two people)": "800",
        "reviews_list": "[('Rated 4.0', 'Good food')]",
        "menu_item": "[]",
        "listed_in(type)": "Delivery",
        "listed_in(city)": "banashankari",
    }
    row.update(overrides)
    return pd.DataFrame([row])


class TestPreprocessDataframe:
    def test_rating_parsed(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["rating"].iloc[0] == 4.1

    def test_cost_parsed(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["cost_for_two"].iloc[0] == 800

    def test_budget_tier(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["budget_tier"].iloc[0] == "medium"

    def test_cuisines_split(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["cuisines_list"].iloc[0] == ["Italian", "Mexican"]

    def test_location_normalized(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["location"].iloc[0] == "Koramangala"

    def test_listed_in_city_normalized(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["listed_in_city"].iloc[0] == "Banashankari"

    def test_listed_in_type_cleaned(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["listed_in_type"].iloc[0] == "Delivery"

    def test_online_order_bool(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["online_order"].iloc[0] == True

    def test_book_table_bool(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["book_table"].iloc[0] == False

    def test_votes_int(self):
        result = preprocess_dataframe(_make_raw_dataframe())
        assert result["votes"].iloc[0] == 500

    def test_name_stripped(self):
        result = preprocess_dataframe(_make_raw_dataframe(name="  Spice Garden  "))
        assert result["name"].iloc[0] == "Spice Garden"

    def test_new_rating_becomes_none(self):
        result = preprocess_dataframe(_make_raw_dataframe(rate="NEW"))
        assert result["rating"].iloc[0] is None

    def test_missing_cost_becomes_none(self):
        result = preprocess_dataframe(
            _make_raw_dataframe(**{"approx_cost(for two people)": float("nan")})
        )
        assert result["cost_for_two"].iloc[0] is None
        assert result["budget_tier"].iloc[0] is None

    def test_original_df_not_mutated(self):
        raw = _make_raw_dataframe()
        original_rate = raw["rate"].iloc[0]
        _ = preprocess_dataframe(raw)
        assert raw["rate"].iloc[0] == original_rate  # unchanged
