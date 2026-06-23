"""
Deterministic filtering engine.

Applies a cascading filter pipeline to reduce the full restaurant catalogue
to a compact candidate set suitable for LLM ranking.

Filter order (per context.md §7.1 and referenced plan Phase 3):
  1. Location — match locality **or** ``listed_in_city`` (case-insensitive substring).
  2. Cuisine  — contains / substring match against each restaurant's cuisines list.
  3. Budget   — exact tier match (``low`` / ``medium`` / ``high``).
  4. Rating   — minimum rating threshold.
  5. Flags    — optional ``online_order`` and ``book_table`` boolean filters.
  6. Sort     — rating desc → votes desc, truncate to ``MAX_CANDIDATES``.

Auto-relaxation:
  When a non-location filter reduces the pool to zero the engine relaxes
  the **last applied** filter and retries, in reverse priority order:
  ``cuisine → budget → rating → flags``.

The result includes metadata about which filters were applied and which
were relaxed, exposed via :class:`FilterResult`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from src.config import settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# Result container
# ════════════════════════════════════════════════════════════════════════


@dataclass
class FilterResult:
    """Container holding filtered candidates along with metadata.

    Attributes:
        candidates:        Ranked list of restaurants (capped at max_candidates).
        total_after_location: Pool size right after the location filter.
        filters_applied:   List of filter labels that were kept.
        filters_relaxed:   List of filter labels that were dropped
                           because they would have emptied the pool.
    """

    candidates: List[Restaurant] = field(default_factory=list)
    total_after_location: int = 0
    filters_applied: List[str] = field(default_factory=list)
    filters_relaxed: List[str] = field(default_factory=list)


# ════════════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════════════


def filter_restaurants(
    restaurants: List[Restaurant],
    prefs: UserPreferences,
    max_candidates: Optional[int] = None,
) -> FilterResult:
    """Apply cascading filters and return a :class:`FilterResult`.

    Args:
        restaurants: Full catalogue of :class:`Restaurant` objects.
        prefs: User-submitted search preferences.
        max_candidates: Override for :pyattr:`settings.max_candidates_for_llm`.

    Returns:
        A :class:`FilterResult` containing ranked candidates and metadata.
    """
    max_k = max_candidates or settings.max_candidates_for_llm

    # ── 1. Location (hard filter — never relaxed) ───────────────────────
    pool = _filter_location(restaurants, prefs.location)
    total_after_location = len(pool)

    if not pool:
        logger.info("No restaurants matched location '%s'.", prefs.location)
        return FilterResult(
            candidates=[],
            total_after_location=0,
            filters_applied=["location"],
        )

    # ── 2–5. Build optional filter chain ────────────────────────────────
    optional_filters: List[Tuple[Callable[[Restaurant], bool], str]] = []

    # 2 — Cuisine (substring / contains)
    if prefs.cuisine:
        cuisine_lower = prefs.cuisine.strip().lower()
        optional_filters.append((
            lambda r, _c=cuisine_lower: any(
                _c in c.lower() for c in r.cuisines
            ),
            "cuisine",
        ))

    # 3 — Budget tier
    budget = prefs.budget.strip().lower()
    if budget:
        optional_filters.append((
            lambda r, _b=budget: r.budget_tier == _b,
            "budget",
        ))

    # 4 — Minimum rating
    if prefs.min_rating > 0:
        min_r = prefs.min_rating
        optional_filters.append((
            lambda r, _m=min_r: r.rating is not None and r.rating >= _m,
            "rating",
        ))

    # 5 — Boolean service flags
    if prefs.online_order is True:
        optional_filters.append((
            lambda r: r.online_order is True,
            "online_order",
        ))

    if prefs.book_table is True:
        optional_filters.append((
            lambda r: r.book_table is True,
            "book_table",
        ))

    # 5b — Restaurant type (optional)
    if prefs.rest_type:
        rt_lower = prefs.rest_type.strip().lower()
        optional_filters.append((
            lambda r, _rt=rt_lower: (
                r.rest_type is not None and _rt in r.rest_type.lower()
            ),
            "rest_type",
        ))

    # ── Apply with auto-relaxation ──────────────────────────────────────
    pool, applied, relaxed = _apply_with_relaxation(pool, optional_filters)

    # ── 6. Sort, deduplicate, and truncate ──────────────────────────────
    pool.sort(key=lambda r: (r.rating or 0, r.votes), reverse=True)

    seen = set()
    deduped_pool = []
    for r in pool:
        # Use address for deduplication if present; fallback to id (unique in tests)
        addr_key = r.address.lower().strip() if r.address else r.id
        key = (r.name.lower().strip(), addr_key)
        if key not in seen:
            seen.add(key)
            deduped_pool.append(r)
    pool = deduped_pool[:max_k]

    result = FilterResult(
        candidates=pool,
        total_after_location=total_after_location,
        filters_applied=["location"] + applied,
        filters_relaxed=relaxed,
    )

    logger.info(
        "Filter complete: %d candidates (applied=%s, relaxed=%s).",
        len(pool),
        result.filters_applied,
        result.filters_relaxed,
    )
    return result


# ════════════════════════════════════════════════════════════════════════
# Internal helpers
# ════════════════════════════════════════════════════════════════════════


def _filter_location(
    restaurants: List[Restaurant],
    location: str,
) -> List[Restaurant]:
    """Match location against both ``location`` and ``listed_in_city``.

    Uses case-insensitive substring matching so that, for example,
    ``"Koramangala"`` matches ``"Koramangala 5th Block"``.
    """
    loc = location.strip().lower()
    if not loc:
        return list(restaurants)

    return [
        r
        for r in restaurants
        if loc in r.location.lower()
        or (r.listed_in_city and loc in r.listed_in_city.lower())
    ]


def _apply_with_relaxation(
    pool: List[Restaurant],
    filters: List[Tuple[Callable[[Restaurant], bool], str]],
) -> Tuple[List[Restaurant], List[str], List[str]]:
    """Apply filters sequentially, relaxing any that would empty the pool.

    Filters are applied in order.  If a filter reduces the remaining pool
    to zero it is **skipped** (relaxed) rather than applied.

    Returns:
        A 3-tuple: ``(surviving_pool, applied_labels, relaxed_labels)``.
    """
    applied: List[str] = []
    relaxed: List[str] = []
    result = pool

    for fn, label in filters:
        filtered = [r for r in result if fn(r)]
        if filtered:
            result = filtered
            applied.append(label)
        else:
            relaxed.append(label)
            logger.debug("Relaxed filter '%s' (would return 0 results).", label)

    return result, applied, relaxed
