"""
Centralized exception hierarchy for the restaurant recommendation system.

All custom exceptions inherit from a common ``RecommendationError`` base
so callers can catch broadly or narrowly as needed.
"""

from __future__ import annotations


class RecommendationError(Exception):
    """Base exception for all recommendation system errors."""


class ConfigurationError(RecommendationError):
    """Missing or invalid configuration (e.g. API key, model settings)."""


class DatasetUnavailableError(RecommendationError):
    """Hugging Face download failed and no local cache exists."""


class SchemaError(RecommendationError):
    """Upstream dataset schema has changed — mandatory columns are missing."""


class HallucinationError(RecommendationError):
    """LLM produced only invalid / hallucinated recommendations.

    Raised when *every* recommendation returned by the LLM fails
    the candidate cross-reference check, meaning none map back to the
    filtered candidate set.
    """
