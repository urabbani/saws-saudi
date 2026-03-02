"""
SAWS Time-Series Anomaly Detection

Statistical Process Control (SPC) for vegetation index monitoring.
Implements z-score anomaly detection, change point detection, and
missing data imputation for satellite time series data.

References:
- Montgomery, D. C. (2017). Introduction to Statistical Quality Control.
- Brockwell, P. J., & Davis, R. A. (2016). Introduction to Time Series and Forecasting.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


# ==================== Z-SCORE ANOMALY DETECTION ====================

def detect_zscore_anomalies(
    values: list[float],
    threshold: float = 2.5,
    window_size: int | None = None,
) -> dict[str, Any]:
    """
    Detect anomalies using z-score statistical process control.

    Z-score method identifies values that deviate significantly from
    the historical mean. Uses moving window for baseline calculation.

    Args:
        values: Time series values
        threshold: Z-score threshold for anomaly detection (default 2.5 ≈ 99% confidence)
        window_size: Rolling window size (None = use all data)

    Returns:
        Anomaly detection results with:
        - anomalies: List of (index, value, z_score) tuples
        - anomaly_indices: Indices of detected anomalies
        - anomaly_count: Number of anomalies detected
        - z_scores: Z-scores for all values
        - mean: Mean of baseline period
        - std: Standard deviation of baseline period

    Reference:
        - WMO guidelines for climate data quality control
    """
    if len(values) < 3:
        return {
            "anomalies": [],
            "anomaly_indices": [],
            "anomaly_count": 0,
            "z_scores": [],
            "mean": 0.0,
            "std": 0.0,
        }

    values_array = np.array(values)

    # Calculate baseline statistics
    if window_size is None or window_size >= len(values):
        # Use entire series for baseline
        baseline_mean = np.mean(values_array)
        baseline_std = np.std(values_array, ddof=1)
        z_scores = (values_array - baseline_mean) / baseline_std if baseline_std > 0 else np.zeros_like(values_array)
    else:
        # Use rolling window for baseline
        z_scores = []
        for i in range(len(values)):
            # Get historical window (exclude current)
            start_idx = max(0, i - window_size)
            end_idx = i
            window = values_array[start_idx:end_idx]

            if len(window) > 0:
                baseline_mean = np.mean(window)
                baseline_std = np.std(window, ddof=1)
                if baseline_std > 0:
                    z_score = (values_array[i] - baseline_mean) / baseline_std
                else:
                    z_score = 0.0
            else:
                z_score = 0.0

            z_scores.append(z_score)

        z_scores = np.array(z_scores)
        baseline_mean = np.mean(values_array[:min(window_size, len(values_array))])
        baseline_std = np.std(values_array[:min(window_size, len(values_array))], ddof=1)

    # Detect anomalies
    anomaly_mask = np.abs(z_scores) > threshold
    anomaly_indices = np.where(anomaly_mask)[0].tolist()

    anomalies = []
    for idx in anomaly_indices:
        anomalies.append({
            "index": int(idx),
            "value": float(values_array[idx]),
            "z_score": float(z_scores[idx]),
            "severity": "extreme" if abs(z_scores[idx]) > 3.5 else "moderate",
        })

    return {
        "anomalies": anomalies,
        "anomaly_indices": anomaly_indices,
        "anomaly_count": len(anomalies),
        "z_scores": z_scores.tolist(),
        "mean": float(baseline_mean),
        "std": float(baseline_std),
        "threshold": threshold,
    }


# ==================== CHANGE POINT DETECTION ====================

def detect_change_points(
    values: list[float],
    min_window: int = 5,
    significance: float = 0.05,
) -> dict[str, Any]:
    """
    Detect significant change points in time series.

    Uses two-sample t-test to detect statistically significant shifts
    in the mean of the time series. Useful for detecting:
    - Sudden crop stress events
    - Harvest periods
    - Irrigation effects

    Args:
        values: Time series values
        min_window: Minimum window size for change detection
        significance: Statistical significance level (default 0.05)

    Returns:
        Change points with:
        - change_points: List of (index, p_value, magnitude) tuples
        - change_count: Number of change points detected
        - segments: Description of segments between change points

    Reference:
        - Bai, J., & Perron, P. (2003). Computation and analysis of structural changes.
    """
    if len(values) < min_window * 2:
        return {
            "change_points": [],
            "change_count": 0,
            "segments": [],
        }

    values_array = np.array(values)
    n = len(values_array)

    change_points = []

    # Test each possible change point
    for i in range(min_window, n - min_window):
        before = values_array[:i]
        after = values_array[i:]

        # Two-sample t-test
        try:
            t_stat, p_value = stats.ttest_ind(before, after)

            if p_value < significance:
                # Calculate magnitude of change
                mean_before = np.mean(before)
                mean_after = np.mean(after)
                magnitude = mean_after - mean_before

                change_points.append({
                    "index": i,
                    "date_offset": i,  # For mapping to actual dates
                    "p_value": float(p_value),
                    "t_statistic": float(t_stat),
                    "magnitude": float(magnitude),
                    "mean_before": float(mean_before),
                    "mean_after": float(mean_after),
                    "direction": "increase" if magnitude > 0 else "decrease",
                })
        except Exception as e:
            logger.debug(f"Change point test failed at index {i}: {e}")
            continue

    # Filter overlapping change points (keep most significant)
    if change_points:
        # Sort by p-value (most significant first)
        change_points.sort(key=lambda x: x["p_value"])

        # Remove change points within min_window of each other
        filtered = []
        used_indices = set()

        for cp in change_points:
            idx = cp["index"]
            # Check if this index is too close to an already selected change point
            if not any(abs(idx - used) < min_window for used in used_indices):
                filtered.append(cp)
                used_indices.add(idx)

        change_points = filtered

    # Generate segment descriptions
    segments = []
    if change_points:
        prev_idx = 0
        for cp in change_points:
            segments.append({
                "start": prev_idx,
                "end": cp["index"],
                "mean": float(np.mean(values_array[prev_idx:cp["index"]])),
            })
            prev_idx = cp["index"]

        segments.append({
            "start": prev_idx,
            "end": n,
            "mean": float(np.mean(values_array[prev_idx:])),
        })
    else:
        segments.append({
            "start": 0,
            "end": n,
            "mean": float(np.mean(values_array)),
        })

    return {
        "change_points": change_points,
        "change_count": len(change_points),
        "segments": segments,
    }


# ==================== MISSING DATA IMPUTATION ====================

def impute_missing_values(
    values: list[float],
    dates: list[datetime] | None = None,
    method: str = "linear",
    max_gap_days: int = 16,
) -> dict[str, Any]:
    """
    Impute missing values in time series data.

    Supports multiple imputation methods:
    - linear: Linear interpolation
    - seasonal: Seasonal decomposition + interpolation
    - mean: Historical mean substitution
    - forward: Forward fill

    Args:
        values: Time series with NaN for missing values
        dates: Corresponding dates (optional, for gap calculation)
        method: Imputation method
        max_gap_days: Maximum gap to impute (MODIS 16-day cycle default)

    Returns:
        Imputed data with:
        - values: Imputed values
        - imputed_indices: Indices of imputed values
        - imputed_count: Number of imputed values
        - method_used: Method actually used

    Reference:
        - Little, R. J., & Rubin, D. B. (2019). Statistical Analysis with Missing Data.
    """
    values_array = np.array(values, dtype=float)
    n = len(values_array)

    # Find missing values
    missing_mask = np.isnan(values_array)
    missing_indices = np.where(missing_mask)[0]

    if len(missing_indices) == 0:
        return {
            "values": values_array.tolist(),
            "imputed_indices": [],
            "imputed_count": 0,
            "method_used": method,
        }

    imputed = values_array.copy()

    if method == "linear":
        # Linear interpolation
        for idx in missing_indices:
            # Find nearest non-missing values before and after
            before_idx = idx - 1
            while before_idx >= 0 and np.isnan(values_array[before_idx]):
                before_idx -= 1

            after_idx = idx + 1
            while after_idx < n and np.isnan(values_array[after_idx]):
                after_idx += 1

            if before_idx >= 0 and after_idx < n:
                # Linear interpolation
                x0, x1 = before_idx, after_idx
                y0, y1 = values_array[before_idx], values_array[after_idx]
                imputed[idx] = y0 + (y1 - y0) * (idx - x0) / (x1 - x0)
            elif before_idx >= 0:
                # Forward fill
                imputed[idx] = values_array[before_idx]
            elif after_idx < n:
                # Backward fill
                imputed[idx] = values_array[after_idx]
            else:
                # No valid data, use mean of non-missing
                valid_values = values_array[~missing_mask]
                if len(valid_values) > 0:
                    imputed[idx] = np.mean(valid_values)

    elif method == "mean":
        # Historical mean substitution
        valid_values = values_array[~missing_mask]
        if len(valid_values) > 0:
            mean_value = np.mean(valid_values)
            imputed[missing_mask] = mean_value

    elif method == "forward":
        # Forward fill
        last_valid = 0.0
        for i in range(n):
            if not np.isnan(values_array[i]):
                last_valid = values_array[i]
                imputed[i] = values_array[i]
            else:
                imputed[i] = last_valid

    elif method == "seasonal":
        # Seasonal adjustment + linear interpolation
        # For agricultural data with seasonal patterns
        if dates is not None and len(dates) == n:
            # Calculate day-of-year means for seasonal adjustment
            valid_mask = ~missing_mask
            doy_values = {}

            for i in range(n):
                if valid_mask[i]:
                    doy = dates[i].timetuple().tm_yday
                    if doy not in doy_values:
                        doy_values[doy] = []
                    doy_values[doy].append(values_array[i])

            # Calculate seasonal means
            seasonal_means = {doy: np.mean(vals) for doy, vals in doy_values.items()}

            # Impute using seasonal means + trend
            for idx in missing_indices:
                doy = dates[idx].timetuple().tm_yday

                if doy in seasonal_means:
                    imputed[idx] = seasonal_means[doy]
                else:
                    # Fallback to linear interpolation
                    imputed[idx] = impute_missing_values(
                        values, None, method="linear"
                    )["values"][idx]
        else:
            # Fallback to linear if no dates
            return impute_missing_values(values, None, method="linear")

    return {
        "values": imputed.tolist(),
        "imputed_indices": missing_indices.tolist(),
        "imputed_count": len(missing_indices),
        "method_used": method,
    }


# ==================== TREND ANALYSIS ====================

def calculate_trend(
    values: list[float],
    dates: list[datetime] | None = None,
) -> dict[str, Any]:
    """
    Calculate trend statistics for time series.

    Performs linear regression to determine:
    - Slope (trend magnitude)
    - Correlation coefficient (R²)
    - Significance (p-value)
    - Trend direction

    Args:
        values: Time series values
        dates: Corresponding dates (optional, uses index if None)

    Returns:
        Trend statistics with:
        - slope: Trend magnitude (units per time step)
        - intercept: Y-intercept
        - r_squared: Coefficient of determination
        - p_value: Statistical significance
        - trend_direction: 'increasing', 'decreasing', or 'stable'
        - significance: 'significant', 'not_significant'

    Reference:
        - Mann-Kendall trend test for non-parametric alternative
    """
    values_array = np.array(values)
    n = len(values_array)

    if n < 3:
        return {
            "slope": 0.0,
            "intercept": 0.0,
            "r_squared": 0.0,
            "p_value": 1.0,
            "trend_direction": "stable",
            "significance": "insufficient_data",
        }

    # Create x values (time steps)
    if dates is None:
        x = np.arange(n)
    else:
        # Convert dates to numeric (days since first date)
        base_date = dates[0]
        x = np.array([(d - base_date).days for d in dates])

    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values_array)
    r_squared = r_value ** 2

    # Determine trend direction
    if abs(p_value) > 0.05:
        trend_direction = "stable"
        significance = "not_significant"
    else:
        significance = "significant"
        if slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "p_value": float(p_value),
        "std_error": float(std_err),
        "trend_direction": trend_direction,
        "significance": significance,
    }


# ==================== VEGETATION INDEX SPECIFIC ANALYSIS ====================

def analyze_ndvi_timeseries(
    ndvi_values: list[float],
    dates: list[datetime],
    crop_type: str = "default",
    expected_range: tuple[float, float] = (0.2, 0.8),
) -> dict[str, Any]:
    """
    Comprehensive NDVI time series analysis.

    Combines anomaly detection, trend analysis, and phenology-aware
    interpretation for Saudi agricultural crops.

    Args:
        ndvi_values: NDVI time series
        dates: Corresponding dates
        crop_type: Type of crop for context
        expected_range: Expected NDVI range for the crop

    Returns:
        Comprehensive analysis with:
        - anomalies: Z-score anomaly detection results
        - trend: Trend analysis results
        - change_points: Significant change points
        - health_status: Overall crop health assessment
        - recommendations: Management recommendations
    """
    if len(ndvi_values) != len(dates):
        raise ValueError("NDVI values and dates must have same length")

    # Anomaly detection
    anomalies = detect_zscore_anomalies(ndvi_values, threshold=2.5)

    # Trend analysis
    trend = calculate_trend(ndvi_values, dates)

    # Change point detection
    change_points = detect_change_points(ndvi_values, min_window=5)

    # Current status
    current_ndvi = ndvi_values[-1] if ndvi_values else 0.0

    # Health assessment
    if current_ndvi < expected_range[0]:
        health_status = "poor"
        severity = "critical"
    elif current_ndvi < expected_range[1]:
        health_status = "moderate"
        severity = "warning"
    else:
        health_status = "good"
        severity = "normal"

    # Generate recommendations
    recommendations = []

    if anomalies["anomaly_count"] > 0:
        recommendations.append(f"Detected {anomalies['anomaly_count']} anomalies requiring investigation")

    if trend["trend_direction"] == "decreasing" and trend["significance"] == "significant":
        recommendations.append("Significant declining trend detected - review irrigation and nutrient management")

    if health_status == "poor":
        recommendations.append("Current NDVI below expected range - immediate attention needed")

    if change_points["change_count"] > 0:
        latest_change = change_points["change_points"][0]
        if latest_change["direction"] == "decrease":
            recommendations.append(f"Recent significant decrease detected at index {latest_change['index']}")

    return {
        "anomalies": anomalies,
        "trend": trend,
        "change_points": change_points,
        "current_ndvi": current_ndvi,
        "health_status": health_status,
        "severity": severity,
        "recommendations": recommendations,
        "crop_type": crop_type,
        "analysis_date": datetime.now().isoformat(),
    }


def calculate_moving_statistics(
    values: list[float],
    window: int = 3,
) -> dict[str, Any]:
    """
    Calculate moving window statistics for time series.

    Provides rolling mean, standard deviation, and confidence
    intervals for monitoring vegetation index trends.

    Args:
        values: Time series values
        window: Window size for moving statistics

    Returns:
        Moving statistics with:
        - rolling_mean: Rolling mean
        - rolling_std: Rolling standard deviation
        - upper_bound: Upper confidence bound (mean + 2*std)
        - lower_bound: Lower confidence bound (mean - 2*std)
    """
    values_array = np.array(values)
    n = len(values_array)

    rolling_mean = []
    rolling_std = []
    upper_bound = []
    lower_bound = []

    for i in range(n):
        start = max(0, i - window + 1)
        window_values = values_array[start:i+1]

        mean = np.mean(window_values)
        std = np.std(window_values, ddof=1)

        rolling_mean.append(float(mean))
        rolling_std.append(float(std))
        upper_bound.append(float(mean + 2 * std))
        lower_bound.append(float(mean - 2 * std))

    return {
        "rolling_mean": rolling_mean,
        "rolling_std": rolling_std,
        "upper_bound": upper_bound,
        "lower_bound": lower_bound,
        "window": window,
    }
