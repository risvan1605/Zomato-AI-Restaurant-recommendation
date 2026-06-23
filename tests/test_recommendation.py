"""Tests for src.services.recommendation (with mocked LLM)."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.recommendation import RecommendationService


def _sample_restaurants():
    return [
        Restaurant(
            id="1", name="Spice Garden", location="Koramangala",
            cuisines=["North Indian", "Chinese"], cost_for_two=900,
            rating=4.3, votes=500, rest_type="Casual Dining", budget_tier="medium",
        ),
        Restaurant(
            id="2", name="Pasta Place", location="Koramangala",
            cuisines=["Italian"], cost_for_two=1200,
            rating=4.5, votes=300, rest_type="Fine Dining", budget_tier="medium",
        ),
    ]


def _mock_llm_response() -> Dict[str, Any]:
    return {
        "summary": "Great options in Koramangala!",
        "recommendations": [
            {
                "id": "2",
                "rank": 1,
                "name": "Pasta Place",
                "cuisine": "Italian",
                "rating": 4.5,
                "estimated_cost": 1200,
                "explanation": "Top-rated Italian in the area.",
            },
        ],
    }


class TestRecommendationService:
    def test_recommend_with_mocked_llm(self):
        mock_client = MagicMock()
        mock_client.complete_json.return_value = _mock_llm_response()

        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="Koramangala", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        assert result.summary == "Great options in Koramangala!"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].name == "Pasta Place"
        assert result.recommendations[0].cuisine == "Italian"
        assert result.recommendations[0].rating == 4.5
        assert result.recommendations[0].estimated_cost == 1200
        assert result.recommendations[0].explanation == "Top-rated Italian in the area."

    def test_recommend_with_fallback_name_matching(self):
        # Test that if the ID is missing/invalid, matching falls back to name.
        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "summary": "Great options in Koramangala!",
            "recommendations": [
                {
                    "id": "999",  # non-existent ID
                    "name": "Spice Garden",
                    "explanation": "Great North Indian food.",
                }
            ],
        }

        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="Koramangala", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        assert len(result.recommendations) == 1
        assert result.recommendations[0].name == "Spice Garden"
        assert result.recommendations[0].cuisine == "North Indian, Chinese"  # enriched!

    def test_recommend_filters_hallucinations(self):
        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "summary": "Great options!",
            "recommendations": [
                {
                    "id": "2",
                    "name": "Pasta Place",
                    "explanation": "Valid restaurant.",
                },
                {
                    "id": "999",
                    "name": "Imaginary Bistro",
                    "explanation": "Hallucinated restaurant.",
                }
            ],
        }

        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="Koramangala", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        # Imaginary Bistro should be filtered out
        assert len(result.recommendations) == 1
        assert result.recommendations[0].name == "Pasta Place"
        assert result.recommendations[0].rank == 1

    def test_fallback_on_all_hallucinations(self):
        mock_client = MagicMock()
        mock_client.complete_json.return_value = {
            "summary": "Great options!",
            "recommendations": [
                {
                    "id": "999",
                    "name": "Imaginary Bistro",
                    "explanation": "Hallucinated restaurant.",
                }
            ],
        }

        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="Koramangala", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        # Should fall back to metric-based ranking since no valid candidates survived
        assert result.metadata["model"] == "fallback-metric"
        assert len(result.recommendations) > 0

    def test_fallback_on_llm_failure(self):
        mock_client = MagicMock()
        mock_client.complete_json.side_effect = RuntimeError("API down")

        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="Koramangala", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        # Should fall back to metric-based ranking
        assert result.metadata["model"] == "fallback-metric"
        assert len(result.recommendations) > 0

    def test_empty_result_for_no_matching_location(self):
        mock_client = MagicMock()
        service = RecommendationService(llm_client=mock_client)
        prefs = UserPreferences(location="NonExistent", budget="medium")
        result = service.recommend(_sample_restaurants(), prefs)

        assert result.recommendations == []
        assert result.metadata["candidates_considered"] == 0

