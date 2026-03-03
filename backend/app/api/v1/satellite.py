"""
SAWS Satellite Data API Endpoints

Satellite imagery and vegetation index endpoints.
"""

from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, UserId
from app.models.field import Field
from app.models.satellite import SatelliteData, SatelliteSource
from app.schemas.satellite import (
    NDVIPoint,
    SatelliteImage,
    SatelliteImageListResponse,
    SatelliteSourceInfo,
    SatelliteSourceListResponse,
    VegetationIndexResponse,
    VegetationIndexType,
)

router = APIRouter()


# Predefined satellite source information
SATELLITE_SOURCES = [
    SatelliteSourceInfo(
        source=SatelliteSource.MODIS,
        name="MODIS",
        description="Moderate Resolution Imaging Spectroradiometer",
        resolution="250m",
        revisit_time="Daily",
        coverage="Global",
        cost="Free",
        available=True,
    ),
    SatelliteSourceInfo(
        source=SatelliteSource.LANDSAT,
        name="Landsat 8-9",
        description="NASA/USGS Landsat program",
        resolution="30m",
        revisit_time="16-day",
        coverage="Global",
        cost="Free",
        available=True,
    ),
    SatelliteSourceInfo(
        source=SatelliteSource.SENTINEL1,
        name="Sentinel-1",
        description="ESA SAR imaging",
        resolution="10m",
        revisit_time="6-day",
        coverage="Global",
        cost="Free",
        available=True,
    ),
    SatelliteSourceInfo(
        source=SatelliteSource.SENTINEL2,
        name="Sentinel-2",
        description="ESA optical and multispectral",
        resolution="10m",
        revisit_time="5-day",
        coverage="Global",
        cost="Free",
        available=True,
    ),
    SatelliteSourceInfo(
        source=SatelliteSource.PLANET,
        name="Planet Scope",
        description="Planet Labs satellite constellation",
        resolution="3-5m",
        revisit_time="Daily",
        coverage="Global",
        cost="Commercial",
        available=False,
    ),
]


@router.get("/sources", response_model=SatelliteSourceListResponse)
async def list_satellite_sources(
    db: DBSession,
    user_id: UserId,
) -> SatelliteSourceListResponse:
    """
    List available satellite data sources.

    Returns information about MODIS, Sentinel-1/2, Landsat, etc.

    Args:
        db: Database session
        user_id: Authenticated user ID

    Returns:
        List of available satellite sources
    """
    return SatelliteSourceListResponse(items=SATELLITE_SOURCES)


@router.get("/images", response_model=SatelliteImageListResponse)
async def list_satellite_images(
    db: DBSession,
    user_id: UserId,
    source: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> SatelliteImageListResponse:
    """
    List available satellite imagery for user fields.

    Args:
        db: Database session
        user_id: Authenticated user ID
        source: Filter by satellite source (MODIS, Sentinel, Landsat)
        start_date: Start date filter
        end_date: End date filter
        skip: Number of records to skip
        limit: Maximum records to return

    Returns:
        List of satellite images
    """
    # Build base query
    query = select(SatelliteData)

    # Apply source filter
    if source:
        query = query.where(SatelliteData.source == source)

    # Apply date filters
    if start_date:
        query = query.where(SatelliteData.image_date >= start_date)
    if end_date:
        query = query.where(SatelliteData.image_date <= end_date)

    # Default to last 90 days if no dates specified
    if not start_date:
        default_start = datetime.now() - timedelta(days=90)
        query = query.where(SatelliteData.image_date >= default_start)

    # Order by date descending
    query = query.order_by(SatelliteData.image_date.desc())

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    satellite_images = result.scalars().all()

    # Convert to response model
    items = [
        SatelliteImage(
            id=str(sat_data.id),
            field_id=str(sat_data.field_id),
            source=SatelliteSource(sat_data.source),
            image_id=sat_data.image_id or f"IMG_{sat_data.source}_{sat_data.image_date:%Y%m%d}",
            collection_id=sat_data.collection_id or "S2MSI2A",
            acquisition_date=sat_data.created_at,
            image_date=sat_data.image_date,
            cloud_cover=sat_data.cloud_cover or 0.0,
            ndvi=sat_data.ndvi,
            evi=sat_data.evi,
            lst=sat_data.lst,
            quality_score=1.0 - (sat_data.cloud_cover or 0.0),
        )
        for sat_data in satellite_images
    ]

    return SatelliteImageListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get("/indices/{field_id}", response_model=VegetationIndexResponse)
async def get_vegetation_indices(
    field_id: str,
    db: DBSession,
    user_id: UserId,
    index_type: Annotated[VegetationIndexType, Query()] = VegetationIndexType.NDVI,
    start_date: date | None = None,
    end_date: date | None = None,
) -> VegetationIndexResponse:
    """
    Get vegetation index time series for a field.

    Supports NDVI, EVI, SAVI, MSAVI, NDMI, and LST.

    Args:
        field_id: Field ID
        db: Database session
        user_id: Authenticated user ID
        index_type: Type of vegetation index
        start_date: Start date for time series
        end_date: End date for time series

    Returns:
        Vegetation index time series data
    """
    # Verify field exists
    field_result = await db.execute(select(Field).where(Field.id == field_id))
    field = field_result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Default date range - last 180 days
    if not start_date:
        start_date = datetime.now().date() - timedelta(days=180)
    if not end_date:
        end_date = datetime.now().date()

    # Build query for satellite data
    query = (
        select(SatelliteData)
        .where(SatelliteData.field_id == field_id)
        .where(SatelliteData.image_date >= start_date)
        .where(SatelliteData.image_date <= end_date)
        .order_by(SatelliteData.image_date.desc())
    )

    result = await db.execute(query)
    satellite_data = result.scalars().all()

    if not satellite_data:
        # Return empty time series if no data found
        return VegetationIndexResponse(
            field_id=field_id,
            index_type=index_type,
            start_date=start_date,
            end_date=end_date,
            data=[],
            statistics=None,
        )

    # Map index type to model field
    index_fields = {
        VegetationIndexType.NDVI: "ndvi",
        VegetationIndexType.EVI: "evi",
        VegetationIndexType.SAVI: "savi",
        VegetationIndexType.MSAVI: "msavi",
        VegetationIndexType.NDMI: "ndmi",
        VegetationIndexType.LST: "lst",
    }
    field_name = index_fields.get(index_type, "ndvi")

    # Convert to time series data
    data_points = []
    values = []

    for sat_data in satellite_data:
        value = getattr(sat_data, field_name, None)
        if value is not None:
            data_points.append(
                NDVIPoint(
                    date=sat_data.image_date,
                    value=value,
                    source=SatelliteSource(sat_data.source) if sat_data.source else None,
                    cloud_cover=sat_data.cloud_cover,
                )
            )
            values.append(value)

    # Sort by date ascending for charts
    data_points.sort(key=lambda x: x.date)

    # Calculate statistics
    statistics = None
    if values:
        statistics = {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "std": (sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)) ** 0.5,
        }

    return VegetationIndexResponse(
        field_id=field_id,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date,
        data=data_points,
        statistics=statistics,
    )


@router.get("/ndvi/{field_id}", response_model=VegetationIndexResponse)
async def get_ndvi_timeseries(
    field_id: str,
    db: DBSession,
    user_id: UserId,
    start_date: date | None = None,
    end_date: date | None = None,
) -> VegetationIndexResponse:
    """
    Get NDVI time series for a field.

    Args:
        field_id: Field ID
        db: Database session
        user_id: Authenticated user ID
        start_date: Start date for time series
        end_date: End date for time series

    Returns:
        NDVI time series data
    """
    # Delegate to get_vegetation_indices with NDVI index type
    return await get_vegetation_indices(
        field_id=field_id,
        db=db,
        user_id=user_id,
        index_type=VegetationIndexType.NDVI,
        start_date=start_date,
        end_date=end_date,
    )
