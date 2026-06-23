"""
Dataset loader.

Downloads the Zomato restaurant dataset from Hugging Face on first run,
preprocesses it, then caches the result as a local Parquet file at
``cache/zomato_preprocessed.parquet`` for sub-second startup on later runs.

The loader handles the two-step pipeline:
  1. Download raw data from HF  →  convert to pandas
  2. Run the preprocessor       →  persist as Parquet

Subsequent calls skip both steps and read directly from the cached file.

Hardening (Phase 5):
  • Corrupted cache recovery — auto-delete and re-download.
  • Schema validation — verify mandatory columns exist after load.
  • Offline detection — friendly error when HF is unreachable and no cache.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from src.config import settings
from src.services.errors import DatasetUnavailableError, SchemaError

logger = logging.getLogger(__name__)

# Parquet filename for the fully-preprocessed snapshot.
_CACHE_FILENAME = "zomato_preprocessed.parquet"

# Mandatory columns that must exist after preprocessing.
# We check for both raw and preprocessed variants so the validator
# works on both fresh HF downloads and cached Parquet files.
_REQUIRED_COLUMNS_RAW = {"name", "location"}
_REQUIRED_COLUMNS_RATINGS = {"rate", "rating"}        # at least one
_REQUIRED_COLUMNS_CUISINES = {"cuisines", "cuisines_list"}  # at least one


def _validate_schema(df: pd.DataFrame, *, source: str) -> None:
    """Raise :class:`SchemaError` if mandatory columns are missing.

    Args:
        df: The DataFrame to validate.
        source: Human-readable source label for error messages
            (e.g. ``"Hugging Face"`` or ``"Parquet cache"``).
    """
    cols = set(df.columns)

    missing_core = _REQUIRED_COLUMNS_RAW - cols
    if missing_core:
        raise SchemaError(
            f"Dataset from {source} is missing mandatory columns: {missing_core}. "
            "The upstream Hugging Face schema may have changed."
        )

    if not (_REQUIRED_COLUMNS_RATINGS & cols):
        raise SchemaError(
            f"Dataset from {source} has neither 'rate' nor 'rating' column. "
            "Cannot determine restaurant ratings."
        )

    if not (_REQUIRED_COLUMNS_CUISINES & cols):
        raise SchemaError(
            f"Dataset from {source} has neither 'cuisines' nor 'cuisines_list' column. "
            "Cannot determine restaurant cuisines."
        )


def load_dataset_cached(*, force_reload: bool = False) -> pd.DataFrame:
    """Load (and optionally re-download) the Zomato dataset.

    On the **first run** the function will:
      1. Download the raw dataset from Hugging Face (~574 MB).
      2. Run full preprocessing (rating parsing, cost cleaning, etc.).
      3. Persist the result as ``<cache_dir>/zomato_preprocessed.parquet``.

    On **subsequent runs** it reads straight from the cached Parquet file,
    providing sub-second startup.

    Hardening:
      • If the cached Parquet is corrupted, it is deleted and re-downloaded.
      • If HF is unreachable and no cache exists, a user-friendly
        :class:`DatasetUnavailableError` is raised.
      • After loading, mandatory columns are validated.

    Args:
        force_reload: When ``True``, re-download from HF and overwrite
            the local cache even if it already exists.

    Returns:
        A preprocessed :class:`~pandas.DataFrame` ready for querying.

    Raises:
        SchemaError: If mandatory columns are missing.
        DatasetUnavailableError: If HF is unreachable and no cache exists.
    """
    cache_dir = Path(settings.data_cache_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = cache_dir / _CACHE_FILENAME

    # ── Try reading from cache ──────────────────────────────────────────
    if parquet_path.exists() and not force_reload:
        try:
            logger.info("Loading preprocessed cache from %s", parquet_path)
            df = pd.read_parquet(parquet_path)
            _validate_schema(df, source="Parquet cache")
            return df
        except SchemaError:
            raise  # schema issues are not recoverable by re-reading
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Cache file %s appears corrupted (%s: %s). "
                "Deleting and re-downloading …",
                parquet_path,
                type(exc).__name__,
                exc,
            )
            try:
                os.remove(parquet_path)
            except OSError:
                pass  # best-effort cleanup

    # ── First run / cache miss: download → preprocess → persist ─────────
    logger.info(
        "Downloading dataset '%s' from Hugging Face …", settings.hf_dataset_name,
    )

    try:
        from datasets import load_dataset  # noqa: E402
        ds = load_dataset(settings.hf_dataset_name, split="train")
        # ── Prevent OOM: Drop heavy columns before Pandas conversion ────────
        drop_cols = [c for c in ["reviews_list", "menu_item"] if c in ds.column_names]
        if drop_cols:
            ds = ds.remove_columns(drop_cols)
    except Exception as exc:  # noqa: BLE001
        # Distinguish between "no internet" and other failures
        err_name = type(exc).__name__
        if any(tok in err_name for tok in ("ConnectionError", "ConnectTimeout", "OSError")):
            raise DatasetUnavailableError(
                "Cannot reach Hugging Face and no local cache exists. "
                "Please connect to the internet and try again."
            ) from exc
        # For all other errors (auth, dataset not found, etc.) re-raise
        raise DatasetUnavailableError(
            f"Failed to download dataset from Hugging Face: {exc}"
        ) from exc

    raw_df = ds.to_pandas()
    logger.info("Downloaded %d rows. Running preprocessor …", len(raw_df))

    # Validate the raw schema before preprocessing
    _validate_schema(raw_df, source="Hugging Face")

    # Import here to avoid circular imports (preprocessor imports settings).
    from src.data.preprocessor import preprocess_dataframe  # noqa: E402

    processed_df = preprocess_dataframe(raw_df)

    processed_df.to_parquet(parquet_path, index=False)
    logger.info("Cached preprocessed data to %s", parquet_path)

    return processed_df
