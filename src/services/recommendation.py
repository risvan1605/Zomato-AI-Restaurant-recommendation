"""
Recommendation orchestrator.

Central service that wires together:
  Preferences → Filter → CandidateMapper → PromptBuilder → LLMClient
  → ResponseValidator → RecommendationResponse

Includes a metric-based fallback (rating/votes desc) when Groq is unavailable.

Phase 5 hardening:
  • Uses ``response_validator`` for anti-hallucination cross-referencing.
  • Catches ``HallucinationError`` and falls back to metric ranking.
  • Logs latency and token usage via the LLM client metadata.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.recommendation import Recommendation, RecommendationResponse
from src.models.restaurant import Restaurant
from src.services.errors import ConfigurationError, HallucinationError
from src.services.filter import FilterResult, filter_restaurants
from src.services.llm_client import LLMClient
from src.services.prompt_builder import build_system_prompt, build_user_prompt
from src.services.response_validator import validate_response

logger = logging.getLogger(__name__)


class RecommendationService:
    """Orchestrates the full recommendation pipeline."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client or LLMClient()

    def recommend(
        self,
        restaurants: List[Restaurant],
        prefs: UserPreferences,
    ) -> RecommendationResponse:
        """Run the recommendation pipeline end-to-end.

        Args:
            restaurants: Full restaurant catalog.
            prefs: Validated user preferences.

        Returns:
            A :class:`RecommendationResponse` with ranked recommendations.
        """
        # Step 1 ─ Deterministic filtering
        filter_result: FilterResult = filter_restaurants(restaurants, prefs)

        if not filter_result.candidates:
            return RecommendationResponse(
                summary="No restaurants matched your criteria.",
                metadata={
                    "candidates_considered": 0,
                    "filters_applied": filter_result.filters_applied,
                    "filters_relaxed": filter_result.filters_relaxed,
                    "model": "",
                },
            )

        candidates = filter_result.candidates

        # Step 2 ─ LLM ranking (with fallback)
        try:
            response = self._rank_with_llm(candidates, prefs)
        except ConfigurationError:
            # API key missing — fall back but also propagate the reason
            logger.warning("Groq API key not configured; using fallback ranking.")
            response = self._fallback_ranking(candidates, prefs)
            response.metadata["fallback_reason"] = "api_key_missing"
        except HallucinationError as exc:
            logger.warning("All LLM recommendations hallucinated: %s", exc)
            response = self._fallback_ranking(candidates, prefs)
            response.metadata["fallback_reason"] = "hallucination"
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM ranking failed (%s: %s); using fallback.", type(exc).__name__, exc)
            response = self._fallback_ranking(candidates, prefs)
            response.metadata["fallback_reason"] = str(type(exc).__name__)

        # Enrich metadata from filter result
        response.metadata["candidates_considered"] = len(candidates)
        response.metadata["total_after_location"] = filter_result.total_after_location
        response.metadata["filters_applied"] = filter_result.filters_applied
        response.metadata["filters_relaxed"] = filter_result.filters_relaxed
        return response

    # ── Private helpers ─────────────────────────────────────────────────

    def _rank_with_llm(
        self,
        candidates: List[Restaurant],
        prefs: UserPreferences,
    ) -> RecommendationResponse:
        """Use Groq to rank and explain recommendations.

        Delegates hallucination detection to ``response_validator``.
        """
        t0 = time.monotonic()

        system = build_system_prompt()
        user = build_user_prompt(prefs, candidates)
        data = self._llm.complete_json(system, user)

        latency_ms = (time.monotonic() - t0) * 1000
        logger.info("LLM ranking pipeline completed in %.0fms", latency_ms)

        # ── Validate & cross-reference (Phase 5) ───────────────────────
        matched, summary = validate_response(data, candidates)

        recs = []
        for item in matched:
            restaurant = item["_matched_restaurant"]
            recs.append(
                Recommendation(
                    rank=len(recs) + 1,
                    name=restaurant.name,
                    cuisine=(
                        ", ".join(restaurant.cuisines)
                        if len(restaurant.cuisines) > 0
                        else ""
                    ),
                    rating=restaurant.rating,
                    estimated_cost=restaurant.cost_for_two,
                    votes=restaurant.votes,
                    budget_tier=restaurant.budget_tier or "Unknown",
                    rest_type=restaurant.rest_type,
                    online_order=restaurant.online_order,
                    book_table=restaurant.book_table,
                    explanation=item.get("explanation", ""),
                )
            )

        return RecommendationResponse(
            recommendations=recs,
            summary=summary,
            metadata={
                "model": settings.groq_model,
                "llm_latency_ms": round(latency_ms, 1),
            },
        )

    @staticmethod
    def _fallback_ranking(
        candidates: List[Restaurant],
        prefs: UserPreferences,
    ) -> RecommendationResponse:
        """Pure metric-based fallback when LLM is unavailable."""
        top = candidates[: settings.top_k_recommendations]
        recs = [
            Recommendation(
                rank=idx + 1,
                name=r.name,
                cuisine=", ".join(r.cuisines),
                rating=r.rating,
                estimated_cost=r.cost_for_two,
                votes=r.votes,
                budget_tier=r.budget_tier or "Unknown",
                rest_type=r.rest_type,
                online_order=r.online_order,
                book_table=r.book_table,
                explanation="Ranked by rating and popularity (LLM unavailable).",
            )
            for idx, r in enumerate(top)
        ]
        return RecommendationResponse(
            recommendations=recs,
            summary="Results ranked by rating and votes (LLM fallback).",
            metadata={"model": "fallback-metric"},
        )
