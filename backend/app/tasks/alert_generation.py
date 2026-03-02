"""
SAWS Alert Generation Tasks

Celery tasks for generating and sending alerts.
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
from app.models.satellite import SatelliteData
from app.services.alert.generator import generate_alerts_for_field
from app.services.alert.notifier import send_notification

logger = logging.getLogger(__name__)
settings = get_settings()


@shared_task(name="app.tasks.alerts.generate_alerts")
def generate_alerts() -> dict:
    """
    Generate alerts for all active fields.

    Checks for:
    - Low NDVI (vegetation stress)
    - Extreme temperatures
    - Soil moisture deficit
    - Pest detection risk
    """
    logger.info("Starting alert generation")

    try:
        async with async_session_maker() as session:
            # Get all active fields
            result = await session.execute(
                select(Field).where(Field.status == "active")
            )
            fields = result.scalars().all()

            logger.info(f"Checking alerts for {len(fields)} fields")

            alerts_created = 0
            for field in fields:
                try:
                    # Get latest satellite data
                    sat_result = await session.execute(
                        select(SatelliteData)
                        .where(SatelliteData.field_id == field.id)
                        .order_by(SatelliteData.image_date.desc())
                        .limit(5)
                    )
                    satellite_data = sat_result.scalars().all()

                    # Generate alerts based on thresholds
                    new_alerts = generate_alerts_for_field(field, satellite_data)

                    for alert_data in new_alerts:
                        # Check for similar recent alert
                        recent_alert = await session.execute(
                            select(Alert)
                            .where(
                                Alert.field_id == field.id,
                                Alert.alert_type == alert_data["alert_type"],
                                Alert.created_at >= datetime.now() - timedelta(days=3),
                            )
                            .limit(1)
                        )

                        if not recent_alert.scalar_one_or_none():
                            alert = Alert(
                                user_id=field.owner_id,
                                field_id=field.id,
                                severity=alert_data["severity"],
                                alert_type=alert_data["alert_type"],
                                title=alert_data["title"],
                                message=alert_data["message"],
                                district=field.district_id,
                                priority=alert_data.get("priority", 50),
                                data=alert_data.get("data"),
                            )

                            session.add(alert)
                            alerts_created += 1

                except Exception as e:
                    logger.error(f"Error generating alerts for field {field.id}: {e}")
                    continue

            await session.commit()
            logger.info(f"Generated {alerts_created} new alerts")

            return {
                "status": "success",
                "alerts_created": alerts_created,
            }

    except Exception as e:
        logger.error(f"Error in alert generation task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.alerts.send_pending_notifications")
def send_pending_notifications() -> dict:
    """
    Send pending alert notifications.

    Sends notifications via:
    - Email
    - SMS
    - WhatsApp
    """
    logger.info("Sending pending notifications")

    try:
        async with async_session_maker() as session:
            # Get unsent alerts (critical and warning only)
            result = await session.execute(
                select(Alert)
                .where(
                    Alert.severity.in_([AlertSeverity.CRITICAL, AlertSeverity.WARNING]),
                    Alert.email_sent == False,  # Email as primary notification
                    Alert.created_at >= datetime.now() - timedelta(hours=24),
                )
                .order_by(Alert.created_at)
                .limit(100)
            )
            alerts = result.scalars().all()

            logger.info(f"Found {len(alerts)} pending notifications")

            sent_count = 0
            for alert in alerts:
                try:
                    # Send email notification
                    if settings.alert_email_enabled:
                        success = send_notification(
                            alert_id=alert.id,
                            notification_type="email",
                            alert_data=alert,
                        )

                        if success:
                            alert.email_sent = True
                            sent_count += 1

                    # Send SMS notification (critical only)
                    if alert.severity == AlertSeverity.CRITICAL and settings.alert_sms_enabled:
                        send_notification(
                            alert_id=alert.id,
                            notification_type="sms",
                            alert_data=alert,
                        )
                        alert.sms_sent = True

                    # Send WhatsApp notification (if enabled)
                    if alert.severity == AlertSeverity.CRITICAL and settings.alert_whatsapp_enabled:
                        send_notification(
                            alert_id=alert.id,
                            notification_type="whatsapp",
                            alert_data=alert,
                        )
                        alert.whatsapp_sent = True

                except Exception as e:
                    logger.error(f"Error sending notification for alert {alert.id}: {e}")
                    continue

            await session.commit()
            logger.info(f"Sent {sent_count} notifications")

            return {
                "status": "success",
                "notifications_sent": sent_count,
            }

    except Exception as e:
        logger.error(f"Error in notification sending task: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(name="app.tasks.alerts.cleanup_old_alerts")
def cleanup_old_alerts() -> dict:
    """
    Clean up old alerts beyond retention period.

    Removes alerts older than alert_retention_days.
    """
    logger.info("Cleaning up old alerts")

    try:
        async with async_session_maker() as session:
            cutoff_date = datetime.now() - timedelta(days=settings.alert_retention_days)

            # Delete old alerts
            result = await session.execute(
                select(Alert).where(Alert.created_at < cutoff_date)
            )
            old_alerts = result.scalars().all()

            for alert in old_alerts:
                await session.delete(alert)

            await session.commit()
            logger.info(f"Deleted {len(old_alerts)} old alerts")

            return {
                "status": "success",
                "alerts_deleted": len(old_alerts),
            }

    except Exception as e:
        logger.error(f"Error in alert cleanup task: {e}")
        return {"status": "error", "message": str(e)}
