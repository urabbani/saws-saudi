"""
SAWS Analytics Schemas

Pydantic schemas for analytics API validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DroughtStatus(str, Enum):
    """Drought classification following WMO standards."""

    EXTREME = "extreme"  # SPEI <= -2.5
    SEVERE = "severe"  # -2.5 < SPEI <= -2.0
    MODERATE = "moderate"  # -2.0 < SPEI <= -1.5
    ABNORMALLY_DRY = "abnormally_dry"  # -1.5 < SPEI <= -1.0
    NORMAL = "normal"  # -1.0 < SPEI <= 1.0
    WET = "wet"  # SPEI > 1.0


class NDVIPoint(BaseModel):
    """NDVI value at a point in time."""

    date: datetime
    value: float


class CropTrendsResponse(BaseModel):
    """Crop health trends over time."""

    field_id: str | None = None
    crop_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    ndvi_trend: list[NDVIPoint]
    evi_trend: list[NDVIPoint] | None = None
    statistics: dict[str, float] | None = None  # min, max, mean, trend slope
    health_status: DroughtStatus | None = None


class YieldPrediction(BaseModel):
    """Yield prediction for a field."""

    predicted_yield: float  # tons per hectare
    confidence_interval: tuple[float, float]  # (lower, upper)
    confidence_level: float  # e.g., 0.95
    prediction_date: datetime
    expected_harvest_date: datetime | None = None
    model_version: str
    factors: dict[str, Any] | None = None  # Contributing factors


class YieldPredictionResponse(BaseModel):
    """Yield prediction response."""

    field_id: str
    prediction: YieldPrediction


class DroughtStatusResponse(BaseModel):
    """Current drought status for a location."""

    latitude: float
    longitude: float
    spei_value: float
    spei_scale: int  # Time scale in months
    status: DroughtStatus
    status_changed_at: datetime | None = None
    trend: str | None = None  # "improving", "worsening", "stable"
    contributing_factors: dict[str, Any] | None = None


class DroughtForecastPoint(BaseModel):
    """Drought forecast at a point in time."""

    date: datetime
    spei_predicted: float
    spei_lower_bound: float | None = None
    spei_upper_bound: float | None = None
    status: DroughtStatus


class DroughtForecastResponse(BaseModel):
    """Drought forecast for a location."""

    latitude: float
    longitude: float
    forecast_days: int
    generated_at: datetime
    model_version: str
    forecast: list[DroughtForecastPoint]


class CropHealthDistribution(BaseModel):
    """Crop health distribution across fields."""

    excellent: int  # NDVI > 0.6
    good: int  # 0.4 < NDVI <= 0.6
    moderate: int  # 0.2 < NDVI <= 0.4
    poor: int  # NDVI <= 0.2
    total: int
