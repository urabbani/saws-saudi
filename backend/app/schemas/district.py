"""
SAWS District Schemas

Pydantic schemas for district API validation and serialization.
"""

from typing import Any

from pydantic import BaseModel, Field


class District(BaseModel):
    """Administrative district information."""

    id: str
    name: str = Field(..., min_length=1, max_length=255)
    name_ar: str | None = Field(None, max_length=255)  # Arabic name
    region: str = Field(default="Eastern Province")
    area_hectares: float | None = None
    centroid_latitude: float | None = None
    centroid_longitude: float | None = None

    class Config:
        from_attributes = True


class DistrictSummary(BaseModel):
    """Brief district information."""

    id: str
    name: str
    name_ar: str | None
    total_fields: int = 0
    total_area_hectares: float = 0.0
    average_ndvi: float | None = None
    health_status: str | None = None  # Based on average NDVI


class DistrictResponse(BaseModel):
    """District detail response."""

    data: DistrictSummary
    fields: list[Any] | None = None  # List of field summaries


class DistrictListResponse(BaseModel):
    """List of all districts."""

    items: list[DistrictSummary]
