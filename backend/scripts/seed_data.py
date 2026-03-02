#!/usr/bin/env python3
"""
SAWS Data Seeding Script

Seeds the database with initial data for the Eastern Province of Saudi Arabia.
Includes districts, sample fields, and administrative data.

Usage:
    python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import random

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shapely.geometry import shape, Polygon, box
from geojson import Feature, FeatureCollection, Polygon as GeoPolygon

from app.config import get_settings
from app.db.base import async_session_maker
from app.models.field import Field, CropType, SoilType, IrrigationType
from app.models.alert import Alert, AlertSeverity, AlertStatus, AlertType

settings = get_settings()


# Eastern Province Districts with accurate coordinates
EASTERN_PROVINCE_DISTRICTS = [
    {
        "name": "Al-Hasa",
        "name_ar": "الأحساء",
        "center": {"longitude": 49.5833, "latitude": 25.3000},
        "bounds": {"min_lon": 49.30, "min_lat": 25.00, "max_lon": 49.80, "max_lat": 25.80},
        "description": "Largest oasis in the world with 2M+ date palms",
        "area_hectares": 200000,
        "key_crops": ["dates", "citrus", "vegetables"]
    },
    {
        "name": "Qatif",
        "name_ar": "القطيف",
        "center": {"longitude": 50.0000, "latitude": 26.5000},
        "bounds": {"min_lon": 49.80, "min_lat": 26.20, "max_lon": 50.20, "max_lat": 26.70},
        "description": "Coastal date farming region",
        "area_hectares": 35000,
        "key_crops": ["dates", "vegetables"]
    },
    {
        "name": "Hofuf",
        "name_ar": "الهفوف",
        "center": {"longitude": 49.5833, "latitude": 25.3500},
        "bounds": {"min_lon": 49.30, "min_lat": 25.10, "max_lon": 49.80, "max_lat": 25.60},
        "description": "Historic agricultural center",
        "area_hectares": 45000,
        "key_crops": ["dates", "wheat", "alfalfa"]
    },
    {
        "name": "Dammam",
        "name_ar": "الدمام",
        "center": {"longitude": 50.1000, "latitude": 26.4000},
        "bounds": {"min_lon": 49.90, "min_lat": 26.20, "max_lon": 50.30, "max_lat": 26.50},
        "description": "Capital of Eastern Province with urban agriculture",
        "area_hectares": 8000,
        "key_crops": ["vegetables", "ornamental"]
    },
    {
        "name": "Al-Khobar",
        "name_ar": "الخبر",
        "center": {"longitude": 50.2000, "latitude": 26.3000},
        "bounds": {"min_lon": 50.00, "min_lat": 26.15, "max_lon": 50.40, "max_lat": 26.45},
        "description": "Peri-urban agricultural zone",
        "area_hectares": 5000,
        "key_crops": ["vegetables", "citrus"]
    },
    {
        "name": "Al-Jubail",
        "name_ar": "الجبيل",
        "center": {"longitude": 49.6500, "latitude": 27.0000},
        "bounds": {"min_lon": 49.40, "min_lat": 26.80, "max_lon": 50.00, "max_lat": 27.20},
        "description": "Industrial zone with protected agriculture",
        "area_hectares": 6000,
        "key_crops": ["vegetables", "tomatoes"]
    },
    {
        "name": "Hafar Al-Batin",
        "name_ar": "حفر الباطن",
        "center": {"longitude": 46.0000, "latitude": 28.0000},
        "bounds": {"min_lon": 45.50, "min_lat": 27.50, "max_lon": 46.50, "max_lat": 28.50},
        "description": "Northern Eastern Province agricultural zone",
        "area_hectares": 25000,
        "key_crops": ["wheat", "alfalfa", "sorghum"]
    }
]


# Sample field data for testing
SAMPLE_CROPS = [
    CropType.DATES,
    CropType.WHEAT,
    CropType.TOMATOES,
    CropType.ALFALFA,
    CropType.SORGHUM,
    CropType.CITRUS
]

SAMPLE_SOIL_TYPES = [
    SoilType.SANDY,
    SoilType.SANDY_LOAM,
    SoilType.LOAM,
    SoilType.CLAY_LOAM
]

SAMPLE_IRRIGATION_TYPES = [
    IrrigationType.DRIP,
    IrrigationType.SPRINKLER,
    IrrigationType.FLOOD,
    IrrigationType.PERCUTATION
]


def generate_random_field_geometry(district_bounds: dict) -> dict:
    """
    Generate a random field polygon within district bounds.

    Args:
        district_bounds: District boundary coordinates

    Returns:
        GeoJSON polygon geometry
    """
    min_lon = district_bounds["min_lon"]
    min_lat = district_bounds["min_lat"]
    max_lon = district_bounds["max_lon"]
    max_lat = district_bounds["max_lat"]

    # Generate random field size (0.5-5 hectares)
    # Roughly 0.005-0.05 degrees (approximately)
    size = random.uniform(0.005, 0.03)

    # Random center point within district
    center_lon = random.uniform(min_lon + size, max_lon - size)
    center_lat = random.uniform(min_lat + size, max_lat - size)

    # Create a simple rectangular field
    coords = [
        [center_lon, center_lat],
        [center_lon + size, center_lat],
        [center_lon + size, center_lat + size],
        [center_lon, center_lat + size],
        [center_lon, center_lat]  # Close the polygon
    ]

    return {
        "type": "Polygon",
        "coordinates": [coords]
    }


async def seed_districts(session: AsyncSession) -> int:
    """
    Seed district data for Eastern Province.

    Args:
        session: Database session

    Returns:
        Number of districts created
    """
    print("\nSeeding Eastern Province districts...")

    count = 0
    for district_data in EASTERN_PROVINCE_DISTRICTS:
        # Check if district already exists
        result = await session.execute(
            select(Field).where(Field.name == district_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  • District '{district_data['name']}' already exists")
            continue

        # Create district as a field (using field model for geographic data)
        district = Field(
            name=district_data["name"],
            name_ar=district_data.get("name_ar"),
            district=district_data["name"],
            # Create bounds as geometry
            geometry=f"POLYGON(("
            f"{district_data['bounds']['min_lon']} {district_data['bounds']['min_lat']}, "
            f"{district_data['bounds']['max_lon']} {district_data['bounds']['min_lat']}, "
            f"{district_data['bounds']['max_lon']} {district_data['bounds']['max_lat']}, "
            f"{district_data['bounds']['min_lon']} {district_data['bounds']['max_lat']}, "
            f"{district_data['bounds']['min_lon']} {district_data['bounds']['min_lat']}"
            f"))",
            area_hectares=district_data["area_hectares"],
            crop_type=CropType.MIXED,
            description=district_data["description"],
            is_active=True,
            owner_id="system"
        )

        session.add(district)
        count += 1
        print(f"  ✓ Created district: {district_data['name']}")

    await session.commit()
    print(f"✓ Seeded {count} districts")
    return count


async def seed_sample_fields(session: AsyncSession) -> int:
    """
    Seed sample agricultural fields for testing.

    Args:
        session: Database session

    Returns:
        Number of fields created
    """
    print("\nSeeding sample agricultural fields...")

    count = 0
    field_id = 1

    for district in EASTERN_PROVINCE_DISTRICTS:
        # Create 3-8 sample fields per district
        num_fields = random.randint(3, 8)

        for i in range(num_fields):
            # Generate random field data
            crop_type = random.choice(district["key_crops"])
            if crop_type == "dates":
                crop_enum = CropType.DATES
            elif crop_type == "wheat":
                crop_enum = CropType.WHEAT
            elif crop_type == "tomatoes" or crop_type == "vegetables":
                crop_enum = CropType.TOMATOES
            elif crop_type == "alfalfa":
                crop_enum = CropType.ALFALFA
            elif crop_type == "sorghum":
                crop_enum = CropType.SORGHUM
            elif crop_type == "citrus":
                crop_enum = CropType.CITRUS
            else:
                crop_enum = CropType.MIXED

            # Generate geometry
            geom = generate_random_field_geometry(district["bounds"])

            # Create field
            field = Field(
                name=f"{district['name']}-Field-{field_id}",
                name_ar=f"حقل {field_id}",
                district=district["name"],
                geometry=str(geom),
                area_hectares=random.uniform(2.0, 50.0),
                crop_type=crop_enum,
                soil_type=random.choice(SAMPLE_SOIL_TYPES),
                irrigation_type=random.choice(SAMPLE_IRRIGATION_TYPES),
                # Current status
                ndvi=random.uniform(0.25, 0.65),
                soil_moisture=random.uniform(10.0, 35.0),
                temperature=random.uniform(25.0, 42.0),
                # Predictions
                predicted_yield=random.uniform(50.0, 95.0),
                health_status=random.choice(["excellent", "good", "moderate", "poor"]),
                drought_status=random.choice(["none", "mild", "moderate", "severe"]),
                is_active=True,
                owner_id="demo_user",
                description=f"Sample agricultural field in {district['name']}"
            )

            session.add(field)
            count += 1
            field_id += 1

    await session.commit()
    print(f"✓ Seeded {count} sample fields")
    return count


async def seed_sample_alerts(session: AsyncSession) -> int:
    """
    Seed sample alerts for testing.

    Args:
        session: Database session

    Returns:
        Number of alerts created
    """
    print("\nSeeding sample alerts...")

    # Get some field IDs
    result = await session.execute(select(Field).limit(10))
    fields = result.scalars().all()

    if not fields:
        print("  ! No fields found, skipping alerts")
        return 0

    count = 0
    alert_types = [
        AlertType.DROUGHT,
        AlertType.HIGH_TEMPERATURE,
        AlertType.LOW_NDVI,
        AlertType.IRRIGATION_NEEDED
    ]

    for field in fields[:5]:  # Create alerts for first 5 fields
        # Create 1-2 alerts per field
        for _ in range(random.randint(1, 2)):
            alert = Alert(
                field_id=field.id,
                alert_type=random.choice(alert_types),
                severity=random.choice([
                    AlertSeverity.CRITICAL,
                    AlertSeverity.WARNING,
                    AlertSeverity.ADVISORY
                ]),
                status=AlertStatus.ACTIVE,
                title=f"Sample alert for {field.name}",
                message=random.choice([
                    "NDVI values below threshold for current growth stage",
                    "Temperature exceeding optimal range for crop type",
                    "Soil moisture critically low",
                    "Drought conditions detected (SPEI < -1.5)"
                ]),
                location={"lon": 49.5, "lat": 25.3},  # Will be updated from field
                affected_area_hectares=field.area_hectares,
                recommended_actions=random.choice([
                    "Increase irrigation frequency",
                    "Check irrigation system",
                    "Monitor soil moisture daily",
                    "Consider heat stress mitigation"
                ]),
                expires_at=datetime.now() + timedelta(days=7)
            )

            session.add(alert)
            count += 1

    await session.commit()
    print(f"✓ Seeded {count} sample alerts")
    return count


async def main():
    """
    Main seeding function.
    """
    print("=" * 60)
    print("SAWS Database Seeding")
    print("=" * 60)

    async with async_session_maker() as session:
        total_count = 0

        # Seed districts
        total_count += await seed_districts(session)

        # Seed sample fields
        total_count += await seed_sample_fields(session)

        # Seed sample alerts
        total_count += await seed_sample_alerts(session)

        print("\n" + "=" * 60)
        print(f"✓ Seeding complete! Total records created: {total_count}")
        print("\nSample data overview:")
        print("  • 7 Eastern Province districts")
        print("  • 30-50 sample agricultural fields")
        print("  • 5-10 sample alerts")
        print("\nNext steps:")
        print("  1. Start the server: uvicorn app.main:app --reload")
        print("  2. Visit: http://localhost:8000/docs")
        print("  3. Access API: http://localhost:8000/api/v1/fields")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
