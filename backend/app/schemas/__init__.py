"""
SAWS Schemas

All Pydantic schemas for API validation and serialization.
"""

from app.schemas.alert import (
    Alert,
    AlertCreate,
    AlertListResponse,
    AlertSeverity,
    AlertStats,
    AlertSummary,
    AlertType,
    AlertUpdate,
)
from app.schemas.analytics import (
    CropHealthDistribution,
    CropTrendsResponse,
    DroughtForecastPoint,
    DroughtForecastResponse,
    DroughtStatus,
    DroughtStatusResponse,
    NDVIPoint,
    YieldPrediction,
    YieldPredictionResponse,
)
from app.schemas.district import District, DistrictListResponse, DistrictResponse, DistrictSummary
from app.schemas.field import (
    FieldCreate,
    FieldDetail,
    FieldDetailResponse,
    FieldGeometry,
    FieldListResponse,
    FieldStats,
    FieldSummary,
    FieldUpdate,
)
from app.schemas.satellite import (
    NDVIPoint as SatelliteNDVIPoint,
    SatelliteImage,
    SatelliteImageListResponse,
    SatelliteSource,
    SatelliteSourceInfo,
    SatelliteSourceListResponse,
    VegetationIndexResponse,
    VegetationIndexType,
)
from app.schemas.weather import (
    CurrentWeather,
    CurrentWeatherResponse,
    DailyForecast,
    ForecastResponse,
    HistoricalWeatherData,
    HistoricalWeatherResponse,
    HourlyForecast,
)

__all__ = [
    # Field
    "FieldCreate",
    "FieldUpdate",
    "FieldDetail",
    "FieldSummary",
    "FieldListResponse",
    "FieldDetailResponse",
    "FieldStats",
    "FieldGeometry",
    # Alert
    "Alert",
    "AlertCreate",
    "AlertUpdate",
    "AlertListResponse",
    "AlertSummary",
    "AlertStats",
    "AlertSeverity",
    "AlertType",
    # Satellite
    "SatelliteSource",
    "SatelliteSourceInfo",
    "SatelliteSourceListResponse",
    "SatelliteImage",
    "SatelliteImageListResponse",
    "VegetationIndexResponse",
    "VegetationIndexType",
    "SatelliteNDVIPoint",
    # Weather
    "CurrentWeather",
    "CurrentWeatherResponse",
    "DailyForecast",
    "ForecastResponse",
    "HistoricalWeatherData",
    "HistoricalWeatherResponse",
    "HourlyForecast",
    # Analytics
    "CropTrendsResponse",
    "YieldPrediction",
    "YieldPredictionResponse",
    "DroughtStatus",
    "DroughtStatusResponse",
    "DroughtForecastResponse",
    "DroughtForecastPoint",
    "CropHealthDistribution",
    "NDVIPoint",
    # District
    "District",
    "DistrictSummary",
    "DistrictResponse",
    "DistrictListResponse",
]
