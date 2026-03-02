"""
SAWS Fields API Endpoints

Field CRUD operations for agricultural fields in the Eastern Province.
"""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import DBSession, UserId
from app.models.field import Field
from app.models.satellite import SatelliteData
from app.schemas.field import (
    FieldCreate,
    FieldDetail,
    FieldDetailResponse,
    FieldListResponse,
    FieldSummary,
    FieldUpdate,
)

router = APIRouter()


@router.get("", response_model=FieldListResponse)
async def list_fields(
    db: DBSession,
    user_id: UserId,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    district: str | None = None,
    crop_type: str | None = None,
) -> FieldListResponse:
    """
    List all agricultural fields with pagination and filtering.
    """
    # Build base query
    query = select(Field).where(Field.status == "active")

    # Apply filters
    if district:
        query = query.where(Field.district_id == district)
    if crop_type:
        query = query.where(Field.crop_type == crop_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Field.name).offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    fields = result.scalars().all()

    # Convert to response format
    items = []
    for field in fields:
        # Get latest NDVI from satellite data
        sat_query = (
            select(SatelliteData.ndvi, SatelliteData.image_date)
            .where(SatelliteData.field_id == field.id)
            .where(SatelliteData.ndvi.isnot(None))
            .order_by(SatelliteData.image_date.desc())
            .limit(1)
        )
        sat_result = await db.execute(sat_query)
        latest_sat = sat_result.first()

        # Determine health status
        latest_ndvi = latest_sat[0] if latest_sat else None
        health_status = _calculate_health_status(latest_ndvi, field.crop_type)

        items.append(FieldSummary(
            id=field.id,
            name=field.name,
            district_id=field.district_id,
            crop_type=field.crop_type,
            area_hectares=field.area_hectares,
            centroid_latitude=field.centroid_latitude,
            centroid_longitude=field.centroid_longitude,
            status=field.status,
            latest_ndvi=latest_ndvi,
            health_status=health_status,
        ))

    return FieldListResponse(total=total, skip=skip, limit=limit, items=items)


@router.get("/stats")
async def get_field_stats(db: DBSession) -> dict:
    """
    Get field statistics for the dashboard.
    """
    # Total fields and area
    total_result = await db.execute(
        select(
            func.count(Field.id).label("total_fields"),
            func.sum(Field.area_hectares).label("total_area"),
        ).where(Field.status == "active")
    )
    total_data = total_result.one()

    # Fields by crop type
    crop_result = await db.execute(
        select(Field.crop_type, func.count(Field.id))
        .where(Field.status == "active")
        .group_by(Field.crop_type)
    )
    by_crop = {row[0]: row[1] for row in crop_result.all()}

    # Fields by status
    status_result = await db.execute(
        select(Field.status, func.count(Field.id))
        .group_by(Field.status)
    )
    by_status = {row[0]: row[1] for row in status_result.all()}

    # Health distribution
    health_dist = {"excellent": 0, "good": 0, "moderate": 0, "poor": 0}

    all_fields = await db.execute(select(Field).where(Field.status == "active"))
    for field in all_fields.scalars():
        # Get latest NDVI
        sat_result = await db.execute(
            select(SatelliteData.ndvi)
            .where(SatelliteData.field_id == field.id)
            .where(SatelliteData.ndvi.isnot(None))
            .order_by(SatelliteData.image_date.desc())
            .limit(1)
        )
        latest_ndvi = sat_result.scalar()
        status = _calculate_health_status(latest_ndvi, field.crop_type)
        health_dist[status] = health_dist.get(status, 0) + 1

    return {
        "total_fields": total_data.total_fields or 0,
        "total_area_hectares": float(total_data.total_area or 0),
        "fields_by_crop_type": by_crop,
        "fields_by_status": by_status,
        "health_distribution": health_dist,
    }


@router.get("/{field_id}", response_model=FieldDetailResponse)
async def get_field(
    field_id: str,
    db: DBSession,
    user_id: UserId,
) -> FieldDetailResponse:
    """Get field details by ID."""
    result = await db.execute(select(Field).where(Field.id == field_id))
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Get latest satellite data
    sat_result = await db.execute(
        select(SatelliteData)
        .where(SatelliteData.field_id == field_id)
        .where(SatelliteData.ndvi.isnot(None))
        .order_by(SatelliteData.image_date.desc())
        .limit(5)
    )
    satellite_data = sat_result.scalars().all()

    # Get latest NDVI and date
    latest_ndvi = None
    latest_ndvi_date = None
    if satellite_data:
        latest_ndvi = satellite_data[0].ndvi
        latest_ndvi_date = satellite_data[0].image_date

    # Calculate health status
    health_status = _calculate_health_status(latest_ndvi, field.crop_type)

    # Build response
    field_detail = FieldDetail(
        id=field.id,
        name=field.name,
        description=field.description,
        district_id=field.district_id,
        geometry=field.geometry_geojson,
        centroid_latitude=field.centroid_latitude,
        centroid_longitude=field.centroid_longitude,
        area_hectares=field.area_hectares,
        crop_type=field.crop_type,
        variety=field.variety,
        status=field.status,
        owner_id=field.owner_id,
        owner_name=field.owner_name,
        created_at=field.created_at,
        updated_at=field.updated_at,
        latest_ndvi=latest_ndvi,
        latest_ndvi_date=latest_ndvi_date,
        health_status=health_status,
    )

    # Count unread alerts
    from app.models.alert import Alert

    alert_result = await db.execute(
        select(func.count(Alert.id))
        .where(Alert.field_id == field_id)
        .where(Alert.is_read == False)
    )
    field_detail.alerts = alert_result.scalar() or 0

    return FieldDetailResponse(data=field_detail)


@router.post("", response_model=FieldDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_field(
    field_data: FieldCreate,
    db: DBSession,
    user_id: UserId,
) -> FieldDetailResponse:
    """Create a new agricultural field."""
    # Calculate centroid from geometry
    centroid = _calculate_centroid(field_data.geometry)
    area = _calculate_area_hectares(field_data.geometry)

    # Create field instance
    field = Field(
        id=uuid4().hex,
        name=field_data.name,
        description=field_data.description,
        district_id=field_data.district_id,
        geometry=_geojson_to_wkt(field_data.geometry),
        centroid_latitude=centroid["lat"],
        centroid_longitude=centroid["lon"],
        area_hectares=area,
        crop_type=field_data.crop_type,
        variety=field_data.variety,
        status="active",
        owner_id=field_data.owner_id,
        owner_name=field_data.owner_name,
    )

    db.add(field)
    await db.commit()
    await db.refresh(field)

    # Convert to response
    field_detail = FieldDetail(
        id=field.id,
        name=field.name,
        description=field.description,
        district_id=field.district_id,
        geometry=field.geometry_geojson,
        centroid_latitude=field.centroid_latitude,
        centroid_longitude=field.centroid_longitude,
        area_hectares=field.area_hectares,
        crop_type=field.crop_type,
        variety=field.variety,
        status=field.status,
        owner_id=field.owner_id,
        owner_name=field.owner_name,
        created_at=field.created_at,
        updated_at=field.updated_at,
        latest_ndvi=None,
        latest_ndvi_date=None,
        health_status="moderate",
    )

    return FieldDetailResponse(data=field_detail)


@router.put("/{field_id}", response_model=FieldDetailResponse)
async def update_field(
    field_id: str,
    field_data: FieldUpdate,
    db: DBSession,
    user_id: UserId,
) -> FieldDetailResponse:
    """Update an existing field."""
    result = await db.execute(select(Field).where(Field.id == field_id))
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # Update fields
    if field_data.name is not None:
        field.name = field_data.name
    if field_data.description is not None:
        field.description = field_data.description
    if field_data.crop_type is not None:
        field.crop_type = field_data.crop_type
    if field_data.variety is not None:
        field.variety = field_data.variety
    if field_data.status is not None:
        field.status = field_data.status

    await db.commit()
    await db.refresh(field)

    # Get latest NDVI
    sat_result = await db.execute(
        select(SatelliteData.ndvi, SatelliteData.image_date)
        .where(SatelliteData.field_id == field_id)
        .where(SatelliteData.ndvi.isnot(None))
        .order_by(SatelliteData.image_date.desc())
        .limit(1)
    )
    latest_sat = sat_result.first()

    health_status = _calculate_health_status(
        latest_sat[0] if latest_sat else None,
        field.crop_type,
    )

    field_detail = FieldDetail(
        id=field.id,
        name=field.name,
        description=field.description,
        district_id=field.district_id,
        geometry=field.geometry_geojson,
        centroid_latitude=field.centroid_latitude,
        centroid_longitude=field.centroid_longitude,
        area_hectares=field.area_hectares,
        crop_type=field.crop_type,
        variety=field.variety,
        status=field.status,
        owner_id=field.owner_id,
        owner_name=field.owner_name,
        created_at=field.created_at,
        updated_at=field.updated_at,
        latest_ndvi=latest_sat[0] if latest_sat else None,
        latest_ndvi_date=latest_sat[1] if latest_sat else None,
        health_status=health_status,
    )

    return FieldDetailResponse(data=field_detail)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_field(
    field_id: str,
    db: DBSession,
    user_id: UserId,
) -> None:
    """Delete a field."""
    result = await db.execute(select(Field).where(Field.id == field_id))
    field = result.scalar_one_or_none()

    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    await db.delete(field)
    await db.commit()


def _calculate_health_status(ndvi: float | None, crop_type: str) -> str:
    """Calculate health status based on NDVI and crop type."""
    if ndvi is None:
        return "moderate"

    # Crop-specific thresholds for Saudi arid regions
    thresholds = {
        "dates": (0.45, 0.6),      # Date palms have higher NDVI
        "wheat": (0.35, 0.55),     # Wheat
        "tomatoes": (0.4, 0.6),   # Tomatoes
        "alfalfa": (0.45, 0.65),  # Alfalfa
        "sorghum": (0.35, 0.55),  # Sorghum
        "citrus": (0.5, 0.65),    # Citrus
    }

    min_ndvi, max_ndvi = thresholds.get(crop_type, (0.3, 0.5))

    if ndvi >= max_ndvi:
        return "excellent"
    elif ndvi >= (min_ndvi + max_ndvi) / 2:
        return "good"
    elif ndvi >= min_ndvi:
        return "moderate"
    else:
        return "poor"


def _calculate_centroid(geometry: dict) -> dict:
    """Calculate centroid from GeoJSON polygon."""
    coords = geometry["coordinates"][0]
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]

    return {
        "lat": sum(lats) / len(lats),
        "lon": sum(lons) / len(lons),
    }


def _calculate_area_hectares(geometry: dict) -> float:
    """Calculate approximate area in hectares from GeoJSON polygon."""
    import math

    coords = geometry["coordinates"][0]
    area = 0.0

    for i in range(len(coords)):
        j = (i + 1) % len(coords)
        lat1, lon1 = coords[i][1], coords[i][0]
        lat2, lon2 = coords[j][1], coords[j][0]

        area += (lon2 - lon1) * (2 + math.sin(math.radians(lat1)) +
                 math.sin(math.radians(lat2)))

    # Convert to hectares (approximate)
    area_abs = abs(area) * 111320 * 111320 / 10000
    return round(area_abs, 2)


def _geojson_to_wkt(geometry: dict) -> str:
    """Convert GeoJSON polygon to WKT format."""
    coords = geometry["coordinates"][0]
    coord_str = ", ".join([f"{c[0]} {c[1]}" for c in coords])
    return f"POLYGON(({coord_str}))"
