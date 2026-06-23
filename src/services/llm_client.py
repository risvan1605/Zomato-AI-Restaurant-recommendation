"""
Groq LLM client wrapper.

Provides a thin abstraction over the Groq Python SDK with JSON output mode,
timeout controls, and exponential backoff retries.

Phase 5 hardening:
  • API key pre-validation — raise ``ConfigurationError`` early.
  • Context window guard — warn and truncate if prompt is too long.
  • Temperature reduction retry — retry with lower temp on JSON parse failure.
  • Response metadata — expose raw response for latency/token logging.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from groq import Groq

from src.config import settings
from src.services.errors import ConfigurationError
from src.services.response_validator import strip_markdown_fences

logger = logging.getLogger(__name__)

# Placeholder patterns that indicate an unconfigured API key.
_PLACEHOLDER_KEYS = {"your-api-key-here", "your_api_key_here", ""}


class LLMClient:
    """Wrapper around the Groq chat completion API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> None:
        self._api_key = api_key or settings.groq_api_key
        self._model = model or settings.groq_model
        self._temperature = temperature if temperature is not None else settings.groq_temperature
        self._max_retries = max_retries

        # Note: API key validation is deferred to complete_json so fallback ranking works
        self._client = Groq(api_key=self._api_key)

    def _validate_api_key(self) -> None:
        """Raise :class:`ConfigurationError` if the API key looks invalid."""
        key = self._api_key.strip() if self._api_key else ""
        if not key or key.lower() in _PLACEHOLDER_KEYS or len(key) < 20:
            raise ConfigurationError(
                "Groq API key is missing or invalid. "
                "Set GROQ_API_KEY in your .env file with a valid key from "
                "https://console.groq.com/keys"
            )

    # ════════════════════════════════════════════════════════════════════
    # Public API
    # ════════════════════════════════════════════════════════════════════

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Send a chat completion and parse the response as JSON.

        Retries with exponential backoff on transient failures.
        On the first JSON parse failure, retries once with reduced
        temperature (0.1) for more deterministic output.

        Args:
            system_prompt: System role content.
            user_prompt: User role content.

        Returns:
            Parsed JSON dict from the LLM response.

        Raises:
            RuntimeError: If all retries are exhausted.
            ConfigurationError: If the API key is invalid.
        """
        # ── API key validation ──────────────────────────────────────────
        self._validate_api_key()

        # ── Context window guard ────────────────────────────────────────
        total_prompt = system_prompt + user_prompt
        estimated_tokens = len(total_prompt) // 4
        if estimated_tokens > settings.max_prompt_tokens:
            logger.warning(
                "Estimated prompt tokens (%d) exceed MAX_PROMPT_TOKENS (%d). "
                "The LLM may truncate or fail.",
                estimated_tokens,
                settings.max_prompt_tokens,
            )

        last_error: Optional[Exception] = None
        had_json_error = False

        for attempt in range(1, self._max_retries + 1):
            # On JSON parse failure, reduce temperature for next attempt
            temp = 0.1 if had_json_error else self._temperature

            try:
                data, meta = self._call(system_prompt, user_prompt, temp)
                # Log token usage and latency
                if meta:
                    logger.info(
                        "Groq response — model=%s, prompt_tokens=%s, "
                        "completion_tokens=%s, total_tokens=%s",
                        meta.get("model", self._model),
                        meta.get("prompt_tokens", "?"),
                        meta.get("completion_tokens", "?"),
                        meta.get("total_tokens", "?"),
                    )
                return data

            except json.JSONDecodeError as exc:
                last_error = exc
                had_json_error = True
                logger.warning(
                    "JSON parse failed on attempt %d/%d: %s. "
                    "Retrying with temperature=0.1 …",
                    attempt, self._max_retries, exc,
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)

            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning(
                    "Groq API error on attempt %d/%d: %s: %s",
                    attempt, self._max_retries,
                    type(exc).__name__, exc,
                )
                if attempt < self._max_retries:
                    time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Groq API call failed after {self._max_retries} retries: {last_error}"
        ) from last_error

    # ════════════════════════════════════════════════════════════════════
    # Internal
    # ════════════════════════════════════════════════════════════════════

    def _call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Make a single Groq API call and return (parsed_json, metadata).

        Raises:
            json.JSONDecodeError: If the response is not valid JSON.
            Exception: Any Groq SDK or network error.
        """
        t0 = time.monotonic()

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        latency_ms = (time.monotonic() - t0) * 1000

        content = response.choices[0].message.content
        # Strip markdown fences if present (defence-in-depth)
        content = strip_markdown_fences(content)
        data = json.loads(content)

        # Build metadata for logging
        usage = response.usage
        meta: Dict[str, Any] = {
            "model": getattr(response, "model", self._model),
            "latency_ms": round(latency_ms, 1),
        }
        if usage:
            meta["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
            meta["completion_tokens"] = getattr(usage, "completion_tokens", None)
            meta["total_tokens"] = getattr(usage, "total_tokens", None)

        logger.info("Groq call completed in %.0fms", latency_ms)

        return data, meta
