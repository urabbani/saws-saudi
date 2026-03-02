"""
SAWS SPEI Calculation

Standardized Precipitation Evapotranspiration Index implementation.
Following WMO recommendations and Vicente-Serrano et al. (2010) methodology.

References:
- Vicente-Serrano, S. M., Beguería, S., & López-Moreno, J. I. (2010).
  A Multiscalar Drought Index Sensitive to Global Warming: The Standardized
  Precipitation Evapotranspiration Index. Journal of Climate, 23(7), 1696-1718.
- WMO (2012). Standardized Precipitation Evapotranspiration Index (SPEI) User Guide.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy import stats
from scipy.optimize import fsolve

logger = logging.getLogger(__name__)


# ==================== PROPER DISTRIBUTION FITTING ====================

def fit_log_logistic_params(series: np.ndarray) -> tuple[float, float, float]:
    """
    Fit log-logistic distribution parameters using L-moments method.

    The log-logistic distribution (also known as Fisk distribution)
    is recommended for SPEI calculation as it handles negative values
    (P-ET) well and provides good fits to precipitation data.

    Parameters:
    - alpha (ξ): Scale parameter
    - beta (κ): Shape parameter
    - gamma (γ): Location parameter

    Reference: Vicente-Serrano et al. (2010), Eq. 4-6

    Args:
        series: P-ET values (can be negative)

    Returns:
        (alpha, beta, gamma) parameters for log-logistic distribution
    """
    # Remove NaN values
    clean_series = series[~np.isnan(series)]

    if len(clean_series) < 12:
        # Not enough data for reliable fitting
        logger.warning("Insufficient data for log-logistic fitting")
        return 1.0, 1.0, np.mean(clean_series)

    # Method of L-moments (recommended by Vicente-Serrano)
    # Calculate L-moments
    l1 = np.mean(clean_series)
    sorted_data = np.sort(clean_series)
    n = len(sorted_data)

    # L-moment ratios (simplified approximation)
    b1 = np.sum(sorted_data * (np.arange(1, n + 1) - 0.5) / n) / n
    l2 = 2 * b1 - l1

    # L-CV (coefficient of L-variation)
    t = l2 / l1 if l1 != 0 else 0

    # Estimate parameters from L-moments
    # Using approximation formulas
    if abs(t) < 0.01 or t > 0.95:
        # Fallback to method of moments
        return _fit_moments_log_logistic(clean_series)

    # Shape parameter from L-CV
    # Approximation: t ≈ 1 / (beta + 2) for small t
    beta = max(0.1, (1 - t) / t - 2)

    # Scale parameter
    alpha = l2 * beta * np.sin(np.pi / beta) / np.pi

    # Location parameter
    gamma = l1 - alpha * np.pi / beta / np.sin(np.pi / beta)

    # Ensure valid parameters
    alpha = max(0.1, alpha)
    beta = max(0.1, beta)

    return alpha, beta, gamma


def _fit_moments_log_logistic(series: np.ndarray) -> tuple[float, float, float]:
    """
    Fallback method: fit log-logistic using method of moments.

    Args:
        series: P-ET values

    Returns:
        (alpha, beta, gamma) parameters
    """
    mean = np.mean(series)
    std = np.std(series, ddof=1)

    if std == 0:
        return 1.0, 1.0, mean

    # Approximate parameter relationships
    beta = 3.0  # Reasonable default shape
    alpha = std * beta * np.sin(np.pi / beta) / np.pi
    gamma = mean - alpha * np.pi / beta / np.sin(np.pi / beta)

    return alpha, beta, gamma


def log_logistic_cdf(x: float, alpha: float, beta: float, gamma: float) -> float:
    """
    Calculate log-logistic cumulative distribution function.

    F(x) = 1 / (1 + ((x - gamma) / alpha)^(-beta))

    Reference: Vicente-Serrano et al. (2010), Eq. 7

    Args:
        x: Value to evaluate
        alpha: Scale parameter
        beta: Shape parameter
        gamma: Location parameter

    Returns:
        Cumulative probability [0, 1]
    """
    if alpha <= 0:
        return 0.5

    shifted = (x - gamma) / alpha

    # Avoid numerical issues
    if shifted <= 0 and beta > 0:
        return 0.0
    elif shifted <= 0:
        return 1.0

    try:
        ratio = shifted ** (-beta)
        return 1.0 / (1.0 + ratio)
    except (OverflowError, ZeroDivisionError):
        return 0.5


def log_logistic_ppf(p: float, alpha: float, beta: float, gamma: float) -> float:
    """
    Calculate log-logistic percent point function (inverse CDF).

    F^(-1)(p) = gamma + alpha * (p / (1 - p))^(1/beta)

    Used to transform standard normal values back to original scale.

    Args:
        p: Probability [0, 1]
        alpha: Scale parameter
        beta: Shape parameter
        gamma: Location parameter

    Returns:
        Value corresponding to probability p
    """
    p = np.clip(p, 1e-10, 1 - 1e-10)

    odds = p / (1 - p)
    return gamma + alpha * (odds ** (1 / beta))


def standard_normal_ppf(p: float) -> float:
    """
    Calculate standard normal percent point function (inverse CDF).

    Uses scipy.stats.norm.ppf which implements the inverse
    of the standard normal CDF.

    This transforms the cumulative probability to a Z-score,
    which is the final SPEI value.

    Args:
        p: Probability [0, 1]

    Returns:
        Z-score (SPEI value)
    """
    p = np.clip(p, 1e-10, 1 - 1e-10)
    return stats.norm.ppf(p)


# ==================== MAIN SPEI CALCULATION ====================

def calculate_spei_for_location(
    latitude: float,
    longitude: float,
    scale_months: int = 3,
    start_date: datetime | None = None,
) -> float:
    """
    Calculate SPEI for a specific location and time scale.

    SPEI Calculation Procedure (Vicente-Serrano et al., 2010):
    1. Calculate monthly P - ET (precipitation minus evapotranspiration)
    2. Sum over the time scale (1, 3, 6, 12, 24 months)
    3. Fit log-logistic distribution to historical P-ET values
    4. Transform each value to cumulative probability using CDF
    5. Convert probability to standard normal Z-score

    The resulting SPEI values follow standard normal distribution:
    - SPEI = 0: Median conditions
    - SPEI < 0: Drier than normal (drought)
    - SPEI > 0: Wetter than normal

    Args:
        latitude: Location latitude (Eastern Province: 24-28°N)
        longitude: Location longitude (Eastern Province: 45-55°E)
        scale_months: Time scale in months (3, 6, 12 recommended)
        start_date: Calculation start date (defaults to 3 years ago for calibration)

    Returns:
        SPEI value (negative = drought, positive = wet)

    Example:
        >>> spei_3 = calculate_spei_for_location(26.0, 50.0, scale_months=3)
        >>> # Returns e.g., -1.8 (moderate drought)
    """
    try:
        # Default: need at least 3 years of data for reliable SPEI calibration
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365 * 3)

        # Get climate data for location
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

        if len(pet_series) == 0:
            logger.warning("Empty P-ET series after aggregation")
            return 0.0

        # Convert to numpy array
        pet_array = np.array(pet_series)

        # Fit log-logistic distribution to historical P-ET values
        alpha, beta, gamma = fit_log_logistic_params(pet_array)

        # Calculate SPEI for the most recent value
        latest_pet = pet_array[-1]

        # Transform to cumulative probability using log-logistic CDF
        probability = log_logistic_cdf(latest_pet, alpha, beta, gamma)

        # Transform probability to standard normal Z-score (this is SPEI)
        spei_value = standard_normal_ppf(probability)

        logger.debug(
            f"SPEI-{scale_months}: {spei_value:.2f} "
            f"(P-ET={latest_pet:.1f}mm, params: α={alpha:.1f}, β={beta:.2f}, γ={gamma:.1f})"
        )

        return float(spei_value)

    except Exception as e:
        logger.error(f"Error calculating SPEI: {e}", exc_info=True)
        return 0.0


# ==================== CLIMATE DATA FUNCTIONS ====================

def _get_climate_data(
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """
    Get precipitation and evapotranspiration data.

    Production Implementation:
    - Query TimescaleDB for PME precipitation data
    - Calculate FAO-56 Penman-Monteith reference evapotranspiration
    - Use ERA5 reanalysis as fallback

    Development Mode:
    - Returns realistic simulated data for Eastern Province climate
    - Maintains statistical properties of arid region

    Args:
        latitude: Location latitude
        longitude: Location longitude
        start_date: Start of data period
        end_date: End of data period

    Returns:
        List of daily climate records with P, ET, and P-ET
    """
    # TODO: Implement production data fetching from:
    # - PME (Presidency of Meteorology and Environment) API for precipitation
    # - FAO-56 Penman-Monteith ET calculation using weather stations
    # - ERA5 reanalysis for gap-filling

    # Simulate arid region climate data
    data = []
    current = start_date

    # Eastern Province climate characteristics
    # Based on long-term climatology for Saudi arid regions
    base_precip = 5.0  # mm/month (very low - hyper-arid)
    base_et = 200.0  # mm/month (very high potential ET)
    seasonality = 0.3  # Seasonal variation

    # Set random seed for reproducibility
    rng = np.random.RandomState(seed=int(latitude * 100 + longitude))

    while current <= end_date:
        # Add seasonal variation (summer hotter, slightly wetter)
        month = current.month
        seasonal_factor = 1 + seasonality * np.sin(2 * np.pi * (month - 1) / 12)

        # Precipitation: highly variable, mostly zero
        # 90% of days have no rain in Eastern Province
        if rng.random() < 0.90:
            precip = 0.0
        else:
            # Exponential distribution for rain events
            precip = max(0, base_precip * seasonal_factor * rng.exponential(2) / 30)

        # Evapotranspiration: temperature-driven
        # Peak in summer (Jun-Aug), minimum in winter (Dec-Feb)
        et = base_et * seasonal_factor + rng.normal(0, 15)

        # Random drought periods (10% of months)
        is_drought_month = rng.random() < 0.1
        if is_drought_month:
            precip *= 0.2  # Severe rainfall deficit
            et *= 1.3  # Higher ET due to heat

        data.append({
            "date": current,
            "precipitation": max(0, precip),
            "evapotranspiration": max(0, et),
            "pet": max(0, precip - et),
        })

        current += timedelta(days=1)

    return data


def _aggregate_monthly_pet(
    climate_data: list[dict[str, Any]],
) -> list[float]:
    """
    Aggregate daily P-ET to monthly totals.

    SPEI is calculated on monthly time scales, so we need
    to sum daily values to monthly totals.

    Args:
        climate_data: List of daily climate records

    Returns:
        List of monthly P-ET totals
    """
    monthly_data = {}

    for record in climate_data:
        month_key = record["date"].strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = []
        monthly_data[month_key].append(record["pet"])

    return [sum(values) for values in monthly_data.values()]


def _rolling_sum(series: list[float], window: int) -> list[float]:
    """
    Calculate rolling sum for SPEI time scale.

    SPEI-3 uses 3-month rolling sum, SPEI-6 uses 6-month, etc.
    This represents cumulative water surplus/deficit over the period.

    Args:
        series: Monthly P-ET values
        window: Number of months to sum

    Returns:
        Rolling sum values
    """
    result = []
    for i in range(len(series) - window + 1):
        result.append(sum(series[i:i + window]))
    return result


# ==================== SPEI CLASSIFICATION ====================

def get_spei_classification(spei: float) -> dict[str, Any]:
    """
    Get SPEI classification following WMO standards.

    Classification follows McKee et al. (1993) and WMO guidelines,
    with SPEI-specific thresholds from Vicente-Serrano et al. (2010).

    Args:
        spei: SPEI value

    Returns:
        Classification dict with label, color, action, and category

    Reference:
        - WMO & GWP (2016). Handbook of Drought Indicators and Indices.
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

    Different time scales capture different drought types:
    - SPEI-1: Short-term / meteorological drought (soil moisture)
    - SPEI-3: Agricultural drought (crop response)
    - SPEI-6: Hydrological drought onset (streamflow)
    - SPEI-12: Long-term drought (groundwater, reservoirs)
    - SPEI-24: Climate patterns and trends

    Args:
        latitude: Location latitude
        longitude: Location longitude

    Returns:
        Dictionary of SPEI values at different time scales
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


# ==================== UTILITY FUNCTIONS ====================

def validate_spei_series(spei_values: list[float]) -> dict[str, Any]:
    """
    Validate SPEI time series for scientific correctness.

    Checks that SPEI values follow expected statistical properties:
    - Mean approximately 0 (standard normal)
    - Standard deviation approximately 1
    - No extreme outliers beyond ±6

    Args:
        spei_values: List of SPEI values

    Returns:
        Validation results with statistics and warnings
    """
    if not spei_values:
        return {"valid": False, "error": "Empty SPEI series"}

    spei_array = np.array(spei_values)
    mean = np.mean(spei_array)
    std = np.std(spei_array)
    min_val = np.min(spei_array)
    max_val = np.max(spei_array)

    warnings = []

    # Check mean is near zero
    if abs(mean) > 0.2:
        warnings.append(f"SPEI mean ({mean:.3f}) deviates from expected 0")

    # Check standard deviation is near 1
    if abs(std - 1.0) > 0.2:
        warnings.append(f"SPEI std ({std:.3f}) deviates from expected 1.0")

    # Check for extreme outliers
    if min_val < -6 or max_val > 6:
        warnings.append(f"Extreme SPEI values detected: [{min_val:.2f}, {max_val:.2f}]")

    return {
        "valid": len(warnings) == 0,
        "mean": mean,
        "std": std,
        "min": min_val,
        "max": max_val,
        "count": len(spei_values),
        "warnings": warnings,
    }
