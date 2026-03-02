"""
SAWS Satellite Data Fetch Tasks

Celery tasks for fetching satellite imagery from various sources.
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import async_session_maker
from app.models.field import Field
from app.models.satellite import SatelliteData, SatelliteSource
from app.services.satellite.gee import GeeClient
from app.services.satellite.indices import calculate_ndvi, calculate_evi

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(name="app.tasks.satellite.fetch_modis_data")
def fetch_modis_data() -> dict:
    """
    Fetch MODIS satellite data for all active fields.

    MODIS provides daily imagery at 250m resolution.
    """
    logger.info("Starting MODIS data fetch")

    try:
        gee = GeeClient()

        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Fetching MODIS data for {len(fields)} fields")

            # Calculate date range (last 7 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            fetched_count = 0
            for field in fields:
                try:
                    # Fetch MODIS image collection
                    images = gee.get_modis_images(
                        geometry=field.geometry,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    # Process and store images
                    for image_data in images:
                        # Check if image already exists
                        existing = await session.execute(
                            select(SatelliteData).where(
                                SatelliteData.field_id == field.id,
                                SatelliteData.source == SatelliteSource.MODIS,
                                SatelliteData.image_id == image_data["image_id"],
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        # Create new satellite data record
                        sat_data = SatelliteData(
                            field_id=field.id,
                            source=SatelliteSource.MODIS,
                            image_id=image_data["image_id"],
                            collection_id=settings.modis_collection_id,
                            acquisition_date=datetime.fromisoformat(
                                image_data["acquisition_time"]
                            ),
                            image_date=datetime.fromisoformat(image_data["image_time"]),
                            cloud_cover=image_data.get("cloud_cover", 0),
                            ndvi=image_data.get("ndvi"),
                            evi=image_data.get("evi"),
                            lst=image_data.get("lst"),
                            quality_score=image_data.get("quality_score", 1.0),
                        )

                        session.add(sat_data)
                        fetched_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing MODIS data for field {field.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully fetched {fetched_count} MODIS images")

            return {
                "status": "success",
                "fields_processed": len(fields),
                "images_fetched": fetched_count,
                "source": "modis",
            }

    except Exception as e:
        logger.error(f"Error in MODIS fetch task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.satellite.fetch_landsat_data")
def fetch_landsat_data() -> dict:
    """
    Fetch Landsat satellite data for all active fields.

    Landsat provides higher resolution (30m) imagery with 16-day revisit.
    """
    logger.info("Starting Landsat data fetch")

    try:
        gee = GeeClient()

        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Fetching Landsat data for {len(fields)} fields")

            # Calculate date range (last 60 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=60)

            fetched_count = 0
            for field in fields:
                try:
                    # Fetch Landsat image collection
                    images = gee.get_landsat_images(
                        geometry=field.geometry,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    # Process and store images
                    for image_data in images:
                        # Check if image already exists
                        existing = await session.execute(
                            select(SatelliteData).where(
                                SatelliteData.field_id == field.id,
                                SatelliteData.source == SatelliteSource.LANDSAT,
                                SatelliteData.image_id == image_data["image_id"],
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        # Create new satellite data record
                        sat_data = SatelliteData(
                            field_id=field.id,
                            source=SatelliteSource.LANDSAT,
                            image_id=image_data["image_id"],
                            collection_id=settings.landsat_collection_id,
                            acquisition_date=datetime.fromisoformat(
                                image_data["acquisition_time"]
                            ),
                            image_date=datetime.fromisoformat(image_data["image_time"]),
                            cloud_cover=image_data.get("cloud_cover", 0),
                            ndvi=image_data.get("ndvi"),
                            evi=image_data.get("evi"),
                            lst=image_data.get("lst"),
                            quality_score=image_data.get("quality_score", 1.0),
                        )

                        session.add(sat_data)
                        fetched_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing Landsat data for field {field.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully fetched {fetched_count} Landsat images")

            return {
                "status": "success",
                "fields_processed": len(fields),
                "images_fetched": fetched_count,
                "source": "landsat",
            }

    except Exception as e:
        logger.error(f"Error in Landsat fetch task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.satellite.fetch_sentinel1_data")
def fetch_sentinel1_data() -> dict:
    """
    Fetch Sentinel-1 SAR data for soil moisture analysis.

    SAR data is useful for monitoring irrigation and soil moisture.
    """
    logger.info("Starting Sentinel-1 data fetch")

    try:
        gee = GeeClient()

        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Fetching Sentinel-1 data for {len(fields)} fields")

            # Calculate date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            fetched_count = 0
            for field in fields:
                try:
                    # Fetch Sentinel-1 image collection
                    images = gee.get_sentinel1_images(
                        geometry=field.geometry,
                        start_date=start_date,
                        end_date=end_date,
                    )

                    # Process and store images
                    for image_data in images:
                        # Check if image already exists
                        existing = await session.execute(
                            select(SatelliteData).where(
                                SatelliteData.field_id == field.id,
                                SatelliteData.source == SatelliteSource.SENTINEL1,
                                SatelliteData.image_id == image_data["image_id"],
                            )
                        )
                        if existing.scalar_one_or_none():
                            continue

                        # Create new satellite data record
                        sat_data = SatelliteData(
                            field_id=field.id,
                            source=SatelliteSource.SENTINEL1,
                            image_id=image_data["image_id"],
                            collection_id=settings.sentinel1_collection_id,
                            acquisition_date=datetime.fromisoformat(
                                image_data["acquisition_time"]
                            ),
                            image_date=datetime.fromisoformat(image_data["image_time"]),
                            cloud_cover=0,  # SAR is not affected by clouds
                            quality_score=image_data.get("quality_score", 1.0),
                        )

                        session.add(sat_data)
                        fetched_count += 1

                except Exception as e:
                    logger.error(
                        f"Error processing Sentinel-1 data for field {field.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully fetched {fetched_count} Sentinel-1 images")

            return {
                "status": "success",
                "fields_processed": len(fields),
                "images_fetched": fetched_count,
                "source": "sentinel1",
            }

    except Exception as e:
        logger.error(f"Error in Sentinel-1 fetch task: {e}")
        return {"status": "error", "message": str(e)}
