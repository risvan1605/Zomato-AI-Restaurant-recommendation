"""
Centralized application configuration.

Reads settings from environment variables / .env file using pydantic-settings.
All tuneable parameters (dataset name, budget thresholds, Groq model, etc.)
are declared here so the rest of the codebase imports a single `settings`
object rather than scattering os.environ lookups.
"""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Typed, validated settings loaded from the environment / .env file."""

    # ── Hugging Face dataset ────────────────────────────────────────────
    hf_dataset_name: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        description="Hugging Face dataset identifier.",
    )
    data_cache_path: Path = Field(
        default=Path("cache"),
        description="Local directory for the cached parquet snapshot.",
    )

    # ── Budget tier thresholds (INR for two people) ─────────────────────
    budget_low_max: int = Field(
        default=500,
        description="Upper bound (inclusive) for the 'low' budget tier.",
    )
    budget_medium_max: int = Field(
        default=1500,
        description="Upper bound (inclusive) for the 'medium' budget tier.",
    )

    # ── Candidate / recommendation limits ───────────────────────────────
    max_candidates_for_llm: int = Field(
        default=20,
        description="Maximum restaurants sent to the LLM after filtering.",
    )
    top_k_recommendations: int = Field(
        default=5,
        description="Number of ranked recommendations the LLM should return.",
    )

    # ── Groq LLM configuration ─────────────────────────────────────────
    groq_api_key: str = Field(
        default="",
        description="Groq API key. Required for LLM calls; set in .env.",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Primary Groq model for ranking & explanations.",
    )
    groq_temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature. Kept low for consistent JSON output.",
    )
    groq_fallback_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Faster/cheaper fallback model for dev or retries.",
    )

    # ── Observability ───────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    max_prompt_tokens: int = Field(
        default=6000,
        description="Approximate token budget for LLM prompt; guard against context overflow.",
    )

    # ── CORS ────────────────────────────────────────────────────────────
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL for CORS allowlist.",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance – import this everywhere.
settings = Settings()
