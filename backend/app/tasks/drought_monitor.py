"""
SAWS Drought Monitoring Tasks

Celery tasks for SPEI calculation and drought classification.
"""

import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import async_session_maker
from app.models.alert import Alert, AlertSeverity, AlertType
from app.models.field import Field
from app.services.drought.spei import calculate_spei_for_location
from app.services.drought.classifier import classify_drought

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(name="app.tasks.drought.calculate_spei")
def calculate_spei() -> dict:
    """
    Calculate SPEI (Standardized Precipitation Evapotranspiration Index)
    for all field locations.

    Calculates SPEI at multiple time scales:
    - SPEI-3 (short-term)
    - SPEI-6 (medium-term)
    - SPEI-12 (long-term)
    """
    logger.info("Starting SPEI calculation")

    try:
        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Calculating SPEI for {len(fields)} field locations")

            calculated_count = 0
            for field in fields:
                try:
                    # Calculate SPEI for different time scales
                    for scale in [3, 6, 12]:
                        spei_value = calculate_spei_for_location(
                            latitude=field.centroid_latitude,
                            longitude=field.centroid_longitude,
                            scale_months=scale,
                        )

                        # Store SPEI value (would need SPEI table/model)
                        # For now, we'll use it directly in alert generation

                        logger.debug(
                            f"SPEI-{scale} for field {field.id}: {spei_value:.2f}"
                        )

                    calculated_count += 1

                except Exception as e:
                    logger.error(f"Error calculating SPEI for field {field.id}: {e}")
                    continue

            logger.info(f"Successfully calculated SPEI for {calculated_count} locations")

            return {
                "status": "success",
                "locations_processed": calculated_count,
            }

    except Exception as e:
        logger.error(f"Error in SPEI calculation task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.drought.classify_drought_status")
def classify_drought_status() -> dict:
    """
    Classify drought status for all fields based on SPEI and NDVI.

    Generates alerts for drought conditions.
    """
    logger.info("Starting drought status classification")

    try:
        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            classified_count = 0
            alerts_created = 0

            for field in fields:
                try:
                    # Get latest SPEI value (3-month scale)
                    spei_value = calculate_spei_for_location(
                        latitude=field.centroid_latitude,
                        longitude=field.centroid_longitude,
                        scale_months=3,
                    )

                    # Get latest NDVI
                    sat_result = await session.execute(
                        select(SatelliteData)
                        .where(
                            SatelliteData.field_id == field.id,
                            SatelliteData.ndvi.isnot(None),
                        )
                        .order_by(SatelliteData.image_date.desc())
                        .limit(1)
                    )
                    latest_sat = sat_result.scalar_one_or_none()

                    ndvi_value = latest_sat.ndvi if latest_sat else None

                    # Classify drought status
                    drought_status = classify_drought(
                        spei=spei_value,
                        ndvi=ndvi_value,
                    )

                    logger.info(
                        f"Field {field.id}: SPEI={spei_value:.2f}, "
                        f"NDVI={ndvi_value}, Status={drought_status['status']}"
                    )

                    # Generate alert for severe/extreme drought
                    if drought_status["status"] in ["extreme", "severe"]:
                        # Check for existing recent alert
                        recent_alert = await session.execute(
                            select(Alert)
                            .where(
                                Alert.field_id == field.id,
                                Alert.alert_type == AlertType.DROUGHT,
                                Alert.severity.in_(
                                    [AlertSeverity.CRITICAL, AlertSeverity.WARNING]
                                ),
                                Alert.created_at >= datetime.now() - timedelta(days=7),
                            )
                            .order_by(Alert.created_at.desc())
                            .limit(1)
                        )

                        if not recent_alert.scalar_one_or_none():
                            # Create new alert
                            alert = Alert(
                                user_id=field.owner_id,
                                field_id=field.id,
                                severity=AlertSeverity.CRITICAL
                                if drought_status["status"] == "extreme"
                                else AlertSeverity.WARNING,
                                alert_type=AlertType.DROUGHT,
                                title=f"{drought_status['status'].capitalize()} Drought Detected",
                                message=f"Field '{field.name}' is experiencing {drought_status['status']} drought conditions. "
                                f"SPEI: {spei_value:.2f}. NDVI: {ndvi_value:.2f if ndvi_value else 'N/A'}.",
                                district=field.district_id,
                                priority=90 if drought_status["status"] == "extreme" else 70,
                                data={
                                    "spei": spei_value,
                                    "ndvi": ndvi_value,
                                    "status": drought_status["status"],
                                },
                            )

                            session.add(alert)
                            alerts_created += 1

                    classified_count += 1

                except Exception as e:
                    logger.error(f"Error classifying drought for field {field.id}: {e}")
                    continue

            await session.commit()
            logger.info(
                f"Classified {classified_count} fields, created {alerts_created} alerts"
            )

            return {
                "status": "success",
                "fields_classified": classified_count,
                "alerts_created": alerts_created,
            }

    except Exception as e:
        logger.error(f"Error in drought classification task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.drought.forecast_drought")
def forecast_drought(days: int = 30) -> dict:
    """
    Generate drought forecast for the next N days.

    Uses ML models to predict SPEI values.

    Args:
        days: Number of days to forecast
    """
    logger.info(f"Generating {days}-day drought forecast")

    try:
        # Implementation would use ML models for forecasting
        # For now, return placeholder

        return {
            "status": "success",
            "message": "Drought forecasting not yet implemented",
        }

    except Exception as e:
        logger.error(f"Error in drought forecast task: {e}")
        return {"status": "error", "message": str(e)}
