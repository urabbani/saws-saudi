"""
SAWS Evapotranspiration Calculation

FAO-56 Penman-Monteith reference evapotranspiration calculation
for Saudi Arabia's Eastern Province.

Reference:
- FAO Irrigation and Drainage Paper 56 (Allen et al., 1998)
- Crop evapotranspiration - Guidelines for computing crop water requirements
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ==================== FAO-56 PENMAN-MONTEITH METHOD ====================

def calculate_fao56_penman_monteith(
    temperature: float,  # °C
    humidity: float,  # %
    wind_speed: float,  # m/s at 2m height
    solar_radiation: float | None = None,  # MJ/m²/day
    net_radiation: float | None = None,  # MJ/m²/day
    pressure: float = 101.3,  # kPa
    latitude: float = 26.0,  # degrees (Eastern Province)
    elevation: float = 100.0,  # meters
    day_of_year: int | None = None,
) -> dict[str, Any]:
    """
    Calculate reference evapotranspiration (ET₀) using FAO-56 Penman-Monteith method.

    The FAO Penman-Monteith method is the standard for calculating ET₀:
    ET₀ = [0.408Δ(Rn - G) + γ(900/(T+273))u₂(es - ea)] / [Δ + γ(1 + 0.34u₂)]

    Where:
    - Rn: Net radiation at crop surface
    - G: Soil heat flux density
    - T: Mean air temperature at 2m height
    - u₂: Wind speed at 2m height
    - es: Saturation vapor pressure
    - ea: Actual vapor pressure
    - es - ea: Saturation vapor pressure deficit
    - Δ: Slope of saturation vapor pressure curve
    - γ: Psychrometric constant

    Args:
        temperature: Mean daily air temperature (°C)
        humidity: Mean daily relative humidity (%)
        wind_speed: Mean daily wind speed at 2m height (m/s)
        solar_radiation: Solar radiation (MJ/m²/day, optional)
        net_radiation: Net radiation (MJ/m²/day, optional)
        pressure: Atmospheric pressure (kPa, default 101.3)
        latitude: Latitude in degrees (default 26.0 for Eastern Province)
        elevation: Elevation above sea level (m, default 100)
        day_of_year: Day of year (1-366, auto-calculated if None)

    Returns:
        ET₀ calculation results with:
        - eto: Reference evapotranspiration (mm/day)
        - net_radiation: Net radiation (MJ/m²/day)
        - soil_heat_flux: Soil heat flux (MJ/m²/day)
        - vapor_pressure_deficit: Saturation vapor pressure deficit (kPa)
        - delta: Slope of vapor pressure curve
        - gamma: Psychrometric constant
    """
    try:
        # Day of year
        if day_of_year is None:
            day_of_year = datetime.now().timetuple().tm_yday

        # Convert latitude to radians
        lat_rad = math.radians(latitude)

        # ==================== ATMOSPHERIC PRESSURE ====================
        # Calculate atmospheric pressure based on elevation
        # P = P0 * exp(-z / (R * T / g))
        # Simplified: P = 101.3 * ((293 - 0.0065 * z) / 293) ^ 5.26
        if elevation != 100:  # Use elevation if provided
            pressure = 101.3 * math.pow((293 - 0.0065 * elevation) / 293, 5.26)

        # ==================== VAPOR PRESSURE ====================
        # Saturation vapor pressure (es) using Tetens formula
        # es(T) = 0.6108 * exp(17.27 * T / (T + 237.3))
        es = 0.6108 * math.exp(17.27 * temperature / (temperature + 237.3))

        # Actual vapor pressure (ea) from relative humidity
        # ea = es * RH / 100
        ea = es * humidity / 100

        # Vapor pressure deficit
        vpd = es - ea

        # ==================== SLOPE OF VAPOR PRESSURE CURVE ====================
        # Δ = 4098 * es / (T + 237.3)²
        delta = 4098 * es / math.pow(temperature + 237.3, 2)

        # ==================== PSYCHROMETRIC CONSTANT ====================
        # γ = 0.665 * 10^-3 * P
        # Where P is atmospheric pressure (kPa)
        gamma = 0.665e-3 * pressure

        # ==================== NET RADIATION ====================
        if net_radiation is None:
            if solar_radiation is None:
                # Estimate solar radiation for Eastern Province
                solar_radiation = estimate_solar_radiation(
                    latitude, day_of_year, temperature
                )

            # Calculate net radiation
            # Rn = (1 - α) * Rs - Rnl
            # Where α = albedo (0.23 for reference crop)
            albedo = 0.23
            rn_shortwave = (1 - albedo) * solar_radiation

            # Net longwave radiation (simplified)
            # Rnl = σ * Tk⁴ * (0.34 - 0.14√ea) * (1.35 * Rs/Rso - 0.35)
            sigma = 4.903e-9  # Stefan-Boltzmann constant (MJ/K⁴/m²/day)
            tk = temperature + 273.15  # Temperature in Kelvin

            # Clear sky radiation
            rso = estimate_clear_sky_radiation(latitude, elevation, day_of_year)

            # Cloud cover factor
            cloud_factor = 1.35 * solar_radiation / rso - 0.35
            cloud_factor = max(0.05, min(cloud_factor, 1.0))

            rn_longwave = sigma * math.pow(tk, 4) * (0.34 - 0.14 * math.sqrt(ea)) * cloud_factor

            net_radiation = rn_shortwave - rn_longwave

        # ==================== SOIL HEAT FLUX ====================
        # For daily calculations, G ≈ 0
        soil_heat_flux = 0.0

        # ==================== WIND SPEED ADJUSTMENT ====================
        # Adjust wind speed to 2m height if measured at different height
        # u2 = uz * 4.87 / ln(67.8 * z - 5.42)
        # Assuming input is already at 2m, or adjust if needed

        # ==================== PENMAN-MONTEITH ETo ====================
        # ET₀ = [0.408 * Δ * (Rn - G) + γ * (900 / (T + 273)) * u2 * (es - ea)] / [Δ + γ * (1 + 0.34 * u2)]

        numerator_1 = 0.408 * delta * (net_radiation - soil_heat_flux)
        numerator_2 = gamma * (900 / (temperature + 273)) * wind_speed * vpd
        numerator = numerator_1 + numerator_2

        denominator = delta + gamma * (1 + 0.34 * wind_speed)

        eto = numerator / denominator

        # Ensure non-negative
        eto = max(0, eto)

        return {
            "eto": round(eto, 2),  # mm/day
            "net_radiation": round(net_radiation, 2),  # MJ/m²/day
            "soil_heat_flux": round(soil_heat_flux, 2),  # MJ/m²/day
            "vapor_pressure_deficit": round(vpd, 3),  # kPa
            "delta": round(delta, 3),  # kPa/°C
            "gamma": round(gamma, 4),  # kPa/°C
            "saturation_vapor_pressure": round(es, 3),  # kPa
            "actual_vapor_pressure": round(ea, 3),  # kPa
            "method": "FAO-56 Penman-Monteith",
        }

    except Exception as e:
        logger.error(f"Error calculating ET₀: {e}", exc_info=True)
        # Return fallback value
        return {
            "eto": 6.0,  # Typical Eastern Province value
            "net_radiation": 15.0,
            "soil_heat_flux": 0.0,
            "vapor_pressure_deficit": 2.5,
            "delta": 0.15,
            "gamma": 0.067,
            "method": "Fallback (error occurred)",
        }


def estimate_solar_radiation(
    latitude: float,
    day_of_year: int,
    temperature: float,
) -> float:
    """
    Estimate solar radiation for Eastern Province.

    Uses Hargreaves-Samani formula for estimating solar radiation
    from temperature when direct measurements are unavailable.

    Rs = k_r * sqrt(Tmax - Tmin) * Ra

    Args:
        latitude: Latitude in degrees
        day_of_year: Day of year (1-366)
        temperature: Mean daily temperature (°C)

    Returns:
        Estimated solar radiation (MJ/m²/day)
    """
    # Calculate extraterrestrial radiation
    ra = calculate_extraterrestrial_radiation(latitude, day_of_year)

    # Hargreaves coefficient (adjusted for arid regions)
    # Higher value for Eastern Province due to clear skies
    k_r = 0.18  # k_r = 0.16 for interior, 0.19 for coastal

    # Temperature range (assume ±5°C diurnal variation)
    temp_range = 10  # Approximation for Eastern Province

    # Estimate solar radiation
    rs = k_r * math.sqrt(temp_range) * ra

    # Clamp to reasonable range
    rs = max(5.0, min(rs, 30.0))  # 5-30 MJ/m²/day

    return rs


def calculate_extraterrestrial_radiation(
    latitude: float,
    day_of_year: int,
) -> float:
    """
    Calculate extraterrestrial radiation (Ra).

    Ra is the solar radiation at the top of the atmosphere.

    Args:
        latitude: Latitude in degrees
        day_of_year: Day of year (1-366)

    Returns:
        Extraterrestrial radiation (MJ/m²/day)
    """
    # Solar constant
    gsc = 0.0820  # MJ/m²/min

    # Convert latitude to radians
    lat_rad = math.radians(latitude)

    # Solar declination
    # δ = 23.45 * sin(2π * (doy + 284) / 365)
    declination = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)

    # Inverse relative distance Earth-Sun
    # dr = 1 + 0.033 * cos(2π * doy / 365)
    dr = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)

    # Sunset hour angle
    # ωs = arccos(-tan(φ) * tan(δ))
    term = -math.tan(lat_rad) * math.tan(declination)
    term = max(-1, min(term, 1))  # Clamp to [-1, 1]
    sunset_hour_angle = math.acos(term)

    # Ra = (24 * 60 / π) * Gsc * dr * [ωs * sin(φ) * sin(δ) + cos(φ) * cos(δ) * sin(ωs)]
    ra = (
        (24 * 60 / math.pi) * gsc * dr *
        (sunset_hour_angle * math.sin(lat_rad) * math.sin(declination) +
         math.cos(lat_rad) * math.cos(declination) * math.sin(sunset_hour_angle))
    )

    return ra


def estimate_clear_sky_radiation(
    latitude: float,
    elevation: float,
    day_of_year: int,
) -> float:
    """
    Estimate clear sky solar radiation.

    Args:
        latitude: Latitude in degrees
        elevation: Elevation above sea level (m)
        day_of_year: Day of year

    Returns:
        Clear sky radiation (MJ/m²/day)
    """
    # Extraterrestrial radiation
    ra = calculate_extraterrestrial_radiation(latitude, day_of_year)

    # Clear sky radiation
    # Rso = (0.75 + 2e-5 * z) * Ra
    rso = (0.75 + 2e-5 * elevation) * ra

    return rso


# ==================== CROP COEFFICIENTS (Kc) ====================

def get_crop_coefficient(
    crop_type: str,
    growth_stage: str,
) -> float:
    """
    Get crop coefficient (Kc) for FAO-56 ETc calculation.

    ETc = Kc * ET₀

    Saudi-specific Kc values adjusted for:
    - High temperatures
    - Low humidity
    - Sandy soils

    Args:
        crop_type: Type of crop (dates, wheat, tomatoes, alfalfa)
        growth_stage: Growth stage (initial, development, mid, late)

    Returns:
        Crop coefficient (Kc)

    Reference:
        - FAO-56 Irrigation and Drainage Paper 56
        - Saudi Ministry of Agriculture crop guidelines
    """
    # Saudi-adjusted Kc values
    kc_values = {
        "dates": {
            "initial": 0.50,  # Winter dormancy
            "development": 0.70,  # Spring growth
            "mid": 0.95,  # Summer peak
            "late": 0.70,  # Harvest/fall
        },
        "wheat": {
            "initial": 0.40,  # Establishment
            "development": 0.75,  # Tillering
            "mid": 1.15,  # Heading/grain filling
            "late": 0.40,  # Ripening
        },
        "tomatoes": {
            "initial": 0.60,  # Transplant establishment
            "development": 0.80,  # Vegetative
            "mid": 1.10,  # Flowering/fruit set
            "late": 0.85,  # Harvest
        },
        "alfalfa": {
            "initial": 0.40,  # After cutting
            "development": 0.70,  # Regrowth
            "mid": 1.05,  # Full cover
            "late": 1.05,  # Maintained
        },
        "sorghum": {
            "initial": 0.40,
            "development": 0.75,
            "mid": 1.05,
            "late": 0.70,
        },
        "citrus": {
            "initial": 0.70,
            "development": 0.70,
            "mid": 0.75,
            "late": 0.70,
        },
    }

    if crop_type not in kc_values:
        logger.warning(f"Unknown crop type: {crop_type}, using default")
        crop_type = "dates"

    return kc_values[crop_type].get(growth_stage, 0.70)


# ==================== CROP WATER REQUIREMENT ====================

def calculate_crop_water_requirement(
    crop_type: str,
    growth_stage: str,
    eto: float,
    efficiency: float = 0.85,
    sand_content: float = 0.85,
) -> dict[str, Any]:
    """
    Calculate crop water requirement for Saudi conditions.

    IR = (Kc * ET₀ - Pe) / (Ea * (1 - LR))

    Where:
    - Kc: Crop coefficient
    - ET₀: Reference evapotranspiration
    - Pe: Effective precipitation (negligible in EP)
    - Ea: Irrigation efficiency
    - LR: Leaching requirement (for salt management)

    Args:
        crop_type: Type of crop
        growth_stage: Current growth stage
        eto: Reference ET (mm/day)
        efficiency: Irrigation system efficiency (0-1)
        sand_content: Soil sand content (0-1, affects leaching)

    Returns:
        Water requirement with irrigation recommendation
    """
    # Get crop coefficient
    kc = get_crop_coefficient(crop_type, growth_stage)

    # Calculate crop ET
    etc = kc * eto

    # Effective precipitation (minimal in Eastern Province)
    pe = 0.0  # Assume no effective rainfall

    # Leaching requirement (for salt management in arid soils)
    # LR = ECw / (5 * ECe - ECw) for saline conditions
    # Simplified for EP sandy soils
    lr = 0.10 + 0.10 * sand_content  # 10-20% leaching for sandy soils

    # Calculate irrigation requirement
    # IR = (ETc - Pe) / (Efficiency * (1 - LR))
    if efficiency > 0 and lr < 1:
        irrigation_requirement = (etc - pe) / (efficiency * (1 - lr))
    else:
        irrigation_requirement = etc / efficiency

    # Daily and weekly recommendations
    daily_water = round(irrigation_requirement, 1)
    weekly_water = round(daily_water * 7, 1)

    return {
        "crop_type": crop_type,
        "growth_stage": growth_stage,
        "kc": round(kc, 2),
        "eto": round(eto, 2),
        "crop_et": round(etc, 2),
        "daily_water_mm": daily_water,
        "weekly_water_mm": weekly_water,
        "leaching_requirement": round(lr, 3),
        "irrigation_efficiency": efficiency,
        "next_irrigation_hours": _calculate_irrigation_interval(etc, crop_type),
    }


def _calculate_irrigation_interval(etc: float, crop_type: str) -> int:
    """Calculate irrigation interval in hours based on ETc."""
    # Typical allowable depletion for different crops
    depletion_allowances = {
        "dates": 0.50,  # 50% depletion
        "wheat": 0.55,
        "tomatoes": 0.40,  # Sensitive
        "alfalfa": 0.50,
    }

    depletion = depletion_allowances.get(crop_type, 0.50)

    # Assume 100mm available water holding capacity for sandy loam
    aw = 100  # mm
    raw = aw * depletion  # Readily available water

    # Interval (in hours) = RAW / ETc * 24
    if etc > 0:
        interval_hours = int((raw / etc) * 24)
        # Clamp to reasonable range
        return max(12, min(interval_hours, 72))
    else:
        return 24


# ==================== DAILY DATA PROCESSING ====================

def calculate_daily_et_series(
    weather_data: list[dict[str, Any]],
    latitude: float = 26.0,
    elevation: float = 100,
) -> list[dict[str, Any]]:
    """
    Calculate ET₀ for a series of daily weather data.

    Args:
        weather_data: List of daily weather records with:
            - date: datetime
            - temperature: °C
            - humidity: %
            - wind_speed: m/s
            - solar_radiation: MJ/m²/day (optional)
            - pressure: kPa (optional)
        latitude: Latitude in degrees
        elevation: Elevation in meters

    Returns:
        List of daily ET₀ calculations
    """
    results = []

    for day_data in weather_data:
        day_of_year = day_data["date"].timetuple().tm_yday

        eto_result = calculate_fao56_penman_monteith(
            temperature=day_data["temperature"],
            humidity=day_data["humidity"],
            wind_speed=day_data.get("wind_speed", 3.0),
            solar_radiation=day_data.get("solar_radiation"),
            pressure=day_data.get("pressure", 101.3),
            latitude=latitude,
            elevation=elevation,
            day_of_year=day_of_year,
        )

        results.append({
            "date": day_data["date"].isoformat(),
            **eto_result,
        })

    return results


def validate_et_result(eto: float, temperature: float, month: int) -> dict[str, Any]:
    """
    Validate ET₀ calculation result.

    Checks if ET₀ is within expected range for given conditions
    in Eastern Province.

    Args:
        eto: Calculated ET₀ (mm/day)
        temperature: Air temperature (°C)
        month: Month (1-12)

    Returns:
        Validation result with warnings
    """
    warnings = []

    # Expected ET₀ range for Eastern Province (mm/day)
    # Summer (Jun-Aug): 8-12 mm/day
    # Winter (Dec-Feb): 2-4 mm/day
    # Spring/Fall: 5-8 mm/day

    if month in [6, 7, 8]:  # Summer
        min_eto, max_eto = 6.0, 14.0
    elif month in [12, 1, 2]:  # Winter
        min_eto, max_eto = 1.0, 5.0
    else:  # Spring/Fall
        min_eto, max_eto = 4.0, 10.0

    if eto < min_eto:
        warnings.append(f"ET₀ {eto:.2f} below expected range [{min_eto}, {max_eto}] for month {month}")
    elif eto > max_eto:
        warnings.append(f"ET₀ {eto:.2f} above expected range [{min_eto}, {max_eto}] for month {month}")

    # Temperature consistency check
    if temperature > 40 and eto < 8:
        warnings.append(f"High temperature ({temperature}°C) but low ET₀ ({eto:.2f} mm/day)")

    # Sanity check
    if eto < 0:
        warnings.append("Negative ET₀ calculated")
    elif eto > 20:
        warnings.append("Extremely high ET₀ - possible calculation error")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings,
    }
