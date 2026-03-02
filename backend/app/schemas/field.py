"""
SAWS Field Schemas

Pydantic schemas for field API validation and serialization.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FieldGeometry(BaseModel):
    """Field geometry for API responses."""

    type: str = "Polygon"
    coordinates: list[list[list[float]]]  # GeoJSON polygon format


class FieldBase(BaseModel):
    """Base field schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    district_id: str = Field(..., min_length=1, max_length=100)
    geometry: FieldGeometry
    area_hectares: float = Field(..., gt=0)
    crop_type: str = Field(..., pattern="^(dates|wheat|tomatoes|alfalfa|sorghum|citrus|other)$")
    variety: str | None = Field(None, max_length=100)
    owner_name: str = Field(..., min_length=1, max_length=255)


class FieldCreate(FieldBase):
    """Schema for creating a new field."""

    owner_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, v: FieldGeometry) -> FieldGeometry:
        """Validate GeoJSON polygon."""
        if v.type != "Polygon":
            raise ValueError("Only Polygon geometry is supported")
        if not v.coordinates or len(v.coordinates) < 4:
            raise ValueError("Polygon must have at least 4 coordinates")
        # Check if polygon is closed
        if v.coordinates[0][0] != v.coordinates[-1][0]:
            raise ValueError("Polygon must be closed")
        return v


class FieldUpdate(BaseModel):
    """Schema for updating a field."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    crop_type: str | None = Field(None, pattern="^(dates|wheat|tomatoes|alfalfa|sorghum|citrus|other)$")
    variety: str | None = None
    status: str | None = Field(None, pattern="^(active|fallow|preparing|harvested)$")


class FieldDetail(BaseModel):
    """Detailed field information."""

    id: str
    name: str
    description: str | None
    district_id: str
    geometry: FieldGeometry
    centroid_latitude: float
    centroid_longitude: float
    area_hectares: float
    crop_type: str
    variety: str | None
    status: str
    owner_id: str
    owner_name: str
    created_at: datetime
    updated_at: datetime

    # Latest satellite data (if available)
    latest_ndvi: float | None = None
    latest_ndvi_date: datetime | None = None
    health_status: str | None = None  # excellent, good, moderate, poor

    class Config:
        from_attributes = True


class FieldSummary(BaseModel):
    """Brief field information for list views."""

    id: str
    name: str
    district_id: str
    crop_type: str
    area_hectares: float
    centroid_latitude: float
    centroid_longitude: float
    status: str
    latest_ndvi: float | None = None
    health_status: str | None = None


class FieldListResponse(BaseModel):
    """Paginated list of fields."""

    total: int
    skip: int
    limit: int
    items: list[FieldSummary]


class FieldDetailResponse(BaseModel):
    """Detailed field response."""

    data: FieldDetail
    included: dict[str, Any] | None = None  # Related data (alerts, satellite data, etc.)


# Field Statistics
class FieldStats(BaseModel):
    """Field statistics."""

    total_fields: int
    total_area_hectares: float
    fields_by_crop_type: dict[str, int]
    fields_by_status: dict[str, int]
    fields_by_district: dict[str, int]
    health_distribution: dict[str, int]  # excellent, good, moderate, poor
