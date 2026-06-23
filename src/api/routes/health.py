"""
Health check route.
"""

from fastapi import APIRouter, Request

from src.api.schemas import HealthResponse
from src.config import settings
from src.data.repository import RestaurantRepository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request):
    """
    Health check endpoint returning system status and configuration info.
    """
    repo: RestaurantRepository | None = getattr(request.app.state, "repository", None)
    
    dataset_loaded = repo is not None
    restaurant_count = len(repo.all_restaurants()) if repo else 0
    groq_api_configured = bool(settings.groq_api_key and not settings.groq_api_key.startswith("gsk_your_"))
    
    status = "healthy" if dataset_loaded else "degraded"
    
    state_keys = list(request.app.state._state.keys()) if hasattr(request.app.state, '_state') else []
    
    return HealthResponse(
        status=status,
        dataset_loaded=dataset_loaded,
        restaurant_count=restaurant_count,
        groq_api_configured=groq_api_configured,
        error=f"Keys in app.state: {state_keys} | startup_error: {getattr(request.app.state, 'startup_error', 'MISSING')} | repo_type: {type(repo).__name__ if repo else 'None'}"
    )
