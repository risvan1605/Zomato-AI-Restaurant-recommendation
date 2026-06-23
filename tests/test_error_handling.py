"""
Integration tests for Phase 5 error-handling hardening.

Covers:
  • Corrupted Parquet cache triggers re-download.
  • Missing / placeholder API key raises ``ConfigurationError``.
  • Context window guard logs a warning for oversized prompts.
  • Temperature reduction retry on malformed JSON.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.errors import ConfigurationError, DatasetUnavailableError, SchemaError


# ════════════════════════════════════════════════════════════════════════
# 1. Corrupted Parquet cache recovery
# ════════════════════════════════════════════════════════════════════════


class TestCorruptedCacheRecovery:
    """Verify that a corrupted cache file is deleted and re-downloaded."""

    def test_corrupted_cache_triggers_redownload(self, tmp_path):
        """Write garbage to the cache file and verify loader recovers."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        parquet_path = cache_dir / "zomato_preprocessed.parquet"
        parquet_path.write_bytes(b"THIS IS NOT VALID PARQUET DATA")

        # Patch settings to use our tmp cache dir
        with patch("src.data.loader.settings") as mock_settings:
            mock_settings.data_cache_path = cache_dir
            mock_settings.hf_dataset_name = "test/dataset"

            # Mock the HF download to return a minimal DataFrame
            import pandas as pd

            mock_df = pd.DataFrame({
                "name": ["Test Restaurant"],
                "location": ["Test City"],
                "rate": ["4.0/5"],
                "cuisines": ["Italian"],
            })

            # load_dataset is imported inside the function, so patch at source
            with patch("datasets.load_dataset") as mock_load:
                mock_ds = MagicMock()
                mock_ds.to_pandas.return_value = mock_df
                mock_load.return_value = mock_ds

                with patch("src.data.preprocessor.preprocess_dataframe", return_value=mock_df):
                    from src.data.loader import load_dataset_cached
                    result = load_dataset_cached(force_reload=False)

                    assert len(result) == 1
                    # The corrupted file should have been removed and re-created
                    assert parquet_path.exists()

    def test_missing_cache_and_offline_raises(self, tmp_path):
        """No cache + HF unreachable → DatasetUnavailableError."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        with patch("src.data.loader.settings") as mock_settings:
            mock_settings.data_cache_path = cache_dir
            mock_settings.hf_dataset_name = "test/dataset"

            # load_dataset is imported inside the function, so patch at source
            with patch(
                "datasets.load_dataset",
                side_effect=ConnectionError("No internet"),
            ):
                from src.data.loader import load_dataset_cached

                with pytest.raises(DatasetUnavailableError, match="Cannot reach"):
                    load_dataset_cached(force_reload=False)


# ════════════════════════════════════════════════════════════════════════
# 2. Schema validation
# ════════════════════════════════════════════════════════════════════════


class TestSchemaValidation:
    def test_missing_name_column_raises(self):
        import pandas as pd
        from src.data.loader import _validate_schema

        df = pd.DataFrame({"location": ["A"], "rate": [4.0], "cuisines": ["X"]})
        with pytest.raises(SchemaError, match="name"):
            _validate_schema(df, source="test")

    def test_missing_rating_columns_raises(self):
        import pandas as pd
        from src.data.loader import _validate_schema

        df = pd.DataFrame({"name": ["A"], "location": ["B"], "cuisines": ["X"]})
        with pytest.raises(SchemaError, match="rating"):
            _validate_schema(df, source="test")

    def test_missing_cuisine_columns_raises(self):
        import pandas as pd
        from src.data.loader import _validate_schema

        df = pd.DataFrame({"name": ["A"], "location": ["B"], "rate": [4.0]})
        with pytest.raises(SchemaError, match="cuisines"):
            _validate_schema(df, source="test")

    def test_valid_schema_passes(self):
        import pandas as pd
        from src.data.loader import _validate_schema

        df = pd.DataFrame({
            "name": ["A"],
            "location": ["B"],
            "rating": [4.0],
            "cuisines_list": [["Italian"]],
        })
        # Should not raise
        _validate_schema(df, source="test")


# ════════════════════════════════════════════════════════════════════════
# 3. API key validation
# ════════════════════════════════════════════════════════════════════════


class TestAPIKeyValidation:
    def test_empty_key_raises(self):
        with patch("src.services.llm_client.settings") as mock_settings:
            mock_settings.groq_api_key = ""
            mock_settings.groq_model = "test-model"
            mock_settings.groq_temperature = 0.3

            from src.services.llm_client import LLMClient

            with pytest.raises(ConfigurationError, match="missing or invalid"):
                LLMClient(api_key="")

    def test_placeholder_key_raises(self):
        from src.services.llm_client import LLMClient

        with pytest.raises(ConfigurationError, match="missing or invalid"):
            LLMClient(api_key="your-api-key-here")

    def test_short_key_raises(self):
        from src.services.llm_client import LLMClient

        with pytest.raises(ConfigurationError, match="missing or invalid"):
            LLMClient(api_key="sk-short")


# ════════════════════════════════════════════════════════════════════════
# 4. Context window guard
# ════════════════════════════════════════════════════════════════════════


class TestContextWindowGuard:
    def test_oversized_prompt_logs_warning(self, caplog):
        """Verify that an oversized prompt produces a warning log."""
        # Create a client with a valid-looking key
        with patch("src.services.llm_client.Groq"):
            with patch("src.services.llm_client.settings") as mock_settings:
                mock_settings.groq_api_key = "gsk_test_key_1234567890abcdef"
                mock_settings.groq_model = "test-model"
                mock_settings.groq_temperature = 0.3
                mock_settings.max_prompt_tokens = 100  # Very low threshold

                from src.services.llm_client import LLMClient

                client = LLMClient(api_key="gsk_test_key_1234567890abcdef")

                # Mock the _call method to avoid actual API calls
                mock_response = {"recommendations": []}
                client._call = MagicMock(return_value=(mock_response, {}))

                with caplog.at_level(logging.WARNING, logger="src.services.llm_client"):
                    # Prompt with ~1000 chars → ~250 tokens, exceeding 100
                    big_prompt = "x" * 1000
                    client.complete_json("system", big_prompt)

                assert any("exceed MAX_PROMPT_TOKENS" in r.message for r in caplog.records)


# ════════════════════════════════════════════════════════════════════════
# 5. Temperature reduction retry
# ════════════════════════════════════════════════════════════════════════


class TestTemperatureRetry:
    def test_json_error_retries_with_lower_temp(self):
        """On JSON parse failure, verify retry uses temperature=0.1."""
        with patch("src.services.llm_client.Groq"):
            with patch("src.services.llm_client.settings") as mock_settings:
                mock_settings.groq_api_key = "gsk_test_key_1234567890abcdef"
                mock_settings.groq_model = "test-model"
                mock_settings.groq_temperature = 0.3
                mock_settings.max_prompt_tokens = 99999

                from src.services.llm_client import LLMClient

                client = LLMClient(
                    api_key="gsk_test_key_1234567890abcdef",
                    max_retries=2,
                )

                call_temps = []
                call_count = 0

                def mock_call(system, user, temperature):
                    nonlocal call_count
                    call_temps.append(temperature)
                    call_count += 1
                    if call_count == 1:
                        raise json.JSONDecodeError("bad", "", 0)
                    return {"recommendations": []}, {}

                client._call = mock_call

                with patch("src.services.llm_client.time"):
                    result = client.complete_json("system", "user")

                assert call_temps[0] == 0.3   # First attempt: normal temp
                assert call_temps[1] == 0.1   # Second attempt: reduced temp
                assert result == {"recommendations": []}
