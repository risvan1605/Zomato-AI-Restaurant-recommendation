"""
LLM response validator.

Sanitises raw LLM output and cross-references recommendations against the
original candidate set to prevent hallucinations from reaching the UI.

Pipeline:
  1. Strip markdown code fences (`` ```json ... ``` ``).
  2. Parse JSON and normalise alternative key names.
  3. Cross-reference each recommendation against valid candidates.
  4. Discard unmatched entries; raise :class:`HallucinationError` if *all*
     are invalid.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.models.restaurant import Restaurant
from src.services.errors import HallucinationError

logger = logging.getLogger(__name__)

# Regex to strip markdown fences: ```json ... ``` or ``` ... ```
_FENCE_RE = re.compile(
    r"```(?:json)?\s*\n?(.*?)\n?\s*```",
    re.DOTALL,
)

# Known alternative key names the LLM might use for the recommendations list.
_RECOMMENDATION_KEY_ALIASES = (
    "recommendations",
    "recs",
    "results",
    "restaurants",
)


# ════════════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════════════


def strip_markdown_fences(raw: str) -> str:
    """Remove markdown code fences from raw LLM output.

    If the text is wrapped in `` ```json ... ``` `` (or plain `` ``` ``),
    extract the inner content.  Otherwise return the string unchanged.
    """
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def parse_llm_json(raw: str) -> Dict[str, Any]:
    """Parse raw LLM text to a JSON dict, stripping fences first.

    Args:
        raw: Raw string from ``response.choices[0].message.content``.

    Returns:
        Parsed dict.

    Raises:
        json.JSONDecodeError: If the content is not valid JSON after
            fence stripping.
    """
    cleaned = strip_markdown_fences(raw)
    return json.loads(cleaned)


def extract_recommendations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Find the recommendations list in the parsed JSON.

    Tries known key aliases (``recommendations``, ``recs``, ``results``,
    ``restaurants``) in order and returns the first match.

    Args:
        data: Parsed JSON dict from the LLM.

    Returns:
        List of recommendation dicts (possibly empty).
    """
    for key in _RECOMMENDATION_KEY_ALIASES:
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


def cross_reference_candidates(
    llm_recs: List[Dict[str, Any]],
    candidates: List[Restaurant],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Match LLM recommendations to valid candidates.

    For each LLM recommendation, attempts matching in order:
      1. Exact ``id`` match.
      2. Case-insensitive exact ``name`` match.
      3. Fuzzy substring ``name`` match (LLM name contained in candidate
         name, or vice versa).

    Args:
        llm_recs: Raw recommendation dicts from the LLM.
        candidates: The filtered candidate set that was sent to the LLM.

    Returns:
        A 2-tuple:
          - ``matched``: Recommendations that mapped to a valid candidate.
            Each dict is augmented with a ``"_matched_restaurant"`` key
            pointing to the :class:`Restaurant` object.
          - ``rejected``: Recommendations that could not be matched.
    """
    # Build lookup structures
    by_id: Dict[str, Restaurant] = {r.id: r for r in candidates if r.id}
    by_name: Dict[str, Restaurant] = {
        r.name.lower().strip(): r for r in candidates
    }

    matched: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for item in llm_recs:
        restaurant = _match_single(item, by_id, by_name)
        if restaurant:
            item["_matched_restaurant"] = restaurant
            matched.append(item)
        else:
            rejected.append(item)
            logger.warning(
                "Rejected hallucinated recommendation: id=%s, name=%s",
                item.get("id", "?"),
                item.get("name", "?"),
            )

    return matched, rejected


def validate_response(
    raw_json: Dict[str, Any],
    candidates: List[Restaurant],
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Full validation pipeline: extract, cross-reference, raise on all-bad.

    Args:
        raw_json: Parsed JSON dict from the LLM.
        candidates: The filtered candidate set.

    Returns:
        A 2-tuple of (matched recommendations, summary string or None).

    Raises:
        HallucinationError: If every recommendation is rejected.
    """
    recs = extract_recommendations(raw_json)
    summary = raw_json.get("summary")

    if not recs:
        raise HallucinationError(
            "LLM response did not contain a 'recommendations' list."
        )

    matched, rejected = cross_reference_candidates(recs, candidates)

    if rejected:
        logger.info(
            "Discarded %d hallucinated recommendation(s) out of %d total.",
            len(rejected),
            len(recs),
        )

    if not matched:
        raise HallucinationError(
            f"All {len(recs)} LLM recommendations were hallucinated "
            "(none matched the candidate set)."
        )

    return matched, summary


# ════════════════════════════════════════════════════════════════════════
# Internal helpers
# ════════════════════════════════════════════════════════════════════════


def _match_single(
    item: Dict[str, Any],
    by_id: Dict[str, Restaurant],
    by_name: Dict[str, Restaurant],
) -> Optional[Restaurant]:
    """Try to match a single LLM recommendation to a candidate."""
    # 1. Exact ID match
    item_id = str(item.get("id", "")).strip()
    if item_id and item_id in by_id:
        return by_id[item_id]

    # 2. Exact case-insensitive name match
    item_name = str(item.get("name", "")).lower().strip()
    if item_name and item_name in by_name:
        return by_name[item_name]

    # 3. Fuzzy substring match (either direction)
    if item_name:
        for cand_name, restaurant in by_name.items():
            if item_name in cand_name or cand_name in item_name:
                return restaurant

    return None
