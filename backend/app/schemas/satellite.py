"""
SAWS Satellite Schemas

Pydantic schemas for satellite data API validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SatelliteSource(str, Enum):
    """Satellite data sources."""

    MODIS = "modis"
    LANDSAT = "landsat"
    SENTINEL1 = "sentinel1"
    SENTINEL2 = "sentinel2"
    PLANET = "planet"


class VegetationIndexType(str, Enum):
    """Types of vegetation indices."""

    NDVI = "ndvi"
    EVI = "evi"
    SAVI = "savi"
    MSAVI = "msavi"
    NDMI = "ndmi"
    LST = "lst"


class SatelliteSourceInfo(BaseModel):
    """Information about a satellite source."""

    source: SatelliteSource
    name: str
    description: str
    resolution: str  # e.g., "250m", "10m"
    revisit_time: str  # e.g., "Daily", "5-day"
    coverage: str  # e.g., "Global"
    cost: str  # e.g., "Free", "Commercial"
    available: bool = True


class SatelliteSourceListResponse(BaseModel):
    """List of satellite sources."""

    items: list[SatelliteSourceInfo]


class SatelliteImage(BaseModel):
    """Satellite image metadata."""

    id: str
    field_id: str
    source: SatelliteSource
    image_id: str
    collection_id: str
    acquisition_date: datetime
    image_date: datetime
    cloud_cover: float
    ndvi: float | None = None
    evi: float | None = None
    lst: float | None = None
    quality_score: float

    class Config:
        from_attributes = True


class SatelliteImageListResponse(BaseModel):
    """Paginated list of satellite images."""

    total: int
    skip: int
    limit: int
    items: list[SatelliteImage]


class NDVIPoint(BaseModel):
    """NDVI value at a point in time."""

    date: datetime
    value: float
    source: SatelliteSource | None = None
    cloud_cover: float | None = None


class VegetationIndexResponse(BaseModel):
    """Vegetation index time series response."""

    field_id: str
    index_type: VegetationIndexType
    start_date: datetime | None = None
    end_date: datetime | None = None
    data: list[NDVIPoint]
    statistics: dict[str, float] | None = None  # min, max, mean, std
