"""
SAWS Alert Generator

Generates alerts based on thresholds and conditions.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.models.alert import AlertSeverity, AlertType
from app.models.field import Field
from app.models.satellite import SatelliteData

logger = logging.getLogger(__name__)


# Alert thresholds for Saudi Arabia
ALERT_THRESHOLDS = {
    # NDVI thresholds (Saudi-specific)
    "ndvi_critical": 0.15,
    "ndvi_warning": 0.25,
    "ndvi_advisory": 0.35,

    # LST thresholds (Celsius)
    "lst_extreme": 50,
    "lst_severe": 45,
    "lst_warning": 40,

    # SPEI thresholds
    "spei_extreme": -2.5,
    "spei_severe": -2.0,
    "spei_moderate": -1.5,

    # NDMI (moisture)
    "ndmi_critical": -0.2,
    "ndmi_warning": 0.0,
}


def generate_alerts_for_field(
    field: Field,
    satellite_data: list[SatelliteData],
) -> list[dict[str, Any]]:
    """
    Generate all applicable alerts for a field.

    Checks:
    - NDVI anomalies (vegetation stress)
    - Temperature stress (LST)
    - Moisture deficit (NDMI)
    - Drought conditions (SPEI)

    Args:
        field: Field object
        satellite_data: Recent satellite data (max 5 records)

    Returns:
        List of alert dictionaries
    """
    alerts = []

    if not satellite_data:
        return alerts

    # Get most recent data
    latest = satellite_data[0]

    # 1. NDVI-based alerts
    if latest.ndvi is not None:
        alerts.extend(_check_ndvi_alerts(field, latest.ndvi))

    # 2. Temperature-based alerts
    if latest.lst is not None:
        alerts.extend(_check_temperature_alerts(field, latest.lst))

    # 3. Moisture-based alerts
    if latest.ndmi is not None:
        alerts.extend(_check_moisture_alerts(field, latest.ndmi))

    # 4. Trend-based alerts
    if len(satellite_data) >= 3:
        alerts.extend(_check_trend_alerts(field, satellite_data))

    # 5. SPEI-based alerts (would need separate data)
    # alerts.extend(_check_spei_alerts(field))

    return alerts


def _check_ndvi_alerts(field: Field, ndvi: float) -> list[dict[str, Any]]:
    """Check for NDVI-based vegetation stress alerts."""
    alerts = []

    if ndvi <= ALERT_THRESHOLDS["ndvi_critical"]:
        alerts.append({
            "severity": AlertSeverity.CRITICAL,
            "alert_type": AlertType.LOW_NDVI,
            "title": f"Critical: Vegetation Stress in {field.name}",
            "message": (
                f"NDVI has dropped to {ndvi:.2f}, indicating severe vegetation stress. "
                f"Immediate irrigation and crop health assessment required."
            ),
            "priority": 90,
            "data": {"ndvi": ndvi, "threshold": ALERT_THRESHOLDS["ndvi_critical"]},
        })
    elif ndvi <= ALERT_THRESHOLDS["ndvi_warning"]:
        alerts.append({
            "severity": AlertSeverity.WARNING,
            "alert_type": AlertType.LOW_NDVI,
            "title": f"Warning: Low Vegetation Index in {field.name}",
            "message": (
                f"NDVI is {ndvi:.2f}, below the warning threshold. "
                f"Review irrigation schedule and crop condition."
            ),
            "priority": 70,
            "data": {"ndvi": ndvi, "threshold": ALERT_THRESHOLDS["ndvi_warning"]},
        })
    elif ndvi <= ALERT_THRESHOLDS["ndvi_advisory"]:
        alerts.append({
            "severity": AlertSeverity.ADVISORY,
            "alert_type": AlertType.LOW_NDVI,
            "title": f"Advisory: Vegetation Index Declining in {field.name}",
            "message": (
                f"NDVI is {ndvi:.2f}. Monitor crop health and irrigation."
            ),
            "priority": 50,
            "data": {"ndvi": ndvi, "threshold": ALERT_THRESHOLDS["ndvi_advisory"]},
        })

    return alerts


def _check_temperature_alerts(field: Field, lst_kelvin: float) -> list[dict[str, Any]]:
    """Check for temperature-based stress alerts."""
    alerts = []
    lst_c = lst_kelvin - 273.15  # Convert to Celsius

    if lst_c >= ALERT_THRESHOLDS["lst_extreme"]:
        alerts.append({
            "severity": AlertSeverity.CRITICAL,
            "alert_type": AlertType.EXTREME_TEMPERATURE,
            "title": f"CRITICAL: Extreme Heat in {field.name}",
            "message": (
                f"Land surface temperature has reached {lst_c:.1f}°C. "
                f"Crops are at risk of permanent damage. Immediate cooling measures required."
            ),
            "priority": 95,
            "data": {"lst": lst_c, "threshold": ALERT_THRESHOLDS["lst_extreme"]},
        })
    elif lst_c >= ALERT_THRESHOLDS["lst_severe"]:
        alerts.append({
            "severity": AlertSeverity.WARNING,
            "alert_type": AlertType.EXTREME_TEMPERATURE,
            "title": f"Severe Heat Stress in {field.name}",
            "message": (
                f"Temperature is {lst_c:.1f}°C. Significant heat stress expected. "
                f"Increase irrigation if possible."
            ),
            "priority": 75,
            "data": {"lst": lst_c, "threshold": ALERT_THRESHOLDS["lst_severe"]},
        })
    elif lst_c >= ALERT_THRESHOLDS["lst_warning"]:
        alerts.append({
            "severity": AlertSeverity.ADVISORY,
            "alert_type": AlertType.EXTREME_TEMPERATURE,
            "title": f"High Temperature in {field.name}",
            "message": (
                f"Temperature is {lst_c:.1f}°C. Monitor crops for heat stress."
            ),
            "priority": 55,
            "data": {"lst": lst_c, "threshold": ALERT_THRESHOLDS["lst_warning"]},
        })

    return alerts


def _check_moisture_alerts(field: Field, ndmi: float) -> list[dict[str, Any]]:
    """Check for moisture deficit alerts."""
    alerts = []

    if ndmi <= ALERT_THRESHOLDS["ndmi_critical"]:
        alerts.append({
            "severity": AlertSeverity.CRITICAL,
            "alert_type": AlertType.SOIL_MOISTURE,
            "title": f"CRITICAL: Severe Moisture Deficit in {field.name}",
            "message": (
                f"NDMI indicates severe water stress ({ndmi:.2f}). "
                f"Immediate irrigation required to prevent crop loss."
            ),
            "priority": 92,
            "data": {"ndmi": ndmi, "threshold": ALERT_THRESHOLDS["ndmi_critical"]},
        })
    elif ndmi <= ALERT_THRESHOLDS["ndmi_warning"]:
        alerts.append({
            "severity": AlertSeverity.WARNING,
            "alert_type": AlertType.SOIL_MOISTURE,
            "title": f"Warning: Low Soil Moisture in {field.name}",
            "message": (
                f"NDMI is {ndmi:.2f}, indicating water stress. "
                f"Irrigation recommended."
            ),
            "priority": 70,
            "data": {"ndmi": ndmi, "threshold": ALERT_THRESHOLDS["ndmi_warning"]},
        })

    return alerts


def _check_trend_alerts(
    field: Field,
    satellite_data: list[SatelliteData],
) -> list[dict[str, Any]]:
    """Check for concerning trends in satellite data."""
    alerts = []

    # Sort by date (oldest to newest)
    sorted_data = sorted(satellite_data, key=lambda x: x.image_date)

    # Check NDVI trend (last 3 images)
    if len(sorted_data) >= 3 and all(s.ndvi for s in sorted_data[-3:]):
        ndvi_values = [s.ndvi for s in sorted_data[-3:]]

        # Calculate trend
        if ndvi_values[0] > ndvi_values[-1]:  # Declining
            decline = ndvi_values[0] - ndvi_values[-1]

            if decline > 0.15:  # Significant decline
                alerts.append({
                    "severity": AlertSeverity.WARNING,
                    "alert_type": AlertType.LOW_NDVI,
                    "title": f"Rapid Vegetation Decline in {field.name}",
                    "message": (
                        f"NDVI has declined by {decline:.2f} over the last "
                        f"{len(sorted_data)} measurements. Investigate cause."
                    ),
                    "priority": 72,
                    "data": {
                        "decline": decline,
                        "start_ndvi": ndvi_values[0],
                        "end_ndvi": ndvi_values[-1],
                    },
                })
            elif decline > 0.05:  # Moderate decline
                alerts.append({
                    "severity": AlertSeverity.ADVISORY,
                    "alert_type": AlertType.LOW_NDVI,
                    "title": f"Vegetation Declining in {field.name}",
                    "message": (
                        f"NDVI has declined from {ndvi_values[0]:.2f} to {ndvi_values[-1]:.2f}. "
                        f"Monitor closely."
                    ),
                    "priority": 52,
                    "data": {
                        "decline": decline,
                        "start_ndvi": ndvi_values[0],
                        "end_ndvi": ndvi_values[-1],
                    },
                })

    # Check for rising temperatures
    if len(sorted_data) >= 3 and all(s.lst for s in sorted_data[-3:]):
        lst_values = [(s.lst - 273.15) for s in sorted_data[-3:]]
        temp_increase = lst_values[-1] - lst_values[0]

        if temp_increase > 5:  # 5°C increase
            alerts.append({
                "severity": AlertSeverity.WARNING,
                "alert_type": AlertType.EXTREME_TEMPERATURE,
                "title": f"Rising Temperature in {field.name}",
                "message": (
                    f"Temperature has increased by {temp_increase:.1f}°C "
                    f"over recent measurements."
                ),
                "priority": 68,
                "data": {
                    "increase": temp_increase,
                    "start_temp": lst_values[0],
                    "end_temp": lst_values[-1],
                },
            })

    return alerts


def generate_irrigation_alert(
    field: Field,
    next_irrigation: datetime,
    current_moisture: float,
) -> dict[str, Any] | None:
    """
    Generate irrigation recommendation alert.

    Args:
        field: Field object
        next_irrigation: Scheduled next irrigation
        current_moisture: Current soil moisture level (0-1)

    Returns:
        Alert dict or None
    """
    if current_moisture < 0.2:
        return {
            "severity": AlertSeverity.CRITICAL,
            "alert_type": AlertType.IRRIGATION_NEEDED,
            "title": f"Irrigation Required: {field.name}",
            "message": (
                f"Soil moisture is critically low ({current_moisture:.1%}). "
                f"Irrigate immediately."
            ),
            "priority": 88,
            "data": {
                "soil_moisture": current_moisture,
                "next_irrigation": next_irrigation.isoformat(),
            },
        }
    elif current_moisture < 0.35:
        return {
            "severity": AlertSeverity.WARNING,
            "alert_type": AlertType.IRRIGATION_NEEDED,
            "title": f"Irrigation Recommended: {field.name}",
            "message": (
                f"Soil moisture is low ({current_moisture:.1%}). "
                f"Irrigation within 24 hours recommended."
            ),
            "priority": 65,
            "data": {
                "soil_moisture": current_moisture,
                "next_irrigation": next_irrigation.isoformat(),
            },
        }

    return None


def generate_harvest_alert(
    field: Field,
    predicted_yield: float,
    optimal_harvest_date: datetime,
) -> dict[str, Any]:
    """
    Generate harvest readiness alert.

    Args:
        field: Field object
        predicted_yield: Predicted yield (tons/hectare)
        optimal_harvest_date: Optimal harvest date

    Returns:
        Alert dict
    """
    days_until_harvest = (optimal_harvest_date - datetime.now()).days

    if days_until_harvest <= 3:
        return {
            "severity": AlertSeverity.ADVISORY,
            "alert_type": AlertType.HARVEST_READY,
            "title": f"Harvest Ready: {field.name}",
            "message": (
                f"{field.crop_type.capitalize()} crop is ready for harvest. "
                f"Predicted yield: {predicted_yield:.1f} tons/hectare. "
                f"Optimal harvest window: Next 3-5 days."
            ),
            "priority": 60,
            "data": {
                "predicted_yield": predicted_yield,
                "optimal_date": optimal_harvest_date.isoformat(),
                "days_remaining": days_until_harvest,
            },
        }
    elif days_until_harvest <= 14:
        return {
            "severity": AlertSeverity.INFO,
            "alert_type": AlertType.HARVEST_READY,
            "title": f"Harvest Approaching: {field.name}",
            "message": (
                f"Harvest in {days_until_harvest} days. "
                f"Prepare equipment and logistics."
            ),
            "priority": 40,
            "data": {
                "predicted_yield": predicted_yield,
                "optimal_date": optimal_harvest_date.isoformat(),
                "days_remaining": days_until_harvest,
            },
        }

    return {
        "severity": AlertSeverity.INFO,
        "alert_type": AlertType.HARVEST_READY,
        "title": f"Harvest Status: {field.name}",
        "message": (
            f"Expected harvest in {days_until_harvest} days. "
            f"Continue monitoring."
        ),
        "priority": 30,
        "data": {
            "predicted_yield": predicted_yield,
            "optimal_date": optimal_harvest_date.isoformat(),
            "days_remaining": days_until_harvest,
        },
    }
