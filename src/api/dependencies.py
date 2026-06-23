"""
FastAPI dependency injection.
"""

from fastapi import Request

from src.config import Settings, settings
from src.data.repository import RestaurantRepository
from src.services.recommendation import RecommendationService


def get_settings() -> Settings:
    """Return the application settings."""
    return settings


def get_repository(request: Request) -> RestaurantRepository:
    """
    Get the loaded RestaurantRepository from the application state.
    This ensures we use the singleton repository initialized at startup.
    """
    repo = getattr(request.app.state, "repository", None)
    if not repo:
        raise RuntimeError("RestaurantRepository not initialized in app state.")
    return repo


def get_recommendation_service() -> RecommendationService:
    """
    Get the RecommendationService.
    Can be expanded to inject custom LLM clients if needed.
    """
    return RecommendationService()
