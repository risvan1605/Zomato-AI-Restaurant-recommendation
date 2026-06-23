"""
Data preprocessor.

Cleans and normalizes raw Zomato dataset columns into structured,
query-friendly formats used by the filtering engine and LLM prompt builder.

Handles all 17 source columns documented in context.md §5.3:
  url, address, name, online_order, book_table, rate, votes, phone,
  location, rest_type, dish_liked, cuisines, approx_cost(for two people),
  reviews_list, menu_item, listed_in(type), listed_in(city)
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd

from src.config import settings

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════
# Helper parsers — kept module-private but importable for unit tests.
# ════════════════════════════════════════════════════════════════════════


def _parse_rating(value: object) -> Optional[float]:
    """Convert raw rating strings like ``'4.1/5'``, ``'NEW'``, ``'-'`` to float or None.

    Examples
    --------
    >>> _parse_rating("4.1/5")
    4.1
    >>> _parse_rating("NEW")  # returns None
    >>> _parse_rating("-")    # returns None
    >>> _parse_rating(3.8)
    3.8
    """
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.upper() in ("NEW", "-", "", "NONE"):
        return None
    match = re.match(r"(\d+\.?\d*)", text)
    return float(match.group(1)) if match else None


def _parse_cost(value: object) -> Optional[int]:
    """Parse ``approx_cost(for two people)`` to an integer.

    Strips commas, currency symbols, and whitespace.  Returns ``None`` for
    un-parseable or missing values.

    Examples
    --------
    >>> _parse_cost("800")
    800
    >>> _parse_cost("1,200")
    1200
    >>> _parse_cost("₹1,200")
    1200
    """
    if pd.isna(value):
        return None
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def _classify_budget(cost: Optional[int]) -> Optional[str]:
    """Map a numeric cost to a budget tier: ``low`` | ``medium`` | ``high``.

    Thresholds are read from :pyattr:`settings.budget_low_max` and
    :pyattr:`settings.budget_medium_max`.  Returns ``None`` when *cost*
    is ``None``.
    """
    if cost is None:
        return None
    if cost <= settings.budget_low_max:
        return "low"
    if cost <= settings.budget_medium_max:
        return "medium"
    return "high"


def _split_cuisines(value: object) -> list[str]:
    """Split a comma-separated cuisines string into a trimmed list.

    Examples
    --------
    >>> _split_cuisines("Italian, Chinese, Thai")
    ['Italian', 'Chinese', 'Thai']
    >>> _split_cuisines(float('nan'))
    []
    """
    if pd.isna(value):
        return []
    return [c.strip() for c in str(value).split(",") if c.strip()]


def _parse_bool_flag(value: object) -> bool:
    """Convert ``'Yes'``/``'No'`` strings to Python booleans.

    Anything other than a case-insensitive ``'yes'`` is treated as ``False``.
    """
    if pd.isna(value):
        return False
    return str(value).strip().lower() == "yes"


def _clean_text(value: object) -> Optional[str]:
    """Trim whitespace from text fields; return ``None`` for empty / NaN."""
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text if text else None


def _normalize_name(value: object) -> str:
    """Strip and title-case a location / city name."""
    if pd.isna(value):
        return ""
    return str(value).strip().title()


def _parse_votes(value: object) -> int:
    """Safely coerce votes to ``int``, defaulting to ``0``."""
    if pd.isna(value):
        return 0
    try:
        return int(float(str(value).replace(",", "")))
    except (ValueError, TypeError):
        return 0


# ════════════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════════════


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning and normalization steps to the raw Zomato dataset.

    This function operates on a **copy** of the incoming DataFrame and is
    safe to call on both fresh HF downloads and previously cached data.

    Transformations:
      * ``rate``            → ``rating`` (float)
      * ``approx_cost(…)``  → ``cost_for_two`` (int) + ``budget_tier``
      * ``cuisines``        → ``cuisines_list`` (List[str])
      * ``online_order``    → ``online_order`` (bool)
      * ``book_table``      → ``book_table`` (bool)
      * ``location``        → title-cased
      * ``listed_in(city)`` → ``listed_in_city`` (title-cased)
      * ``listed_in(type)`` → ``listed_in_type`` (stripped)
      * ``votes``           → coerced to int
      * ``rest_type``       → stripped
      * ``dish_liked``      → stripped (nullable)
      * ``address``         → stripped (nullable)
      * ``phone``           → stripped (nullable)
      * ``url``             → stripped (nullable)

    Args:
        df: Raw DataFrame straight from HF ``datasets`` or a cached Parquet.

    Returns:
        Cleaned DataFrame with standardized, ready-to-query columns.
    """
    # ── Drop oversized columns immediately to prevent OOM ───────────────
    # reviews_list and menu_item contain massive text blocks and are unused.
    # Dropping them before copying saves ~300MB of RAM during processing.
    drop_cols = [c for c in ["reviews_list", "menu_item"] if c in df.columns]
    out = df.drop(columns=drop_cols) if drop_cols else df.copy()
    
    total = len(out)
    logger.info("Preprocessing %d rows …", total)

    # ── Ratings ─────────────────────────────────────────────────────────
    if "rate" in out.columns:
        out["rating"] = out["rate"].apply(_parse_rating)
    elif "rating" not in out.columns:
        out["rating"] = None

    # ── Cost & budget tier ──────────────────────────────────────────────
    cost_col = (
        "approx_cost(for two people)"
        if "approx_cost(for two people)" in out.columns
        else "cost"
    )
    if cost_col in out.columns:
        out["cost_for_two"] = out[cost_col].apply(_parse_cost)
    elif "cost_for_two" not in out.columns:
        out["cost_for_two"] = None

    out["budget_tier"] = out["cost_for_two"].apply(_classify_budget)

    # ── Cuisines ────────────────────────────────────────────────────────
    if "cuisines" in out.columns:
        out["cuisines_list"] = out["cuisines"].apply(_split_cuisines)
    elif "cuisines_list" not in out.columns:
        out["cuisines_list"] = [[] for _ in range(total)]

    # ── Boolean service flags ───────────────────────────────────────────
    if "online_order" in out.columns:
        out["online_order"] = out["online_order"].apply(_parse_bool_flag)
    elif "online_order" not in out.columns:
        out["online_order"] = False

    if "book_table" in out.columns:
        out["book_table"] = out["book_table"].apply(_parse_bool_flag)
    elif "book_table" not in out.columns:
        out["book_table"] = False

    # ── Votes ───────────────────────────────────────────────────────────
    if "votes" in out.columns:
        out["votes"] = out["votes"].apply(_parse_votes)

    # ── Location normalization ──────────────────────────────────────────
    for col in ("location",):
        if col in out.columns:
            out[col] = out[col].apply(_normalize_name)

    # listed_in(city) → listed_in_city
    if "listed_in(city)" in out.columns:
        out["listed_in_city"] = out["listed_in(city)"].apply(_normalize_name)
    elif "listed_in_city" not in out.columns:
        out["listed_in_city"] = ""

    # listed_in(type) → listed_in_type
    if "listed_in(type)" in out.columns:
        out["listed_in_type"] = out["listed_in(type)"].apply(_clean_text)
    elif "listed_in_type" not in out.columns:
        out["listed_in_type"] = None

    # ── Text cleanup ────────────────────────────────────────────────────
    for col in ("rest_type", "dish_liked", "address", "phone", "url"):
        if col in out.columns:
            out[col] = out[col].apply(_clean_text)

    # ── Name ────────────────────────────────────────────────────────────
    if "name" in out.columns:
        out["name"] = out["name"].astype(str).str.strip()

    # ── Drop oversized columns that won't be used in filtering ──────────
    # reviews_list and menu_item are excluded from the LLM prompt
    # (context.md §5.4) to avoid token-limit issues.
    # We keep them in the DataFrame in case they're needed later,
    # but they are NOT mapped into the Restaurant domain model.

    logger.info("Preprocessing complete.  %d rows ready.", total)
    return out
