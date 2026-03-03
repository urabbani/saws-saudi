"""
SAWS Main Application

Saudi AgriDrought Warning System
FastAPI application entry point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
import structlog

from app.config import get_settings
from app.middleware import setup_middleware
from app.utils.logging import configure_logging

# Get settings
settings = get_settings()

# Configure logging
configure_logging(
    level=settings.log_level,
    format=settings.log_format,
    log_file=settings.log_file,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    logger.info(
        "starting_saws_api",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Startup
    try:
        logger.info("initializing_database")
        from app.db.base import init_db

        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.warning("database_initialization_failed", error=str(e))
        logger.info("api_running_without_database")

    # TODO: Initialize Redis connection
    # TODO: Initialize Celery workers
    # TODO: Initialize Google Earth Engine

    logger.info("startup_complete")

    yield

    # Shutdown
    logger.info("shutting_down")

    try:
        from app.db.base import close_db

        await close_db()
        logger.info("database_connections_closed")
    except Exception:
        pass

    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )

    # Setup middleware
    setup_middleware(app)

    # Include routers
    from app.api.v1 import fields, satellite, weather, alerts, analytics, districts, websocket

    api_v1_prefix = settings.api_v1_prefix

    app.include_router(fields.router, prefix=api_v1_prefix, tags=["Fields"])
    app.include_router(satellite.router, prefix=api_v1_prefix, tags=["Satellite"])
    app.include_router(weather.router, prefix=api_v1_prefix, tags=["Weather"])
    app.include_router(alerts.router, prefix=api_v1_prefix, tags=["Alerts"])
    app.include_router(analytics.router, prefix=api_v1_prefix, tags=["Analytics"])
    app.include_router(districts.router, prefix=api_v1_prefix, tags=["Districts"])
    app.include_router(websocket.router, prefix=api_v1_prefix, tags=["WebSocket"])

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """
        Health check endpoint.

        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        """
        Root endpoint.

        Returns:
            API information
        """
        return {
            "name": settings.app_name,
            "description": settings.app_description,
            "version": settings.app_version,
            "docs_url": "/docs" if settings.debug else None,
            "health_url": "/health",
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers if settings.environment == "production" else 1,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
