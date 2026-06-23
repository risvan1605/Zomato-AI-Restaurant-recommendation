"""
FastAPI application factory and entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import RequestLoggingMiddleware
from src.api.routes import health, metadata, recommend
from src.config import settings
from src.data.loader import load_dataset_cached
from src.data.preprocessor import preprocess_dataframe
from src.data.repository import RestaurantRepository

# Set up logging early
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Loads and caches the dataset on startup, making it available to all requests.
    """
    logger.info("Starting up AI Restaurant Recommender API...")
    try:
        # Load dataset (downloads on first run, reads from parquet on subsequent)
        df = load_dataset_cached(force_reload=False)
        
        # Initialize repository
        repository = RestaurantRepository(df)
        
        # Pre-warm the cache for dropdowns and mapping
        repository.all_restaurants()
        
        # Make repository available to dependency injection
        app.state.repository = repository
        logger.info(f"Startup complete. Dataset loaded with {len(app.state.repository.all_restaurants())} restaurants.")
        
    except Exception as e:
        logger.error(f"Failed to load dataset during startup: {e}")
        # We don't crash the app here so the /health endpoint can report the degraded state
        app.state.repository = None

    yield

    # Shutdown logic (if any)
    logger.info("Shutting down API...")


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    
    app = FastAPI(
        title="AI Restaurant Recommender API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(metadata.router, prefix="/api/v1")
    app.include_router(recommend.router, prefix="/api/v1")

    return app

app = create_app()
