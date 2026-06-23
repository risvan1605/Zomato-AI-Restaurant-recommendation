"""
Recommendation endpoint.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_recommendation_service, get_repository
from src.api.schemas import RecommendRequest, RecommendResponse, RecommendationItem, FiltersMeta
from src.data.repository import RestaurantRepository
from src.services.errors import ConfigurationError, DatasetUnavailableError
from src.services.recommendation import RecommendationService
from src.services.validator import ValidationError, validate_preferences

logger = logging.getLogger(__name__)
router = APIRouter(tags=["recommendation"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    request: RecommendRequest,
    repo: RestaurantRepository = Depends(get_repository),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """
    Get AI-powered restaurant recommendations based on preferences.
    """
    try:
        # Validate and normalize preferences using domain logic
        prefs = validate_preferences(
            location=request.location,
            budget=request.budget,
            min_rating=request.min_rating,
            cuisine=request.cuisine,
            online_order=request.online_order,
            book_table=request.book_table,
            rest_type=request.rest_type,
            additional=request.additional,
            known_locations=repo.unique_locations(),
            known_cuisines=repo.unique_cuisines(),
        )
        
        # Get all restaurants and pass to orchestration service
        all_restaurants = repo.all_restaurants()
        domain_response = service.recommend(all_restaurants, prefs)
        
        # Map domain RecommendationResponse to API RecommendResponse
        api_recs = [
            RecommendationItem(
                rank=rec.rank,
                name=rec.name,
                cuisines=[c.strip() for c in rec.cuisine.split(",") if c.strip()],
                rating=rec.rating,
                votes=getattr(rec, "votes", 0), # Added safely in case votes isn't mapped
                cost_for_two=rec.estimated_cost,
                budget_tier=getattr(rec, "budget_tier", "Unknown"),
                rest_type=getattr(rec, "rest_type", None),
                online_order=getattr(rec, "online_order", False),
                book_table=getattr(rec, "book_table", False),
                explanation=rec.explanation,
            )
            for rec in domain_response.recommendations
        ]
        
        applied_labels = domain_response.metadata.get("filters_applied", [])
        applied_dict = {}
        if "location" in applied_labels:
            applied_dict["location"] = request.location
        if "budget" in applied_labels:
            applied_dict["budget"] = request.budget
        if "cuisine" in applied_labels and request.cuisine:
            applied_dict["cuisine"] = request.cuisine
        if "rating" in applied_labels:
            applied_dict["min_rating"] = request.min_rating
        if "online_order" in applied_labels and request.online_order is not None:
            applied_dict["online_order"] = request.online_order
        if "book_table" in applied_labels and request.book_table is not None:
            applied_dict["book_table"] = request.book_table
        if "rest_type" in applied_labels and request.rest_type:
            applied_dict["rest_type"] = request.rest_type

        return RecommendResponse(
            summary=domain_response.summary,
            recommendations=api_recs,
            metadata={
                "candidates_considered": domain_response.metadata.get("candidates_considered", 0),
                "total_after_location": domain_response.metadata.get("total_after_location", 0),
                "model": domain_response.metadata.get("model", "unknown"),
                "llm_latency_ms": domain_response.metadata.get("llm_latency_ms", 0),
                "fallback_reason": domain_response.metadata.get("fallback_reason"),
            },
            filters=FiltersMeta(
                applied=applied_dict,
                relaxed=domain_response.metadata.get("filters_relaxed", []),
            )
        )
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=503, detail="Service configuration error. AI features may be disabled.")
    except DatasetUnavailableError as e:
        logger.error(f"Dataset error: {e}")
        raise HTTPException(status_code=503, detail="Dataset is currently unavailable.")
    except Exception as e:
        logger.error(f"Unexpected error in recommendation pipeline: {e}")
        import traceback
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {e}\n{tb}")
