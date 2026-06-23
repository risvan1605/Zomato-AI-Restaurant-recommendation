"""
Pydantic V2 schemas for API requests and responses.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """Payload for requesting restaurant recommendations."""
    location: str = Field(..., description="Required city or locality name")
    budget: Literal["low", "medium", "high"] = Field(..., description="Budget tier")
    cuisine: Optional[str] = Field(None, description="Optional single primary cuisine")
    min_rating: float = Field(3.5, ge=0.0, le=5.0, description="Minimum acceptable rating")
    rest_type: Optional[str] = Field(None, description="Optional restaurant type filter")
    online_order: Optional[bool] = Field(None, description="Filter for online ordering")
    book_table: Optional[bool] = Field(None, description="Filter for table booking")
    additional: Optional[str] = Field(None, description="Free-text preferences for LLM")


class RecommendationItem(BaseModel):
    """A single ranked restaurant recommendation."""
    rank: int
    name: str
    cuisines: List[str]
    rating: Optional[float]
    votes: int
    cost_for_two: Optional[int]
    budget_tier: Optional[str]
    rest_type: Optional[str]
    online_order: bool
    book_table: bool
    explanation: str


class FiltersMeta(BaseModel):
    """Metadata about applied and relaxed filters."""
    applied: Dict[str, Any]
    relaxed: List[str]


class RecommendResponse(BaseModel):
    """Full response for a recommendation request."""
    summary: Optional[str] = None
    recommendations: List[RecommendationItem]
    metadata: Dict[str, Any]
    filters: FiltersMeta


class LocationsResponse(BaseModel):
    locations: List[str]


class CuisinesResponse(BaseModel):
    cuisines: List[str]


class RestTypesResponse(BaseModel):
    rest_types: List[str]


class HealthResponse(BaseModel):
    status: str
    dataset_loaded: bool
    restaurant_count: int
    groq_api_configured: bool
    error: Optional[str] = None
