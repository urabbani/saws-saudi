"""
SAWS API v1 Routers

API v1 router initialization
"""

from fastapi import APIRouter

# Import routers
from app.api.v1 import fields, satellite, weather, alerts, analytics, districts

# Create main API v1 router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(fields.router, prefix="/fields", tags=["Fields"])
api_router.include_router(satellite.router, prefix="/satellite", tags=["Satellite"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(districts.router, prefix="/districts", tags=["Districts"])

__all__ = ["api_router", "fields", "satellite", "weather", "alerts", "analytics", "districts"]
