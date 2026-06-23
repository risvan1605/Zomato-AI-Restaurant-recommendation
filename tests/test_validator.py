"""Tests for src.services.validator – Phase 3 coverage."""

import pytest

from src.services.validator import ValidationError, validate_preferences


class TestValidatePreferences:
    """Core validation tests."""

    def test_valid_minimal(self):
        prefs = validate_preferences(location="Koramangala", budget="medium")
        assert prefs.location == "Koramangala"
        assert prefs.budget == "medium"
        assert prefs.min_rating == 0.0
        assert prefs.cuisine is None

    def test_valid_full(self):
        prefs = validate_preferences(
            location="Koramangala",
            budget="High",
            min_rating=4.5,
            cuisine="Italian",
            online_order=True,
            book_table=False,
            rest_type="Fine Dining",
            additional="Family friendly",
        )
        assert prefs.budget == "high"
        assert prefs.min_rating == 4.5
        assert prefs.cuisine == "Italian"
        assert prefs.online_order is True
        assert prefs.book_table is False
        assert prefs.rest_type == "Fine Dining"
        assert prefs.additional == "Family friendly"


class TestLocationValidation:
    def test_empty_location_raises(self):
        with pytest.raises(ValidationError, match="Location is required"):
            validate_preferences(location="", budget="medium")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValidationError, match="Location is required"):
            validate_preferences(location="   ", budget="medium")

    def test_strips_whitespace(self):
        prefs = validate_preferences(location="  Koramangala  ", budget="low")
        assert prefs.location == "Koramangala"

    def test_unknown_location_raises(self):
        with pytest.raises(ValidationError, match="Unknown location"):
            validate_preferences(
                location="Narnia",
                budget="medium",
                known_locations=["Koramangala", "Indiranagar"],
            )

    def test_known_location_case_insensitive(self):
        prefs = validate_preferences(
            location="koramangala",
            budget="medium",
            known_locations=["Koramangala"],
        )
        assert prefs.location == "koramangala"


class TestBudgetValidation:
    def test_invalid_budget_raises(self):
        with pytest.raises(ValidationError, match="Invalid budget tier"):
            validate_preferences(location="Koramangala", budget="luxury")

    def test_normalizes_to_lowercase(self):
        prefs = validate_preferences(location="Koramangala", budget="HIGH")
        assert prefs.budget == "high"


class TestRatingValidation:
    def test_clamps_below_zero(self):
        prefs = validate_preferences(location="K", budget="low", min_rating=-1.0)
        assert prefs.min_rating == 0.0

    def test_clamps_above_five(self):
        prefs = validate_preferences(location="K", budget="low", min_rating=10.0)
        assert prefs.min_rating == 5.0


class TestCuisineValidation:
    def test_unknown_cuisine_raises(self):
        with pytest.raises(ValidationError, match="Unknown cuisine"):
            validate_preferences(
                location="K",
                budget="low",
                cuisine="Martian Food",
                known_cuisines=["Italian", "Chinese"],
            )

    def test_empty_cuisine_becomes_none(self):
        prefs = validate_preferences(location="K", budget="low", cuisine="")
        assert prefs.cuisine is None


class TestTextSanitization:
    def test_strips_control_chars(self):
        prefs = validate_preferences(
            location="Koramangala",
            budget="low",
            additional="Good \x00food \x07please",
        )
        assert "\x00" not in prefs.additional
        assert "\x07" not in prefs.additional

    def test_truncates_long_text(self):
        prefs = validate_preferences(
            location="K",
            budget="low",
            additional="a" * 1000,
        )
        assert len(prefs.additional) <= 500
