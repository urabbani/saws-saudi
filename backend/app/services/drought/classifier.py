"""
SAWS Drought Classification

Classifies drought severity based on multiple indicators.
"""

import logging
from typing import Any

from app.services.drought.spei import get_spei_classification

logger = logging.getLogger(__name__)


def classify_drought(
    spei: float | None = None,
    ndvi: float | None = None,
    lst: float | None = None,
    precip_anomaly: float | None = None,
) -> dict[str, Any]:
    """
    Classify drought status using multiple indicators.

    Priority order for Saudi Arabia:
    1. SPEI-3 (primary agricultural drought indicator)
    2. NDVI (vegetation response)
    3. LST (temperature stress)
    4. Precipitation anomaly

    Args:
        spei: SPEI-3 value
        ndvi: NDVI value
        lst: Land surface temperature (Kelvin)
        precip_anomaly: Precipitation anomaly (%)

    Returns:
        Drought classification with status and recommendations
    """
    status = "normal"
    confidence = 0.0
    indicators = {}

    # SPEI Classification (highest priority)
    if spei is not None:
        spei_class = get_spei_classification(spei)
        indicators["spei"] = {
            "value": spei,
            "classification": spei_class["category"],
        }
        if spei_class["category"] in ["extreme", "severe", "moderate"]:
            status = spei_class["category"]
            confidence += 0.4

    # NDVI Classification
    if ndvi is not None:
        ndvi_class = _classify_ndvi(ndvi)
        indicators["ndvi"] = {
            "value": ndvi,
            "classification": ndvi_class,
        }
        if ndvi_class in ["severe", "extreme"]:
            if status in ["normal", "mild"]:
                status = "moderate"
            confidence += 0.25

    # LST Classification
    if lst is not None:
        lst_c = lst - 273.15  # Convert to Celsius
        lst_class = _classify_temperature(lst_c)
        indicators["temperature"] = {
            "value": lst_c,
            "unit": "°C",
            "classification": lst_class,
        }
        if lst_class == "extreme_heat":
            if status in ["normal"]:
                status = "moderate"
            confidence += 0.2

    # Precipitation Anomaly
    if precip_anomaly is not None:
        precip_class = _classify_precipitation(precip_anomaly)
        indicators["precipitation_anomaly"] = {
            "value": precip_anomaly,
            "unit": "%",
            "classification": precip_class,
        }
        if precip_class == "severe_deficit":
            if status == "normal":
                status = "mild"
            confidence += 0.15

    # Ensure confidence doesn't exceed 1
    confidence = min(confidence, 1.0)

    # Get status details
    status_details = _get_status_details(status)

    return {
        "status": status,
        "confidence": round(confidence, 2),
        "indicators": indicators,
        "label": status_details["label"],
        "color": status_details["color"],
        "action": status_details["action"],
        "recommendation": _get_recommendation(status, indicators),
    }


def _classify_ndvi(ndvi: float) -> str:
    """Classify vegetation condition from NDVI."""
    if ndvi <= 0.1:
        return "extreme"
    elif ndvi <= 0.2:
        return "severe"
    elif ndvi <= 0.3:
        return "moderate"
    elif ndvi <= 0.4:
        return "mild"
    else:
        return "normal"


def _classify_temperature(temp_c: float) -> str:
    """Classify temperature stress for Saudi conditions."""
    if temp_c >= 50:
        return "extreme_heat"
    elif temp_c >= 45:
        return "severe_heat"
    elif temp_c >= 40:
        return "moderate_heat"
    elif temp_c >= 35:
        return "mild_heat"
    else:
        return "normal"


def _classify_precipitation(anomaly: float) -> str:
    """Classify precipitation anomaly."""
    if anomaly <= -75:
        return "extreme_deficit"
    elif anomaly <= -50:
        return "severe_deficit"
    elif anomaly <= -25:
        return "moderate_deficit"
    elif anomaly <= -10:
        return "mild_deficit"
    else:
        return "normal"


def _get_status_details(status: str) -> dict[str, str]:
    """Get detailed information for drought status."""
    status_map = {
        "extreme": {
            "label": "Extreme Drought",
            "color": "#8B0000",
            "action": "EMERGENCY: Immediate intervention required",
        },
        "severe": {
            "label": "Severe Drought",
            "color": "#DC143C",
            "action": "CRITICAL: Implement emergency measures",
        },
        "moderate": {
            "label": "Moderate Drought",
            "color": "#FF8C00",
            "action": "WARNING: Reduce water consumption",
        },
        "mild": {
            "label": "Abnormally Dry",
            "color": "#FFD700",
            "action": "ADVISORY: Monitor conditions closely",
        },
        "normal": {
            "label": "Normal Conditions",
            "color": "#32CD32",
            "action": "No action required",
        },
    }

    return status_map.get(status, status_map["normal"])


def _get_recommendation(
    status: str,
    indicators: dict[str, Any],
) -> list[str]:
    """Generate management recommendations based on status."""
    recommendations = []

    if status == "extreme":
        recommendations.extend([
            "Activate emergency water rationing",
            "Prioritize critical crops only",
            "Suspend non-essential irrigation",
            "Request government assistance",
        ])
    elif status == "severe":
        recommendations.extend([
            "Reduce irrigation by 50%",
            "Focus on high-value crops",
            "Monitor groundwater levels",
            "Prepare for crop loss",
        ])
    elif status == "moderate":
        recommendations.extend([
            "Reduce irrigation by 25%",
            "Apply mulch to reduce evaporation",
            "Adjust planting schedules",
            "Monitor pest activity",
        ])
    elif status == "mild":
        recommendations.extend([
            "Optimize irrigation schedules",
            "Check irrigation equipment",
            "Monitor weather forecasts",
            "Review drought preparedness",
        ])
    else:
        recommendations.extend([
            "Continue normal operations",
            "Maintain monitoring",
            "Update drought plans",
        ])

    # Add indicator-specific recommendations
    if "temperature" in indicators:
        temp = indicators["temperature"]["value"]
        if temp > 40:
            recommendations.append("Provide shade for heat-sensitive crops")

    if "ndvi" in indicators:
        ndvi = indicators["ndvi"]["value"]
        if ndvi < 0.3:
            recommendations.append("Consider early harvest if viable")

    return recommendations


def generate_drought_report(
    field_id: str,
    field_name: str,
    crop_type: str,
    spei: float | None = None,
    ndvi: float | None = None,
    lst: float | None = None,
) -> dict[str, Any]:
    """
    Generate comprehensive drought report for a field.

    Includes status, recommendations, and historical context.
    """
    classification = classify_drought(spei, ndvi, lst)

    # Add crop-specific context
    crop_context = _get_crop_context(crop_type, ndvi, lst)

    return {
        "field_id": field_id,
        "field_name": field_name,
        "crop_type": crop_type,
        "report_date": datetime.now().isoformat(),
        "status": classification["status"],
        "confidence": classification["confidence"],
        "summary": classification["label"],
        "indicators": classification["indicators"],
        "recommendations": classification["recommendation"],
        "crop_context": crop_context,
        "next_review": _calculate_next_review_date(classification["status"]),
    }


def _get_crop_context(
    crop_type: str,
    ndvi: float | None,
    lst: float | None,
) -> dict[str, Any]:
    """Get crop-specific drought context."""
    crop_info = {
        "dates": {
            "name": "Date Palms",
            "drought_tolerance": "High",
            "optimal_temp": (25, 35),
            "water_needs": "Moderate to High",
            "recovery_potential": "Good",
        },
        "wheat": {
            "name": "Wheat",
            "drought_tolerance": "Low",
            "optimal_temp": (15, 25),
            "water_needs": "High",
            "recovery_potential": "Poor",
        },
        "tomatoes": {
            "name": "Tomatoes",
            "drought_tolerance": "Low",
            "optimal_temp": (20, 30),
            "water_needs": "High",
            "recovery_potential": "Moderate",
        },
        "alfalfa": {
            "name": "Alfalfa",
            "drought_tolerance": "Moderate",
            "optimal_temp": (25, 35),
            "water_needs": "High",
            "recovery_potential": "Good",
        },
    }

    info = crop_info.get(crop_type, crop_info["dates"])

    # Add current stress assessment
    stress_level = "none"
    if lst is not None:
        lst_c = lst - 273.15
        optimal_min, optimal_max = info["optimal_temp"]
        if lst_c > optimal_max + 10:
            stress_level = "severe"
        elif lst_c > optimal_max + 5:
            stress_level = "moderate"
        elif lst_c > optimal_max:
            stress_level = "mild"

    info["current_stress"] = stress_level

    return info


def _calculate_next_review_date(status: str) -> str:
    """Calculate when the next review should occur."""
    from datetime import timedelta

    review_intervals = {
        "extreme": 3,  # 3 days
        "severe": 7,  # 1 week
        "moderate": 14,  # 2 weeks
        "mild": 30,  # 1 month
        "normal": 60,  # 2 months
    }

    days = review_intervals.get(status, 30)
    return (datetime.now() + timedelta(days=days)).isoformat()
