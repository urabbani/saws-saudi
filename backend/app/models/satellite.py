"""
SAWS Satellite Data Model

Satellite imagery and vegetation indices.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.field import Field


class SatelliteSource(str, Enum):
    """Satellite data sources."""

    MODIS = "modis"  # MOD13Q1 (250m, daily)
    LANDSAT = "landsat"  # Landsat 8-9 (30m, 16-day)
    SENTINEL1 = "sentinel1"  # SAR (5m, 6-day)
    SENTINEL2 = "sentinel2"  # MSI (10m, 5-day)
    PLANET = "planet"  # PlanetScope (3m, daily)


class SatelliteData(Base):
    """
    Satellite imagery and vegetation indices.

    Stores processed satellite data including:
    - NDVI (Normalized Difference Vegetation Index)
    - EVI (Enhanced Vegetation Index)
    - SAVI (Soil Adjusted Vegetation Index)
    - MSAVI (Modified Soil Adjusted Vegetation Index)
    - NDMI (Normalized Difference Moisture Index)
    - LST (Land Surface Temperature)
    """

    __tablename__ = "satellite_data"

    # Primary key
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: uuid4().hex,
    )

    # Foreign key
    field_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Source information
    source: Mapped[str] = mapped_column(
        Enum(SatelliteSource, name="satellite_source", create_constraint=True),
        nullable=False,
        index=True,
    )
    image_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    collection_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Acquisition time
    acquisition_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    # Date of the image (can differ from acquisition_date due to processing)
    image_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # Cloud coverage percentage (0-100)
    cloud_cover: Mapped[float] = mapped_column(Float, nullable=False)

    # Vegetation Indices
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 to 1
    evi: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 to 1
    savi: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 to 1
    msavi: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0 to 1
    ndmi: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1 to 1

    # Thermal
    lst: Mapped[float | None] = mapped_column(Float, nullable=True)  # Kelvin

    # Raw data URLs (Google Cloud Storage or similar)
    ndvi_tiff_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    true_color_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    false_color_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Additional metadata (JSON)
    # Stores processing parameters, quality flags, etc.
    metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Quality score (0-1, higher is better)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    field: Mapped["Field"] = relationship("Field", back_populates="satellite_data")

    def __repr__(self) -> str:
        return f"<SatelliteData(id={self.id}, source={self.source}, date={self.image_date})>"
