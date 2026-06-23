"""
Unit tests for ``src.services.response_validator``.

Covers:
  • Markdown fence stripping.
  • JSON parsing with fence-wrapped content.
  • Schema validation (missing ``recommendations`` key, alternative key names).
  • Anti-hallucination cross-referencing (valid IDs pass, invalid discarded,
    all-hallucinated triggers error).
  • Fuzzy name matching edge cases.
"""

from __future__ import annotations

import json

import pytest

from src.models.restaurant import Restaurant
from src.services.errors import HallucinationError
from src.services.response_validator import (
    cross_reference_candidates,
    extract_recommendations,
    parse_llm_json,
    strip_markdown_fences,
    validate_response,
)


# ════════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════════


def _make_restaurant(
    id: str = "1",
    name: str = "Jalsa",
    **kwargs,
) -> Restaurant:
    return Restaurant(
        id=id,
        name=name,
        location=kwargs.get("location", "Banashankari"),
        cuisines=kwargs.get("cuisines", ["North Indian"]),
        rating=kwargs.get("rating", 4.2),
        votes=kwargs.get("votes", 500),
        cost_for_two=kwargs.get("cost_for_two", 800),
    )


@pytest.fixture
def sample_candidates() -> list[Restaurant]:
    return [
        _make_restaurant("10", "Jalsa"),
        _make_restaurant("20", "Spice Curry House"),
        _make_restaurant("30", "The Pasta Place"),
    ]


# ════════════════════════════════════════════════════════════════════════
# Markdown fence stripping
# ════════════════════════════════════════════════════════════════════════


class TestStripMarkdownFences:
    def test_no_fences(self):
        raw = '{"summary": "hello"}'
        assert strip_markdown_fences(raw) == raw.strip()

    def test_json_fence(self):
        raw = '```json\n{"summary": "hello"}\n```'
        assert strip_markdown_fences(raw) == '{"summary": "hello"}'

    def test_plain_fence(self):
        raw = '```\n{"data": 1}\n```'
        assert strip_markdown_fences(raw) == '{"data": 1}'

    def test_fence_with_extra_whitespace(self):
        raw = '  ```json\n  {"key": "val"}  \n```  '
        result = strip_markdown_fences(raw)
        assert json.loads(result) == {"key": "val"}

    def test_text_before_fence(self):
        raw = 'Here is the JSON:\n```json\n{"a": 1}\n```'
        result = strip_markdown_fences(raw)
        assert json.loads(result) == {"a": 1}


# ════════════════════════════════════════════════════════════════════════
# JSON parsing
# ════════════════════════════════════════════════════════════════════════


class TestParseLLMJson:
    def test_plain_json(self):
        raw = '{"recommendations": []}'
        assert parse_llm_json(raw) == {"recommendations": []}

    def test_fenced_json(self):
        raw = '```json\n{"summary": "ok", "recommendations": []}\n```'
        result = parse_llm_json(raw)
        assert result["summary"] == "ok"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_json("not json at all")


# ════════════════════════════════════════════════════════════════════════
# Recommendation key extraction
# ════════════════════════════════════════════════════════════════════════


class TestExtractRecommendations:
    def test_standard_key(self):
        data = {"recommendations": [{"id": "1"}]}
        assert len(extract_recommendations(data)) == 1

    def test_alias_recs(self):
        data = {"recs": [{"id": "1"}, {"id": "2"}]}
        assert len(extract_recommendations(data)) == 2

    def test_alias_results(self):
        data = {"results": [{"id": "1"}]}
        assert len(extract_recommendations(data)) == 1

    def test_alias_restaurants(self):
        data = {"restaurants": [{"id": "1"}]}
        assert len(extract_recommendations(data)) == 1

    def test_missing_key(self):
        data = {"summary": "hello"}
        assert extract_recommendations(data) == []

    def test_non_list_value(self):
        data = {"recommendations": "not a list"}
        assert extract_recommendations(data) == []


# ════════════════════════════════════════════════════════════════════════
# Cross-reference (anti-hallucination)
# ════════════════════════════════════════════════════════════════════════


class TestCrossReferenceCandidates:
    def test_exact_id_match(self, sample_candidates):
        llm_recs = [{"id": "10", "name": "Jalsa", "explanation": "Great"}]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 1
        assert len(rejected) == 0
        assert matched[0]["_matched_restaurant"].name == "Jalsa"

    def test_exact_name_match_case_insensitive(self, sample_candidates):
        llm_recs = [{"id": "999", "name": "spice curry house", "explanation": "Nice"}]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 1
        assert matched[0]["_matched_restaurant"].name == "Spice Curry House"

    def test_fuzzy_substring_match(self, sample_candidates):
        # LLM returns "Pasta Place" which is a substring of "The Pasta Place"
        llm_recs = [{"id": "999", "name": "Pasta Place", "explanation": "Good"}]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 1
        assert matched[0]["_matched_restaurant"].name == "The Pasta Place"

    def test_hallucinated_entry_rejected(self, sample_candidates):
        llm_recs = [{"id": "999", "name": "Completely Fake Restaurant"}]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 0
        assert len(rejected) == 1

    def test_mixed_valid_and_hallucinated(self, sample_candidates):
        llm_recs = [
            {"id": "10", "name": "Jalsa", "explanation": "Best"},
            {"id": "999", "name": "Fake Place"},
        ]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 1
        assert len(rejected) == 1

    def test_all_hallucinated(self, sample_candidates):
        llm_recs = [
            {"id": "888", "name": "Totally Made Up"},
            {"id": "777", "name": "Another Fake"},
        ]
        matched, rejected = cross_reference_candidates(llm_recs, sample_candidates)
        assert len(matched) == 0
        assert len(rejected) == 2


# ════════════════════════════════════════════════════════════════════════
# Full validation pipeline
# ════════════════════════════════════════════════════════════════════════


class TestValidateResponse:
    def test_valid_response(self, sample_candidates):
        data = {
            "summary": "Here are your picks.",
            "recommendations": [
                {"id": "10", "name": "Jalsa", "explanation": "Excellent"},
                {"id": "20", "name": "Spice Curry House", "explanation": "Tasty"},
            ],
        }
        matched, summary = validate_response(data, sample_candidates)
        assert len(matched) == 2
        assert summary == "Here are your picks."

    def test_no_recommendations_key_raises(self, sample_candidates):
        data = {"summary": "Hello"}
        with pytest.raises(HallucinationError, match="did not contain"):
            validate_response(data, sample_candidates)

    def test_all_hallucinated_raises(self, sample_candidates):
        data = {
            "recommendations": [
                {"id": "999", "name": "Fake Restaurant"},
            ],
        }
        with pytest.raises(HallucinationError, match="hallucinated"):
            validate_response(data, sample_candidates)

    def test_partial_hallucination_keeps_valid(self, sample_candidates):
        data = {
            "summary": "Mixed results",
            "recommendations": [
                {"id": "10", "name": "Jalsa", "explanation": "Good"},
                {"id": "999", "name": "Ghost Kitchen"},
            ],
        }
        matched, summary = validate_response(data, sample_candidates)
        assert len(matched) == 1
        assert matched[0]["_matched_restaurant"].name == "Jalsa"

    def test_alternative_key_name(self, sample_candidates):
        data = {
            "recs": [
                {"id": "10", "name": "Jalsa", "explanation": "Good"},
            ],
        }
        matched, _ = validate_response(data, sample_candidates)
        assert len(matched) == 1
