"""
SAWS Field Model

Agricultural field data with PostGIS geometry support.
"""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.satellite import SatelliteData


class CropType(str):
    """Saudi Eastern Province crop types."""

    DATES = "dates"
    WHEAT = "wheat"
    TOMATOES = "tomatoes"
    ALFALFA = "alfalfa"
    SORGHUM = "sorghum"
    CITRUS = "citrus"
    OTHER = "other"


class Field(Base):
    """
    Agricultural field representation.

    Represents a farm or agricultural plot in the Eastern Province
    with geometry for GIS mapping and crop information.
    """

    __tablename__ = "fields"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: uuid4().hex,
    )

    # Field information
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    district_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Geometry (PostGIS)
    # Stores field boundary as polygon with spatial index
    geometry: Mapped[bytes] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Center point for quick queries (stored for performance)
    centroid_latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    centroid_longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Area in hectares
    area_hectares: Mapped[float] = mapped_column(Float, nullable=False)

    # Crop information
    crop_type: Mapped[str] = mapped_column(
        Enum("dates", "wheat", "tomatoes", "alfalfa", "sorghum", "citrus", "other", name="crop_type"),
        nullable=False,
        index=True,
    )
    variety: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Current status
    status: Mapped[str] = mapped_column(
        Enum("active", "fallow", "preparing", "harvested", name="field_status"),
        nullable=False,
        default="active",
        index=True,
    )

    # Owner information
    owner_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="field",
        cascade="all, delete-orphan",
    )
    satellite_data: Mapped[list["SatelliteData"]] = relationship(
        "SatelliteData",
        back_populates="field",
        cascade="all, delete-orphan",
    )

    @property
    def geometry_geojson(self) -> dict[str, Any]:
        """
        Convert PostGIS geometry to GeoJSON for API responses.

        Returns:
            GeoJSON Polygon representation
        """
        try:
            shapely_geom = to_shape(self.geometry)
            return shapely_geom.__geo_interface__
        except Exception:
            # Return empty polygon if conversion fails
            return {
                "type": "Polygon",
                "coordinates": [[]],
            }

    @property
    def geometry_wkt(self) -> str:
        """
        Get geometry as Well-Known Text.

        Returns:
            WKT representation of geometry
        """
        try:
            shapely_geom = to_shape(self.geometry)
            return shapely_geom.wkt
        except Exception:
            return "POLYGON EMPTY"

    def get_bounds(self) -> tuple[float, float, float, float]:
        """
        Get bounding box of the field.

        Returns:
            (min_lon, min_lat, max_lon, max_lat)
        """
        try:
            shapely_geom = to_shape(self.geometry)
            bounds = shapely_geom.bounds  # (minx, miny, maxx, maxy)
            return (bounds[0], bounds[1], bounds[2], bounds[3])
        except Exception:
            return (
                self.centroid_longitude - 0.01,
                self.centroid_latitude - 0.01,
                self.centroid_longitude + 0.01,
                self.centroid_latitude + 0.01,
            )

    def to_dict(self, include_geometry: bool = True) -> dict[str, Any]:
        """
        Convert field to dictionary for API responses.

        Args:
            include_geometry: Whether to include full geometry

        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "district_id": self.district_id,
            "centroid": {
                "latitude": self.centroid_latitude,
                "longitude": self.centroid_longitude,
            },
            "area_hectares": self.area_hectares,
            "crop_type": self.crop_type,
            "variety": self.variety,
            "status": self.status,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_geometry:
            data["geometry"] = self.geometry_geojson

        return data

    def __repr__(self) -> str:
        return f"<Field(id={self.id}, name={self.name}, crop_type={self.crop_type})>"
