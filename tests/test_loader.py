"""Tests for src.data.loader – Phase 2 coverage.

Uses monkeypatching to avoid real network calls to Hugging Face.
Verifies caching behaviour (read from Parquet on subsequent calls)
and the force_reload flag.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import importlib

import pandas as pd
import pytest


def _dummy_raw_df() -> pd.DataFrame:
    """A minimal DataFrame pretending to be the raw HF download."""
    return pd.DataFrame(
        {
            "name": ["Test Cafe"],
            "rate": ["4.1/5"],
            "votes": [100],
            "approx_cost(for two people)": ["800"],
            "cuisines": ["Italian"],
            "location": ["koramangala"],
            "online_order": ["Yes"],
            "book_table": ["No"],
            "listed_in(city)": ["bangalore"],
            "listed_in(type)": ["Delivery"],
        }
    )


@pytest.fixture()
def cache_dir(tmp_path, monkeypatch):
    """Point settings.data_cache_path to a tmp dir for isolation."""
    monkeypatch.setattr(
        "src.config.settings.data_cache_path", tmp_path,
    )
    return tmp_path


class TestLoadDatasetCached:
    def test_first_call_downloads_and_caches(self, cache_dir):
        """On first run the loader should call HF, preprocess, and write Parquet."""
        dummy = _dummy_raw_df()
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = dummy

        with patch("datasets.load_dataset", return_value=mock_ds) as mock_load:
            from src.data.loader import load_dataset_cached

            result = load_dataset_cached(force_reload=True)

        mock_load.assert_called_once()
        parquet = cache_dir / "zomato_preprocessed.parquet"
        assert parquet.exists()
        assert len(result) == 1

    def test_second_call_reads_cache(self, cache_dir):
        """When cache exists, HF should NOT be called."""
        # Pre-create a cached file.
        parquet = cache_dir / "zomato_preprocessed.parquet"
        _dummy_raw_df().to_parquet(parquet, index=False)

        with patch("datasets.load_dataset") as mock_load:
            from src.data.loader import load_dataset_cached

            result = load_dataset_cached()

        mock_load.assert_not_called()
        assert len(result) == 1

    def test_force_reload_overwrites_cache(self, cache_dir):
        """force_reload=True should re-download even if cache exists."""
        parquet = cache_dir / "zomato_preprocessed.parquet"
        _dummy_raw_df().to_parquet(parquet, index=False)

        dummy = _dummy_raw_df()
        mock_ds = MagicMock()
        mock_ds.to_pandas.return_value = dummy

        with patch("datasets.load_dataset", return_value=mock_ds) as mock_load:
            from src.data.loader import load_dataset_cached

            _ = load_dataset_cached(force_reload=True)

        mock_load.assert_called_once()
