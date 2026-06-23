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
    
    return HealthResponse(
        status=status,
        dataset_loaded=dataset_loaded,
        restaurant_count=restaurant_count,
        groq_api_configured=groq_api_configured,
    )
