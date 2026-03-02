"""
SAWS SPEI Calculation

Standardized Precipitation Evapotranspiration Index implementation.
Following WMO recommendations for drought monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


def calculate_spei_for_location(
    latitude: float,
    longitude: float,
    scale_months: int = 3,
    start_date: datetime | None = None,
) -> float:
    """
    Calculate SPEI for a specific location and time scale.

    SPEI Standardization:
    1. Calculate P - ET (precipitation minus evapotranspiration)
    2. Sum over the time scale (1, 3, 6, 12, 24 months)
    3. Fit distribution (usually Pearson Type III or Gamma)
    4. Transform to standard normal

    Args:
        latitude: Location latitude
        longitude: Location longitude
        scale_months: Time scale in months (3, 6, 12 recommended)
        start_date: Calculation start date (defaults to 3 years ago)

    Returns:
        SPEI value (negative = drought, positive = wet)
    """
    try:
        # Default: need at least 3 years of data for reliable SPEI
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365 * 3)

        # Get climate data for location
        # This would query TimescaleDB for historical P-ET values
        climate_data = _get_climate_data(
            latitude, longitude, start_date, datetime.now()
        )

        if len(climate_data) < scale_months * 2:
            logger.warning(f"Insufficient data for SPEI-{scale_months} calculation")
            return 0.0

        # Calculate monthly P-ET totals
        monthly_pet = _aggregate_monthly_pet(climate_data)

        # Calculate rolling sum for time scale
        pet_series = _rolling_sum(monthly_pet, scale_months)

        # Standardize using log-logistic distribution
        spei_values = _standardize_spei(pet_series)

        # Return most recent value
        if len(spei_values) > 0:
            return float(spei_values[-1])

        return 0.0

    except Exception as e:
        logger.error(f"Error calculating SPEI: {e}")
        return 0.0


def _get_climate_data(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """
    Get precipitation and evapotranspiration data.

    In production, this queries TimescaleDB with:
    - PME precipitation data
    - FAO Penman-Monteith ET calculation
    - ERA5 reanalysis fallback

    For now, returns simulated data for Eastern Province.
    """
    # Simulate arid region climate data
    data = []
    current = start_date

    # Eastern Province climate characteristics
    base_precip = 5.0  # mm/month (very low)
    base_et = 200.0  # mm/month (very high)
    seasonality = 0.3  # Seasonal variation

    while current <= end_date:
        # Add seasonal variation
        month = current.month
        seasonal_factor = 1 + seasonality * np.sin(2 * np.pi * month / 12)

        # Add some random variation
        precip = max(0, base_precip * seasonal_factor + np.random.exponential(5))
        et = base_et * seasonal_factor + np.random.normal(0, 20)

        # Random drought periods
        if np.random.random() < 0.1:
            precip *= 0.3  # Drought month

        data.append({
            "date": current,
            "precipitation": precip,
            "evapotranspiration": et,
            "pet": precip - et,
        })

        current += timedelta(days=30)

    return data


def _aggregate_monthly_pet(
    climate_data: list[dict[str, Any]],
) -> list[float]:
    """Aggregate daily P-ET to monthly totals."""
    monthly_data = {}

    for record in climate_data:
        month_key = record["date"].strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        monthly_data[month_key].append(record["pet"])

    return [sum(values) for values in monthly_data.values()]


def _rolling_sum(series: list[float], window: int) -> list[float]:
    """Calculate rolling sum for time scale."""
    result = []
    for i in range(len(series) - window + 1):
        result.append(sum(series[i:i + window]))
    return result


def _standardize_spei(series: list[float]) -> list[float]:
    """
    Standardize P-ET series using log-logistic distribution.

    The log-logistic is commonly used for SPEI calculation
    because it handles negative values (P-ET) well.
    """
    if len(series) == 0:
        return []

    series_array = np.array(series)

    # Fit log-logistic distribution
    # For simplicity, using z-score normalization
    # In production, use proper distribution fitting
    mean = np.mean(series_array)
    std = np.std(series_array)

    if std == 0:
        return [0.0] * len(series)

    # Calculate Z-scores
    z_scores = (series_array - mean) / std

    return z_scores.tolist()


def get_spei_classification(spei: float) -> dict[str, Any]:
    """
    Get SPEI classification following WMO standards.

    Args:
        spei: SPEI value

    Returns:
        Classification dict with label and description
    """
    if spei <= -2.5:
        return {
            "label": "Extreme Drought",
            "color": "#8B0000",  # Dark red
            "action": "Emergency: Immediate intervention required",
            "category": "extreme",
        }
    elif spei <= -2.0:
        return {
            "label": "Severe Drought",
            "color": "#DC143C",  # Crimson
            "action": "Critical: Water rationing needed",
            "category": "severe",
        }
    elif spei <= -1.5:
        return {
            "label": "Moderate Drought",
            "color": "#FF4500",  # Orange red
            "action": "Warning: Reduce water usage",
            "category": "moderate",
        }
    elif spei <= -1.0:
        return {
            "label": "Mild Drought",
            "color": "#FFA500",  # Orange
            "action": "Advisory: Monitor conditions",
            "category": "mild",
        }
    elif spei <= 1.0:
        return {
            "label": "Normal",
            "color": "#90EE90",  # Light green
            "action": "Normal conditions",
            "category": "normal",
        }
    else:
        return {
            "label": "Wet",
            "color": "#006400",  # Dark green
            "action": "Above normal precipitation",
            "category": "wet",
        }


def calculate_multi_scale_spei(
    latitude: float,
    longitude: float,
) -> dict[str, float]:
    """
    Calculate SPEI at multiple time scales.

    Provides comprehensive drought assessment:
    - SPEI-1: Short-term (meteorological drought)
    - SPEI-3: Agricultural drought
    - SPEI-6: Hydrological drought onset
    - SPEI-12: Long-term drought
    - SPEI-24: Climate patterns
    """
    scales = {
        "spei_1": 1,
        "spei_3": 3,
        "spei_6": 6,
        "spei_12": 12,
        "spei_24": 24,
    }

    results = {}
    for name, scale in scales.items():
        try:
            results[name] = calculate_spei_for_location(
                latitude, longitude, scale
            )
        except Exception as e:
            logger.error(f"Error calculating {name}: {e}")
            results[name] = 0.0

    return results
