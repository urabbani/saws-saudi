"""
SAWS Vegetation Index Calculation Tasks

Celery tasks for calculating NDVI, EVI, and other vegetation indices.
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import async_session_maker
from app.models.field import Field
from app.models.satellite import SatelliteData, SatelliteSource
from app.services.satellite.indices import (
    calculate_evi,
    calculate_lst,
    calculate_msavi,
    calculate_ndmi,
    calculate_ndvi,
    calculate_savi,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(name="app.tasks.indexes.calculate_vegetation_indices")
def calculate_vegetation_indices() -> dict:
    """
    Calculate vegetation indices for recent satellite data.

    Processes satellite images to calculate:
    - NDVI (Normalized Difference Vegetation Index)
    - EVI (Enhanced Vegetation Index)
    - SAVI (Soil Adjusted Vegetation Index)
    - MSAVI (Modified Soil Adjusted Vegetation Index)
    - NDMI (Normalized Difference Moisture Index)
    """
    logger.info("Starting vegetation index calculation")

    try:
        async with async_session_maker() as session:
            # Get satellite images without calculated indices
            # (images fetched in the last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)

            result = await session.execute(
                select(SatelliteData)
                .where(
                    SatelliteData.created_at >= yesterday,
                    SatelliteData.source.in_(
                        [SatelliteSource.MODIS, SatelliteSource.LANDSAT, SatelliteSource.SENTINEL2]
                    ),
                )
            )
            images = result.scalars().all()

            logger.info(f"Processing {len(images)} satellite images")

            processed_count = 0
            for image in images:
                try:
                    # Get field geometry for GEE
                    field_result = await session.execute(
                        select(Field).where(Field.id == image.field_id)
                    )
                    field = field_result.scalar_one_or_none()

                    if not field:
                        continue

                    # Calculate indices using Google Earth Engine
                    from app.services.satellite.gee import GeeClient

                    gee = GeeClient()

                    # Calculate NDVI
                    if image.ndvi is None:
                        image.ndvi = gee.calculate_index_for_image(
                            image_id=image.image_id,
                            geometry=field.geometry,
                            index_type="ndvi",
                        )

                    # Calculate EVI
                    if image.evi is None:
                        image.evi = gee.calculate_index_for_image(
                            image_id=image.image_id,
                            geometry=field.geometry,
                            index_type="evi",
                        )

                    # Calculate LST (if available)
                    if image.lst is None:
                        image.lst = gee.calculate_index_for_image(
                            image_id=image.image_id,
                            geometry=field.geometry,
                            index_type="lst",
                        )

                    # Update quality score based on cloud cover
                    if image.cloud_cover > 50:
                        image.quality_score = max(0.5, image.quality_score - 0.3)
                    elif image.cloud_cover > 30:
                        image.quality_score = max(0.6, image.quality_score - 0.2)

                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Error calculating indices for image {image.id}: {e}"
                    )
                    continue

            await session.commit()
            logger.info(f"Successfully processed {processed_count} images")

            return {
                "status": "success",
                "images_processed": processed_count,
            }

    except Exception as e:
        logger.error(f"Error in index calculation task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.indexes.recalculate_indices")
def recalculate_indices(field_id: str, start_date: str, end_date: str) -> dict:
    """
    Recalculate vegetation indices for a field and date range.

    Args:
        field_id: Field ID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
    """
    logger.info(f"Recalculating indices for field {field_id} from {start_date} to {end_date}")

    try:
        async with async_session_maker() as session:
            # Get satellite images for the field and date range
            result = await session.execute(
                select(SatelliteData)
                .where(
                    SatelliteData.field_id == field_id,
                    SatelliteData.image_date >= start_date,
                    SatelliteData.image_date <= end_date,
                )
                .order_by(SatelliteData.image_date)
            )
            images = result.scalars().all()

            # Get field
            field_result = await session.execute(
                select(Field).where(Field.id == field_id)
            )
            field = field_result.scalar_one_or_none()

            if not field:
                return {"status": "error", "message": "Field not found"}

            from app.services.satellite.gee import GeeClient

            gee = GeeClient()
            recalculated_count = 0

            for image in images:
                try:
                    # Recalculate all indices
                    image.ndvi = gee.calculate_index_for_image(
                        image_id=image.image_id,
                        geometry=field.geometry,
                        index_type="ndvi",
                    )
                    image.evi = gee.calculate_index_for_image(
                        image_id=image.image_id,
                        geometry=field.geometry,
                        index_type="evi",
                    )

                    recalculated_count += 1

                except Exception as e:
                    logger.error(f"Error recalculating for image {image.id}: {e}")
                    continue

            await session.commit()
            logger.info(f"Recalculated {recalculated_count} images")

            return {
                "status": "success",
                "images_recalculated": recalculated_count,
            }

    except Exception as e:
        logger.error(f"Error in recalculation task: {e}")
        return {"status": "error", "message": str(e)}
