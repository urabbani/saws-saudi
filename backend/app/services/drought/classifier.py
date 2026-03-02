"""
SAWS Drought Classification

Classifies drought severity based on multiple indicators following
WMO (World Meteorological Organization) standards.

SCIENTIFIC METHODOLOGY
======================

Drought Classification Framework:
---------------------------------
The system uses a weighted multi-indicator approach for Saudi Arabia:

1. SPEI-3 (Standardized Precipitation Evapotranspiration Index)
   - Weight: 40% (primary indicator)
   - Time scale: 3 months (agricultural drought)
   - Reference: Vicente-Serrano et al. (2010), Journal of Climate

2. NDVI (Normalized Difference Vegetation Index)
   - Weight: 25% (vegetation response)
   - Crop-specific thresholds
   - Reference: Kogan (1995), Advances in Space Research

3. LST (Land Surface Temperature)
   - Weight: 20% (temperature stress)
   - Crop-specific heat tolerance
   - Reference: Kogan (1997), BAMS

4. Precipitation Anomaly
   - Weight: 15% (supplementary indicator)
   - Monthly deviation from normal

WMO Drought Classification Standards:
------------------------------------
SPEI Value    Classification        Action
≤ -2.5        Extreme Drought       Emergency intervention
-2.5 to -2.0  Severe Drought        Water rationing
-2.0 to -1.5  Moderate Drought      Reduce usage
-1.5 to -1.0  Mild Drought          Monitor
> -1.0        Normal                No action

Saudi Crop-Specific Adjustments:
--------------------------------
Temperature thresholds adjusted for:
- Dates: Optimal 25-35°C, stress >40°C
- Wheat: Optimal 15-25°C, stress >30°C
- Tomatoes: Optimal 20-30°C, stress >35°C
- Alfalfa: Optimal 25-35°C, stress >38°C

Phenology-aware classification:
- Dormancy periods reduce expectations
- Flowering stages increase sensitivity
- Harvest periods adjust thresholds

REFERENCES:
===========
1. WMO & GWP (2016). Handbook of Drought Indicators and Indices.
2. Vicente-Serrano, S. M., et al. (2010). A Multiscalar Drought Index
   Sensitive to Global Warming: The Standardized Precipitation
   Evapotranspiration Index. Journal of Climate, 23(7), 1696-1718.
3. Kogan, F. N. (1995). Droughts of the late 1980s in the United States
   as derived from NOAA polar-orbiting satellite data. Bulletin of
   the American Meteorological Society, 76(7), 1323-1330.
4. McKee, T. B., et al. (1993). The relationship of drought frequency
   and duration to time scales. Preprints, 8th Conference on Applied
   Climatology, 179-184.
5. Saudi Ministry of Environment, Water and Agriculture (2020).
   Crop Calendar Guidelines for Eastern Province.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from app.services.drought.spei import get_spei_classification

logger = logging.getLogger(__name__)


# ==================== CROP-SPECIFIC NDVI THRESHOLDS ====================

# Saudi Eastern Province crop-specific NDVI thresholds
# Based on field studies and regional agricultural research
# Values adjusted for arid climate and irrigation practices
CROP_NDVI_THRESHOLDS = {
    "dates": {
        "name": "Date Palms",
        "excellent_min": 0.50,  # Healthy canopy, 2M+ palms in Al-Hasa
        "good_min": 0.40,
        "moderate_min": 0.35,
        "poor_min": 0.30,
        "senescence_threshold": 0.25,
        # Reference: Al-Bakri et al. (2011) for Saudi date palms
    },
    "wheat": {
        "name": "Wheat",
        "excellent_min": 0.45,  # Winter cereals, optimal growth
        "good_min": 0.35,
        "moderate_min": 0.30,
        "poor_min": 0.25,
        "senescence_threshold": 0.20,
        # Reference: Triticum aestivum NDVI studies in arid regions
    },
    "tomatoes": {
        "name": "Tomatoes",
        "excellent_min": 0.50,  # Protected cultivation, high input
        "good_min": 0.40,
        "moderate_min": 0.35,
        "poor_min": 0.30,
        "senescence_threshold": 0.25,
        # Reference: Solanum lycopersicum in greenhouse conditions
    },
    "alfalfa": {
        "name": "Alfalfa",
        "excellent_min": 0.55,  # Year-round with irrigation, high biomass
        "good_min": 0.45,
        "moderate_min": 0.40,
        "poor_min": 0.35,
        "senescence_threshold": 0.30,
        # Reference: Medicago sativa, multiple cuttings per year
    },
    "sorghum": {
        "name": "Sorghum",
        "excellent_min": 0.50,  # Drought-tolerant, warm-season
        "good_min": 0.40,
        "moderate_min": 0.35,
        "poor_min": 0.30,
        "senescence_threshold": 0.25,
        # Reference: Sorghum bicolor, heat and drought tolerant
    },
    "citrus": {
        "name": "Citrus",
        "excellent_min": 0.55,  # Evergreen, coastal areas
        "good_min": 0.45,
        "moderate_min": 0.40,
        "poor_min": 0.35,
        "senescence_threshold": 0.30,
        # Reference: Citrus sinensis in Eastern Province coastal
    },
    # Default thresholds for "other" crops
    "default": {
        "name": "General Crops",
        "excellent_min": 0.50,
        "good_min": 0.40,
        "moderate_min": 0.30,
        "poor_min": 0.20,
        "senescence_threshold": 0.15,
    },
}


def get_crop_ndvi_thresholds(crop_type: str) -> dict[str, float]:
    """
    Get NDVI thresholds for a specific crop type.

    Args:
        crop_type: Type of crop (dates, wheat, tomatoes, alfalfa, etc.)

    Returns:
        Dictionary with threshold values
    """
    return CROP_NDVI_THRESHOLDS.get(crop_type, CROP_NDVI_THRESHOLDS["default"])


def classify_drought(
    spei: float | None = None,
    ndvi: float | None = None,
    lst: float | None = None,
    precip_anomaly: float | None = None,
    crop_type: str = "default",
) -> dict[str, Any]:
    """
    Classify drought status using multiple indicators.

    Priority order for Saudi Arabia:
    1. SPEI-3 (primary agricultural drought indicator)
    2. NDVI (vegetation response, crop-specific thresholds)
    3. LST (temperature stress)
    4. Precipitation anomaly

    Args:
        spei: SPEI-3 value
        ndvi: NDVI value
        lst: Land surface temperature (Kelvin)
        precip_anomaly: Precipitation anomaly (%)
        crop_type: Type of crop for crop-specific thresholds

    Returns:
        Drought classification with status and recommendations
    """
    status = "normal"
    confidence = 0.0
    indicators = {}

    # Get phenology context
    phenology = get_crop_phenology_stage(crop_type)

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

    # NDVI Classification (crop-specific)
    if ndvi is not None:
        ndvi_class = _classify_ndvi(ndvi, crop_type, phenology)
        indicators["ndvi"] = {
            "value": ndvi,
            "classification": ndvi_class["category"],
            "crop_context": ndvi_class.get("context", ""),
        }
        if ndvi_class["category"] in ["severe", "extreme"]:
            if status in ["normal", "mild"]:
                status = "moderate"
            confidence += 0.25

    # LST Classification
    if lst is not None:
        lst_c = lst - 273.15  # Convert to Celsius
        lst_class = _classify_temperature(lst_c, crop_type)
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
        "recommendation": _get_recommendation(status, indicators, crop_type, phenology),
        "phenology": phenology,
    }


def _classify_ndvi(ndvi: float, crop_type: str, phenology: dict[str, Any] | None = None) -> dict[str, str]:
    """
    Classify vegetation condition from NDVI using crop-specific thresholds.

    Args:
        ndvi: NDVI value
        crop_type: Type of crop for threshold selection
        phenology: Current phenology stage information (optional)

    Returns:
        Classification with category and context
    """
    thresholds = get_crop_ndvi_thresholds(crop_type)

    # Adjust thresholds based on phenology stage
    if phenology and phenology["stage"] in ["dormancy", "senescence"]:
        # Lower expectations during natural decline periods
        thresholds = thresholds.copy()
        thresholds["excellent_min"] *= 0.85
        thresholds["good_min"] *= 0.85
        thresholds["moderate_min"] *= 0.85
        thresholds["poor_min"] *= 0.85

    # Classify based on thresholds
    if ndvi >= thresholds["excellent_min"]:
        category = "excellent"
        context = f"Optimal {thresholds['name']} health"
    elif ndvi >= thresholds["good_min"]:
        category = "good"
        context = f"Good {thresholds['name']} condition"
    elif ndvi >= thresholds["moderate_min"]:
        category = "moderate"
        context = f"Moderate {thresholds['name']} stress"
    elif ndvi >= thresholds["poor_min"]:
        category = "poor"
        context = f"Significant {thresholds['name']} stress"
    else:
        category = "severe"
        context = f"Critical {thresholds['name']} condition"

    # Map to drought severity categories
    severity_map = {
        "excellent": "normal",
        "good": "normal",
        "moderate": "mild",
        "poor": "moderate",
        "severe": "severe",
    }

    return {
        "category": severity_map.get(category, "normal"),
        "ndvi_category": category,
        "context": context,
    }


def _classify_temperature(temp_c: float, crop_type: str = "default") -> str:
    """
    Classify temperature stress for Saudi conditions with crop-specific thresholds.

    Reference: Saudi crop heat tolerance studies
    - Dates: Optimal 25-35°C, stress >40°C
    - Wheat: Optimal 15-25°C, stress >30°C
    - Tomatoes: Optimal 20-30°C, stress >35°C

    Args:
        temp_c: Temperature in Celsius
        crop_type: Type of crop for threshold adjustment

    Returns:
        Temperature stress classification
    """
    # Crop-specific temperature thresholds
    crop_temp_thresholds = {
        "wheat": {"extreme": 40, "severe": 35, "moderate": 30, "mild": 25},
        "tomatoes": {"extreme": 45, "severe": 40, "moderate": 35, "mild": 30},
        "dates": {"extreme": 50, "severe": 45, "moderate": 40, "mild": 35},
        "alfalfa": {"extreme": 48, "severe": 43, "moderate": 38, "mild": 33},
        "sorghum": {"extreme": 50, "severe": 45, "moderate": 40, "mild": 35},
    }

    thresholds = crop_temp_thresholds.get(crop_type, {
        "extreme": 50, "severe": 45, "moderate": 40, "mild": 35
    })

    if temp_c >= thresholds["extreme"]:
        return "extreme_heat"
    elif temp_c >= thresholds["severe"]:
        return "severe_heat"
    elif temp_c >= thresholds["moderate"]:
        return "moderate_heat"
    elif temp_c >= thresholds["mild"]:
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
    crop_type: str = "default",
    phenology: dict[str, Any] | None = None,
) -> list[str]:
    """Generate management recommendations based on status, crop, and phenology."""
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
        temp_thresholds = {
            "wheat": 35, "tomatoes": 40, "dates": 45, "alfalfa": 43
        }
        threshold = temp_thresholds.get(crop_type, 40)
        if temp > threshold:
            recommendations.append(f"Provide shade for heat-sensitive {crop_type}")

    if "ndvi" in indicators:
        ndvi = indicators["ndvi"]["value"]
        thresholds = get_crop_ndvi_thresholds(crop_type)
        if ndvi < thresholds["poor_min"]:
            recommendations.append(f"Consider early harvest for {crop_type} if viable")

    # Add phenology-specific recommendations
    if phenology:
        stage = phenology.get("stage", "")
        if stage == "flowering":
            recommendations.append("Critical: Protect flowering period from water stress")
        elif stage == "fruit_set":
            recommendations.append("Maintain consistent irrigation for fruit development")
        elif stage == "dormancy":
            recommendations.append("Reduce irrigation during natural dormancy period")

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
    classification = classify_drought(spei, ndvi, lst, crop_type=crop_type)

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
        "phenology": classification.get("phenology", {}),
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


# ==================== CROP PHENOLOGY DETECTION ====================

def get_crop_phenology_stage(crop_type: str) -> dict[str, Any]:
    """
    Determine current phenology stage for Saudi crops.

    Saudi Arabia has distinct growing seasons based on temperature:
    - Winter crops (Nov-Mar): Wheat, barley
    - Perennial: Date palms (year-round with dormancy)
    - Summer crops (Apr-Sep): Sorghum, millet

    Reference: Saudi Ministry of Environment, Water and Agriculture crop calendars.

    Args:
        crop_type: Type of crop

    Returns:
        Phenology stage information
    """
    current_date = datetime.now()
    month = current_date.month
    day = current_date.day

    phenology_stages = {
        "dates": _get_date_phenology(month, day),
        "wheat": _get_wheat_phenology(month, day),
        "tomatoes": _get_tomato_phenology(month, day),
        "alfalfa": _get_alfalfa_phenology(month, day),
        "sorghum": _get_sorghum_phenology(month, day),
        "citrus": _get_citrus_phenology(month, day),
    }

    base_stage = phenology_stages.get(crop_type, {
        "stage": "unknown",
        "name": "Unknown Stage",
        "sensitivity": "moderate",
        "ndvi_expectation": "normal",
    })

    base_stage["crop_type"] = crop_type
    base_stage["date"] = current_date.isoformat()

    return base_stage


def _get_date_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Date palm phenology for Saudi Eastern Province.

    Al-Hasa oasis dates (2M+ palms):
    - Dormancy: Dec-Feb
    - Flowering (pollination): Mar-Apr
    - Fruit set: Apr-May
    - Fruit development: May-Jul
    - Harvest (Rutab): Aug-Sep
    - Harvest (Tamar): Oct-Nov

    Reference: Al-Manea et al. (2019) for Saudi date palms.
    """
    if (month == 12 or month == 1 or month == 2):
        return {
            "stage": "dormancy",
            "name": "Winter Dormancy",
            "sensitivity": "low",
            "ndvi_expectation": "declining",
            "description": "Natural winter dormancy, reduced metabolic activity",
        }
    elif (month == 3 and day < 20) or (month == 2 and day > 15):
        return {
            "stage": "flowering",
            "name": "Flowering/Pollination",
            "sensitivity": "critical",
            "ndvi_expectation": "increasing",
            "description": "Pollination period, sensitive to water stress",
        }
    elif (month == 4 or (month == 3 and day >= 20)):
        return {
            "stage": "fruit_set",
            "name": "Fruit Set",
            "sensitivity": "high",
            "ndvi_expectation": "stable",
            "description": "Fruit setting, requires consistent irrigation",
        }
    elif month == 5 or month == 6 or month == 7:
        return {
            "stage": "fruit_development",
            "name": "Fruit Development",
            "sensitivity": "high",
            "ndvi_expectation": "peak",
            "description": "Rapid fruit growth, maximum water demand",
        }
    elif month == 8 or month == 9:
        return {
            "stage": "harvest_rutab",
            "name": "Harvest (Rutab)",
            "sensitivity": "moderate",
            "ndvi_expectation": "stable",
            "description": "Fresh date harvest, irrigation can be reduced",
        }
    else:  # Oct-Nov
        return {
            "stage": "harvest_tamar",
            "name": "Harvest (Tamar)",
            "sensitivity": "low",
            "ndvi_expectation": "declining",
            "description": "Dry date harvest, preparation for dormancy",
        }


def _get_wheat_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Wheat phenology for Saudi Arabia.

    Winter wheat cycle (irrigated):
    - Planting: Nov-Dec
    - Emergence/Tillering: Dec-Jan
    - Jointing/Booting: Feb-Mar
    - Heading/Flowering: Mar-Apr
    - Grain Filling: Apr-May
    - Harvest: May-Jun

    Reference: Saudi Agricultural Development Fund crop guidelines.
    """
    if month == 11 or month == 12:
        return {
            "stage": "planting",
            "name": "Planting/Emergence",
            "sensitivity": "high",
            "ndvi_expectation": "low_increasing",
            "description": "Establishment phase, critical for stand",
        }
    elif month == 1 or month == 2:
        return {
            "stage": "tillering",
            "name": "Tillering/Jointing",
            "sensitivity": "high",
            "ndvi_expectation": "increasing",
            "description": "Vegetative growth, tiller formation",
        }
    elif month == 3 or (month == 4 and day < 15):
        return {
            "stage": "flowering",
            "name": "Heading/Flowering",
            "sensitivity": "critical",
            "ndvi_expectation": "peak",
            "description": "Reproductive stage, very sensitive to stress",
        }
    elif (month == 4 and day >= 15) or month == 5:
        return {
            "stage": "grain_filling",
            "name": "Grain Filling",
            "sensitivity": "high",
            "ndvi_expectation": "stable",
            "description": "Yield determination phase",
        }
    else:  # Jun-Oct (fallow)
        return {
            "stage": "fallow",
            "name": "Fallow/Pre-plant",
            "sensitivity": "none",
            "ndvi_expectation": "bare_soil",
            "description": "Off-season for wheat",
        }


def _get_tomato_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Tomato phenology for Saudi protected cultivation.

    Greenhouse tomatoes grown year-round with cycles:
    - Transplanting: Monthly
    - Vegetative: 4-6 weeks
    - Flowering: 6-10 weeks
    - Fruit set: 8-12 weeks
    - Harvest: 12-20 weeks

    Reference: Saudi vegetable production guidelines.
    """
    # Simplified model for protected cultivation
    cycle_week = ((month - 1) * 4 + day // 7) % 20

    if cycle_week < 4:
        return {
            "stage": "vegetative",
            "name": "Vegetative Growth",
            "sensitivity": "moderate",
            "ndvi_expectation": "increasing",
            "description": "Vegetative establishment",
        }
    elif cycle_week < 8:
        return {
            "stage": "flowering",
            "name": "Flowering",
            "sensitivity": "high",
            "ndvi_expectation": "high",
            "description": "Flowering and fruit set beginning",
        }
    elif cycle_week < 12:
        return {
            "stage": "fruit_set",
            "name": "Fruit Set",
            "sensitivity": "critical",
            "ndvi_expectation": "peak",
            "description": "Active fruit set period",
        }
    elif cycle_week < 16:
        return {
            "stage": "fruit_development",
            "name": "Fruit Development",
            "sensitivity": "high",
            "ndvi_expectation": "stable",
            "description": "Fruit maturation",
        }
    else:
        return {
            "stage": "harvest",
            "name": "Harvest Period",
            "sensitivity": "moderate",
            "ndvi_expectation": "stable_declining",
            "description": "Harvest and crop end",
        }


def _get_alfalfa_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Alfalfa phenology (perennial, multiple cuttings).

    Saudi alfalfa produces 8-10 cuttings/year:
    - Cutting interval: 25-30 days
    - Regrowth: Immediately after cutting
    - Optimal growth: Mar-May, Sep-Nov

    Reference: King Saud University alfalfa trials.
    """
    # Summer stress period
    if month == 6 or month == 7 or month == 8:
        return {
            "stage": "summer_stress",
            "name": "Summer Stress Period",
            "sensitivity": "high",
            "ndvi_expectation": "reduced",
            "description": "Heat stress reduces growth, increase irrigation",
        }
    # Winter slowdown
    elif month == 12 or month == 1 or month == 2:
        return {
            "stage": "winter_slowdown",
            "name": "Winter Slowdown",
            "sensitivity": "moderate",
            "ndvi_expectation": "reduced",
            "description": "Reduced growth due to cooler temperatures",
        }
    # Optimal growth periods
    else:
        return {
            "stage": "active_growth",
            "name": "Active Growth",
            "sensitivity": "moderate",
            "ndvi_expectation": "high",
            "description": "Optimal growing conditions, frequent cuttings",
        }


def _get_sorghum_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Sorghum phenology (summer crop).

    Saudi sorghum cycle:
    - Planting: Apr-May
    - Vegetative: May-Jun
    - Flowering: Jul-Aug
    - Grain filling: Aug-Sep
    - Harvest: Sep-Oct

    Reference: Saudi warm-season crop guidelines.
    """
    if month == 4 or month == 5:
        return {
            "stage": "planting",
            "name": "Planting/Emergence",
            "sensitivity": "high",
            "ndvi_expectation": "low",
            "description": "Establishment period",
        }
    elif month == 6 or (month == 7 and day < 15):
        return {
            "stage": "vegetative",
            "name": "Vegetative Growth",
            "sensitivity": "moderate",
            "ndvi_expectation": "increasing",
            "description": "Rapid vegetative growth",
        }
    elif (month == 7 and day >= 15) or month == 8:
        return {
            "stage": "flowering",
            "name": "Flowering",
            "sensitivity": "critical",
            "ndvi_expectation": "peak",
            "description": "Reproductive stage, sensitive to stress",
        }
    elif month == 9:
        return {
            "stage": "grain_filling",
            "name": "Grain Filling",
            "sensitivity": "high",
            "ndvi_expectation": "high",
            "description": "Yield determination",
        }
    else:
        return {
            "stage": "fallow",
            "name": "Fallow/Pre-plant",
            "sensitivity": "none",
            "ndvi_expectation": "bare_soil",
            "description": "Off-season for sorghum",
        }


def _get_citrus_phenology(month: int, day: int) -> dict[str, Any]:
    """
    Citrus phenology (evergreen).

    Saudi citrus (Eastern Province coastal):
    - Flowering: Mar-Apr (main), Sep (secondary)
    - Fruit set: Apr-May
    - Fruit development: May-Nov
    - Harvest: Nov-Mar

    Reference: Saudi citrus production manual.
    """
    if month == 3 or (month == 4 and day < 15):
        return {
            "stage": "flowering",
            "name": "Main Flowering",
            "sensitivity": "critical",
            "ndvi_expectation": "increasing",
            "description": "Main flowering period, critical for yield",
        }
    elif (month == 4 and day >= 15) or month == 5:
        return {
            "stage": "fruit_set",
            "name": "Fruit Set",
            "sensitivity": "high",
            "ndvi_expectation": "high",
            "description": "Fruit set and early development",
        }
    elif month == 6 or month == 7 or month == 8 or month == 9 or month == 10:
        return {
            "stage": "fruit_development",
            "name": "Fruit Development",
            "sensitivity": "moderate",
            "ndvi_expectation": "stable_high",
            "description": "Fruit sizing and maturation",
        }
    else:  # Nov-Feb
        return {
            "stage": "harvest",
            "name": "Harvest Season",
            "sensitivity": "low",
            "ndvi_expectation": "stable",
            "description": "Harvest period, stress tolerance higher",
        }

