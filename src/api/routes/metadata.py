"""
Metadata routes for the frontend dropdowns.
"""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_repository
from src.api.schemas import CuisinesResponse, LocationsResponse, RestTypesResponse
from src.data.repository import RestaurantRepository

router = APIRouter(tags=["metadata"])


@router.get("/locations", response_model=LocationsResponse)
async def get_locations(repo: RestaurantRepository = Depends(get_repository)):
    """Get all unique locations from the dataset."""
    return LocationsResponse(locations=repo.unique_locations())


@router.get("/cuisines", response_model=CuisinesResponse)
async def get_cuisines(repo: RestaurantRepository = Depends(get_repository)):
    """Get all unique cuisines from the dataset."""
    return CuisinesResponse(cuisines=repo.unique_cuisines())


@router.get("/rest-types", response_model=RestTypesResponse)
async def get_rest_types(repo: RestaurantRepository = Depends(get_repository)):
    """Get all unique restaurant types from the dataset."""
    return RestTypesResponse(rest_types=repo.unique_rest_types())
