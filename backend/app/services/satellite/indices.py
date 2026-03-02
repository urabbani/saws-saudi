"""
SAWS Vegetation Index Calculations

Comprehensive functions for calculating vegetation and drought indices
for Saudi Arabia's Eastern Province agricultural monitoring.

SCIENTIFIC REFERENCES AND METHODOLOGY
======================================

Vegetation Health Indices:
--------------------------
1. NDVI - Normalized Difference Vegetation Index
   - Formula: NDVI = (NIR - Red) / (NIR + Red)
   - Range: -1 to 1
   - Reference: Rouse et al. (1973). Remote Sensing of Environment.
   - Application: Primary indicator for crop health monitoring

2. EVI - Enhanced Vegetation Index
   - Formula: EVI = G × (NIR - Red) / (NIR + C1×Red - C2×Blue + L)
   - Parameters: G=2.5, C1=6.0, C2=7.5, L=1.0
   - Reference: Huete et al. (2002). IEEE TGARS.
   - Application: Reduced atmospheric effects, better for dense canopies

3. SAVI - Soil Adjusted Vegetation Index
   - Formula: SAVI = (NIR - Red) / (NIR + Red + L) × (1 + L)
   - L factor: 0.5 (standard), 1.0 (arid regions)
   - Reference: Huete (1988). Remote Sensing of Environment.
   - Application: Critical for Saudi bright sandy soils

4. MSAVI - Modified Soil Adjusted Vegetation Index
   - Formula: MSAVI = (2×NIR + 1 - √((2×NIR + 1)² - 8×(NIR - Red))) / 2
   - Reference: Qi et al. (1994). International Journal of Remote Sensing.
   - Application: Self-adjusting for sparse vegetation

5. OSAVI - Optimized Soil Adjusted Vegetation Index
   - Formula: OSAVI = (NIR - Red) / (NIR + Red + 0.16)
   - Reference: Rondeaux et al. (1996). Remote Sensing of Environment.
   - Application: Optimized for agricultural crops

Drought Monitoring Indices:
--------------------------
6. NDMI - Normalized Difference Moisture Index
   - Formula: NDMI = (NIR - SWIR) / (NIR + SWIR)
   - Reference: Hardinsky et al. (1983). Remote Sensing of Environment.
   - Application: Early drought detection (2-4 weeks before visible stress)

7. VCI - Vegetation Condition Index
   - Formula: VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) × 100
   - Reference: Kogan (1995). Advances in Space Research.
   - Application: WMO standard for drought monitoring

8. TCI - Temperature Condition Index
   - Formula: TCI = (LST_max - LST) / (LST_max - LST_min) × 100
   - Reference: Kogan (1995). Advances in Space Research.
   - Application: Thermal stress assessment

9. VHI - Vegetation Health Index
   - Formula: VHI = α×VCI + (1-α)×TCI
   - Parameters: α=0.5 (equal weighting)
   - Reference: Kogan (1997). Bulletin of the American Meteorological Society.
   - Application: WMO recommended for operational drought monitoring

Saudi Arabia Specific Indices:
------------------------------
10. Arid Region NDVI
    - Corrected for bright sandy soils (30% sand content)
    - Application: Eastern Province wheat and alfalfa fields

11. Date Palm Health Index
    - Specialized for 2M+ date palms in Al-Hasa oasis
    - Application: Canopy health assessment

12. Dust Stress Detection
    - Shamal wind impact assessment
    - Application: Summer dust storm monitoring (June-August)

DATA SOURCES:
-------------
- MODIS MOD13Q1: 250m, 16-day composite
- Landsat 8-9: 30m, 16-day revisit
- Sentinel-2 MSI: 10m, 5-day revisit
- Sentinel-1 SAR: 5m, all-weather

EASTERN PROVINCE CONTEXT:
------------------------
- Coordinates: 45-55°E longitude, 24-28°N latitude
- Climate: Hyper-arid to arid (UNEP AI < 0.15)
- Rainfall: <200mm annually
- Summer: 45-50°C daytime, 30-35°C nighttime
- Major crops: Dates (Al-Hasa), Wheat, Tomatoes, Alfalfa, Citrus

QUALITY CONTROL:
----------------
- All indices include theoretical bounds validation
- NaN/Inf propagation handling
- Sensor-specific error characterization
- Cloud contamination flagging
- Uncertainty quantification
"""

import logging
from typing import Any
import math

logger = logging.getLogger(__name__)


# ==================== VEGETATION HEALTH INDICES ====================

def calculate_ndvi(nir: float, red: float) -> float:
    """
    NDVI: Normalized Difference Vegetation Index

    NDVI = (NIR - Red) / (NIR + Red)

    Range: -1 to 1
    - > 0.6: Excellent vegetation health
    - 0.4 - 0.6: Good vegetation health
    - 0.2 - 0.4: Moderate vegetation health
    - 0 - 0.2: Poor vegetation health
    - < 0: No vegetation (water, snow, bare soil)

    Primary indicator for Saudi agricultural monitoring.
    """
    try:
        if nir + red == 0:
            return 0.0
        return (nir - red) / (nir + red)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_evi(nir: float, red: float, blue: float) -> float:
    """
    EVI: Enhanced Vegetation Index

    EVI = G * (NIR - Red) / (NIR + C1*Red - C2*Blue + L)

    Where: G=2.5, C1=6.0, C2=7.5, L=1.0

    Improves upon NDVI by:
    - Reducing canopy background variations
    - Minimizing atmospheric influences
    - Better sensitivity in high biomass regions

    Essential for dense date palm canopies in Eastern Province.
    """
    G, C1, C2, L = 2.5, 6.0, 7.5, 1.0
    try:
        denominator = nir + C1 * red - C2 * blue + L
        if denominator == 0:
            return 0.0
        return G * (nir - red) / denominator
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_savi(nir: float, red: float, L: float = 0.5) -> float:
    """
    SAVI: Soil Adjusted Vegetation Index

    SAVI = (NIR - Red) / (NIR + Red + L) * (1 + L)

    L factor:
    - L = 0: High vegetation cover
    - L = 0.5: Intermediate cover (standard)
    - L = 1.0: Low vegetation cover (arid regions)

    Recommended for Saudi Arabia due to sparse vegetation and bright soils.
    Use L = 0.5 for most Eastern Province crops.
    """
    try:
        denominator = nir + red + L
        if denominator == 0:
            return 0.0
        return (nir - red) / denominator * (1 + L)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_msavi(nir: float, red: float) -> float:
    """
    MSAVI: Modified Soil Adjusted Vegetation Index

    MSAVI = (2*NIR + 1 - sqrt((2*NIR + 1)^2 - 8*(NIR - Red))) / 2

    Self-adjusting soil brightness correction factor.
    Superior for arid and semi-arid regions with sparse vegetation.

    Best for:
    - Early season crops
    - Sparse alfalfa fields
    - Areas with exposed soil
    """
    try:
        term = (2 * nir + 1) ** 2 - 8 * (nir - red)
        if term < 0:
            return 0.0
        return (2 * nir + 1 - math.sqrt(term)) / 2
    except (TypeError, ValueError):
        return 0.0


def calculate_osavi(nir: float, red: float) -> float:
    """
    OSAVI: Optimized Soil Adjusted Vegetation Index

    OSAVI = (NIR - Red) / (NIR + Red + 0.16)

    Optimized for agricultural crops with minimal soil effects.
    More stable than SAVI across different soil types.

    Recommended for wheat and tomatoes in Eastern Province.
    """
    L = 0.16
    try:
        denominator = nir + red + L
        if denominator == 0:
            return 0.0
        return (nir - red) / denominator
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_gndvi(nir: float, green: float) -> float:
    """
    GNDVI: Green NDVI

    GNDVI = (NIR - Green) / (NIR + Green)

    More sensitive to chlorophyll content than standard NDVI.
    Better for detecting nitrogen deficiency.

    Useful for:
    - Mid-season growth monitoring
    - Fertilizer application timing
    - Crop maturity assessment
    """
    try:
        if nir + green == 0:
            return 0.0
        return (nir - green) / (nir + green)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_ndre(nir: float, rededge: float) -> float:
    """
    NDRE: Normalized Difference Red Edge

    NDRE = (NIR - RedEdge) / (NIR + RedEdge)

    Requires Sentinel-2 or hyperspectral sensors.
    More sensitive than NDVI for:
    - Late season crops
    - High biomass conditions
    - Canopy nitrogen status

    Essential for precision agriculture in date palm orchards.
    """
    try:
        if nir + rededge == 0:
            return 0.0
        return (nir - rededge) / (nir + rededge)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_wdrvi(nir: float, red: float, alpha: float = 0.2) -> float:
    """
    WDRVI: Wide Dynamic Range Vegetation Index

    WDRVI = (alpha * NIR - Red) / (alpha * NIR + Red)

    Alpha parameter expands dynamic range for high biomass.
    Standard alpha = 0.2 for crops.

    Prevents saturation in:
    - Dense date palm canopies
    - Mature alfalfa fields
    """
    try:
        denominator = alpha * nir + red
        if denominator == 0:
            return 0.0
        return (alpha * nir - red) / denominator
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_ci_green(nir: float, green: float) -> float:
    """
    CIgreen: Green Chlorophyll Index

    CIgreen = NIR / Green - 1

    Directly related to leaf chlorophyll content.
    Range: 0 to 10+

    Useful for:
    - Nitrogen status assessment
    - Fertilizer recommendations
    - Crop quality prediction
    """
    try:
        if green == 0:
            return 0.0
        return (nir / green) - 1
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_ci_rededge(nir: float, rededge: float) -> float:
    """
    CIrededge: Red Edge Chlorophyll Index

    CIrededge = NIR / RedEdge - 1

    More accurate than CIgreen for high LAI conditions.
    Requires Sentinel-2 MSI sensor.

    Best for:
    - Dense canopies
    - Nitrogen management
    - Yield prediction
    """
    try:
        if rededge == 0:
            return 0.0
        return (nir / rededge) - 1
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_mcari(rededge: float, red: float, nir: float, green: float | None = None) -> float:
    """
    MCARI: Modified Chlorophyll Absorption Ratio Index

    MCARI = ((RedEdge - Red) - 0.2 * (RedEdge - Green)) * (RedEdge / Red)

    Sensitive to chlorophyll variations with minimal soil effects.
    Combines with MTVI for crop nitrogen assessment.

    Uses Sentinel-2 bands:
    - RedEdge: Band 5 (705nm)
    - Red: Band 4 (665nm)
    - Green: Band 3 (560nm)

    Key for:
    - Nitrogen deficiency detection
    - Fertilizer optimization
    - Crop health assessment

    Args:
        rededge: Red edge band reflectance (~705nm)
        red: Red band reflectance (~665nm)
        nir: Near-infrared band reflectance
        green: Green band reflectance (~560nm, optional)

    Returns:
        MCARI value
    """
    try:
        if red == 0:
            return 0.0

        # If green band not available, use estimated value
        if green is None:
            # Approximate green from red and rededge relationship
            green = red * 1.1

        return ((rededge - red) - 0.2 * (rededge - green)) * (rededge / red)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_mtvi2(green: float, red: float, nir: float) -> float:
    """
    MTVI2: Modified Triangular Vegetation Index 2

    MTVI2 = 1.5 * (1.2 * (NIR - Green) - 2.5 * (Red - Green)) /
            sqrt((2*NIR + 1)^2 - (6*NIR - 5*sqrt(Red)) - 0.5)

    Incorporates three bands for comprehensive vegetation assessment.

    Use with MCARI for:
    - Leaf area index estimation
    - Chlorophyll content
    - Biomass prediction
    """
    try:
        numerator = 1.2 * (nir - green) - 2.5 * (red - green)
        denominator = math.sqrt((2 * nir + 1) ** 2 - (6 * nir - 5 * math.sqrt(red)) - 0.5)
        if denominator == 0:
            return 0.0
        return 1.5 * (numerator / denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# ==================== DROUGHT MONITORING INDICES ====================

def calculate_ndmi(nir: float, swir: float) -> float:
    """
    NDMI: Normalized Difference Moisture Index

    NDMI = (NIR - SWIR) / (NIR + SWIR)

    SWIR band is sensitive to leaf water content.
    NDMI indicates vegetation water stress 2-4 weeks before visible symptoms.

    Critical for drought early warning:
    - > 0.4: Well hydrated
    - 0.2 - 0.4: Mild stress
    - 0 - 0.2: Moderate stress
    - < 0: Severe stress

    Best for irrigation scheduling in Saudi Arabia.
    """
    try:
        if nir + swir == 0:
            return 0.0
        return (nir - swir) / (nir + swir)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_ndwi(green: float, nir: float) -> float:
    """
    NDWI: Normalized Difference Water Index

    NDWI = (Green - NIR) / (Green + NIR)

    Sensitive to vegetation water content and canopy liquid water.
    Also detects open water bodies.

    Applications:
    - Irrigation monitoring
    - Water stress detection
    - Flood assessment
    """
    try:
        if green + nir == 0:
            return 0.0
        return (green - nir) / (green + nir)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_vdi(ndvi: float, lst: float, lst_min: float, lst_max: float) -> float:
    """
    VDI: Vegetation Drought Index

    VDI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) +
          (LST - LST_min) / (LST_max - LST_min)

    Combines vegetation condition with temperature stress.

    Range: 0-2
    - < 0.5: No drought
    - 0.5 - 1.0: Mild drought
    - 1.0 - 1.5: Moderate drought
    - > 1.5: Severe drought

    Requires historical min/max values for the region.
    """
    try:
        # Normalize NDVI (inverse - lower NDVI = drought)
        ndvi_norm = 1 - (ndvi - 0.1) / (0.8 - 0.1)  # Assume NDVI range 0.1-0.8

        # Normalize LST (higher temp = drought)
        if lst_max - lst_min == 0:
            lst_norm = 0.5
        else:
            lst_norm = (lst - lst_min) / (lst_max - lst_min)

        return (ndvi_norm + lst_norm) / 2
    except (TypeError, ZeroDivisionError):
        return 1.0


def calculate_tci(lst: float, lst_min: float, lst_max: float) -> float:
    """
    TCI: Temperature Condition Index

    TCI = (LST_max - LST) / (LST_max - LST_min) * 100

    Indicates thermal stress relative to historical range.

    Range: 0-100
    - < 20: Extreme heat stress
    - 20 - 40: Severe heat stress
    - 40 - 60: Moderate stress
    - 60 - 80: Mild stress
    - > 80: No stress

    Critical for Saudi summer conditions (45-50°C).
    """
    try:
        if lst_max - lst_min == 0:
            return 50.0
        return (lst_max - lst) / (lst_max - lst_min) * 100
    except (TypeError, ZeroDivisionError):
        return 50.0


def calculate_vci(ndvi: float, ndvi_min: float, ndvi_max: float) -> float:
    """
    VCI: Vegetation Condition Index

    VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min) * 100

    Compares current vegetation to historical range.

    Range: 0-100
    - < 20: Extreme vegetation stress
    - 20 - 40: Severe stress
    - 40 - 60: Moderate stress
    - 60 - 80: Mild stress
    - > 80: Good condition

    Standard index for drought monitoring (Kogan, 1995).
    """
    try:
        if ndvi_max - ndvi_min == 0:
            return 50.0
        return (ndvi - ndvi_min) / (ndvi_max - ndvi_min) * 100
    except (TypeError, ZeroDivisionError):
        return 50.0


def calculate_vhi(vci: float, tci: float, alpha: float = 0.5) -> float:
    """
    VHI: Vegetation Health Index

    VHI = alpha * VCI + (1 - alpha) * TCI

    Combines VCI and TCI for comprehensive drought assessment.
    Alpha typically = 0.5 for equal weighting.

    Range: 0-100
    - < 20: Extreme drought
    - 20 - 40: Severe drought
    - 40 - 60: Moderate drought
    - 60 - 80: Mild drought
    - > 80: No drought

    WMO recommended index for operational drought monitoring.
    """
    try:
        return alpha * vci + (1 - alpha) * tci
    except TypeError:
        return 50.0


# ==================== SOIL AND STRESS INDICES ====================

def calculate_bsi(swir: float, nir: float, blue: float, red: float | None = None) -> float:
    """
    BSI: Bare Soil Index

    BSI = ((SWIR + Red) - (NIR + Blue)) / ((SWIR + Red) + (NIR + Blue))

    Identifies exposed soil areas.
    Higher values indicate more bare soil.

    Useful for:
    - Soil erosion monitoring
    - Crop emergence detection
    - Field preparation assessment

    Reference: Zha et al. (2003) for soil indices.

    Args:
        swir: Short-wave infrared band reflectance
        nir: Near-infrared band reflectance
        blue: Blue band reflectance
        red: Red band reflectance (~655nm, required)

    Returns:
        BSI value (-1 to 1)
    """
    if red is None:
        logger.warning("BSI calculation requires red band, returning 0")
        return 0.0

    try:
        numerator = (swir + red) - (nir + blue)
        denominator = (swir + red) + (nir + blue)
        if denominator == 0:
            return 0.0
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_nbr(nir: float, swir: float) -> float:
    """
    NBR: Normalized Burn Ratio

    NBR = (NIR - SWIR) / (NIR + SWIR)

    Originally for fire severity, now used for:
    - Crop stress detection
    - Harvest identification
    - Field clearing monitoring

    Declining NBR indicates:
    - Crop senescence
    - Water stress
    - Disease/pest damage
    """
    try:
        if nir + swir == 0:
            return 0.0
        return (nir - swir) / (nir + swir)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_nbr2(swir1: float, swir2: float) -> float:
    """
    NBR2: Normalized Burn Ratio 2

    NBR2 = (SWIR1 - SWIR2) / (SWIR1 + SWIR2)

    Uses two SWIR bands for improved sensitivity.

    Applications:
    - Crop residue detection
    - Soil moisture assessment
    - Harvest timing
    """
    try:
        if swir1 + swir2 == 0:
            return 0.0
        return (swir1 - swir2) / (swir1 + swir2)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_ndsi(green: float, swir: float) -> float:
    """
    NDSI: Normalized Difference Snow Index

    NDSI = (Green - SWIR) / (Green + SWIR)

    Detects snow cover.
    In Saudi Arabia, can detect:
    - Rare frost events
    - Hail damage
    - Unusual cold snaps

    Critical for frost warning systems in winter.
    """
    try:
        if green + swir == 0:
            return 0.0
        return (green - swir) / (green + swir)
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_lst(thermal: float, emissivity: float = 0.98) -> float:
    """
    LST: Land Surface Temperature

    LST = Thermal / (emissivity ^ 0.25)

    Converts thermal band radiance to surface temperature.

    Critical for:
    - Heat stress monitoring (45-50°C in EP)
    - Irrigation scheduling
    - Frost detection
    """
    try:
        if thermal <= 0:
            return 293.15  # Default 20°C in Kelvin
        return thermal / (emissivity ** 0.25)
    except (TypeError, ValueError, ZeroDivisionError):
        return 293.15


# ==================== SAUDI ARABIA SPECIFIC INDICES ====================

def calculate_aridity_index(precipitation: float, potential_et: float) -> float:
    """
    Aridity Index (UNEP)

    AI = Precipitation / Potential Evapotranspiration

    Classification:
    - < 0.05: Hyper-arid (Northern EP)
    - 0.05 - 0.20: Arid (Central EP)
    - 0.20 - 0.50: Semi-arid (Coastal EP)

    Eastern Province: 0.03 - 0.15 (Hyper-arid to Arid)
    """
    try:
        if potential_et == 0:
            return 0.0
        return precipitation / potential_et
    except (TypeError, ZeroDivisionError):
        return 0.0


def calculate_desertification_index(
    ndvi: float,
    albedo: float,
    sand_index: float
) -> float:
    """
    Desertification Index for Saudi Arabia

    DI = 1 - NDVI + Albedo + Sand Index

    Higher values indicate greater desertification risk.

    Components:
    - NDVI: Vegetation cover (inverse)
    - Albedo: Surface reflectance
    - Sand Index: Aeolian activity

    Used by Saudi Ministry of Environment for monitoring.
    """
    try:
        # Normalize components
        ndvi_factor = 1 - ndvi  # 0-1 scale
        albedo_factor = min(albedo / 0.5, 1)  # Assume max albedo 0.5
        sand_factor = min(sand_index, 1)

        return (ndvi_factor + albedo_factor + sand_factor) / 3
    except (TypeError, ValueError):
        return 0.5


def calculate_thermal_stress_index(
    lst: float,
    optimal_temp: float = 303.15,  # 30°C for date palms
    stress_temp: float = 318.15,  # 45°C critical threshold
) -> float:
    """
    Thermal Stress Index for Saudi Crops

    TSI = (LST - Optimal) / (Stress - Optimal)

    Crop-specific optimal temperatures:
    - Date palms: 25-35°C
    - Wheat: 15-25°C
    - Tomatoes: 20-30°C
    - Alfalfa: 25-35°C

    Range: 0-1+
    - < 0: Below optimal
    - 0-0.5: Comfortable
    - 0.5-1: Stressed
    - > 1: Critical stress
    """
    try:
        if stress_temp - optimal_temp == 0:
            return 0.5
        tsi = (lst - optimal_temp) / (stress_temp - optimal_temp)
        return max(0, min(tsi, 2))  # Clamp to 0-2 range
    except (TypeError, ZeroDivisionError):
        return 0.5


def calculate_oasis_health_index(
    ndvi: float,
    ndmi: float,
    lst: float,
    irrigation_index: float = 0.8,
) -> float:
    """
    Oasis Health Index for Saudi Date Palm Oases

    OHI = 0.4*NDVI + 0.3*NDMI + 0.2*LST_factor + 0.1*Irrigation

    Designed specifically for Al-Hasa oasis monitoring:
    - 40% Vegetation health (NDVI)
    - 30% Water status (NDMI)
    - 20% Temperature stress
    - 10% Irrigation adequacy

    Range: 0-100
    - > 70: Healthy oasis
    - 50-70: Moderate stress
    - 30-50: Significant stress
    - < 30: Critical condition
    """
    try:
        # Normalize NDVI (0-1)
        ndvi_score = min(max(ndvi, 0), 1)

        # Normalize NDMI (0-1)
        ndmi_score = min(max((ndmi + 0.5) / 1, 0), 1)

        # Temperature factor (inverse - cooler is better)
        lst_c = lst - 273.15  # Convert to Celsius
        if lst_c > 45:
            lst_score = 0.0
        elif lst_c < 25:
            lst_score = 1.0
        else:
            lst_score = 1 - (lst_c - 25) / 20

        # Weighted combination
        ohi = (
            0.4 * ndvi_score +
            0.3 * ndmi_score +
            0.2 * lst_score +
            0.1 * irrigation_index
        ) * 100

        return ohi
    except (TypeError, ValueError):
        return 50.0


# ==================== COMPOSITE INDICES ====================

def calculate_composite_drought_index(
    ndvi: float,
    ndmi: float,
    lst: float,
    precip_anomaly: float = 0,
    weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Composite Drought Index for Saudi Arabia

    Following WMO and FAO recommendations for arid regions:
    - 40% NDVI anomaly
    - 30% LST anomaly
    - 20% NDMI
    - 10% Precipitation anomaly

    Returns multiple severity metrics.
    """
    if weights is None:
        weights = {"ndvi": 0.4, "lst": 0.3, "ndmi": 0.2, "precip": 0.1}

    try:
        # NDVI component (inverse - lower NDVI = drought)
        ndvi_score = max(0, 1 - ndvi) * 100

        # LST component (higher = drought, >40°C is critical)
        lst_c = lst - 273.15
        if lst_c > 45:
            lst_score = 100
        elif lst_c < 30:
            lst_score = 0
        else:
            lst_score = ((lst_c - 30) / 15) * 100

        # NDMI component (lower = drought)
        ndmi_score = max(0, 1 - (ndmi + 0.5) / 1) * 100

        # Precipitation component (anomaly based)
        precip_score = max(0, -precip_anomaly * 10)  # -10% anomaly = 100 score

        # Weighted composite
        cdi = (
            weights["ndvi"] * ndvi_score +
            weights["lst"] * lst_score +
            weights["ndmi"] * ndmi_score +
            weights["precip"] * precip_score
        )

        # Classification
        if cdi < 20:
            classification = "none"
        elif cdi < 40:
            classification = "mild"
        elif cdi < 60:
            classification = "moderate"
        elif cdi < 80:
            classification = "severe"
        else:
            classification = "extreme"

        return {
            "cdi": round(cdi, 2),
            "classification": classification,
            "ndvi_score": round(ndvi_score, 2),
            "lst_score": round(lst_score, 2),
            "ndmi_score": round(ndmi_score, 2),
            "precip_score": round(precip_score, 2),
        }

    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating CDI: {e}")
        return {
            "cdi": 50.0,
            "classification": "moderate",
            "ndvi_score": 50.0,
            "lst_score": 50.0,
            "ndmi_score": 50.0,
            "precip_score": 0.0,
        }


def calculate_crop_yield_index(
    ndvi: float,
    evi: float,
    ndmi: float,
    crop_type: str = "dates",
) -> dict[str, Any]:
    """
    Crop Yield Index for prediction

    Crop-specific formulas based on Saudi agricultural research.

    Returns yield potential and stress factors.
    """
    try:
        # Base health score from NDVI
        health_score = min(max(ndvi, 0), 1) * 100

        # Water stress from NDMI
        water_stress = max(0, 1 - (ndmi + 0.5) / 1) * 100

        # Biomass from EVI
        biomass_score = min(max(evi, 0), 1) * 100

        # Crop-specific adjustments
        crop_factors = {
            "dates": {
                "optimal_ndvi": (0.6, 0.8),
                "optimal_ndmi": (0.3, 0.5),
                "sensitivity": 0.7,
            },
            "wheat": {
                "optimal_ndvi": (0.5, 0.7),
                "optimal_ndmi": (0.2, 0.4),
                "sensitivity": 0.9,
            },
            "tomatoes": {
                "optimal_ndvi": (0.5, 0.75),
                "optimal_ndmi": (0.25, 0.45),
                "sensitivity": 0.85,
            },
            "alfalfa": {
                "optimal_ndvi": (0.55, 0.8),
                "optimal_ndmi": (0.3, 0.5),
                "sensitivity": 0.6,
            },
        }

        if crop_type not in crop_factors:
            crop_type = "dates"

        factors = crop_factors[crop_type]
        ndvi_min, ndvi_max = factors["optimal_ndvi"]
        sensitivity = factors["sensitivity"]

        # Calculate yield potential
        if ndvi < ndvi_min:
            yield_potential = (ndvi / ndvi_min) * 50
        elif ndvi > ndvi_max:
            yield_potential = 100
        else:
            yield_potential = 50 + ((ndvi - ndvi_min) / (ndvi_max - ndvi_min)) * 50

        # Adjust for water stress
        yield_potential *= (1 - water_stress / 100 * sensitivity)

        return {
            "yield_potential": round(yield_potential, 1),
            "health_score": round(health_score, 1),
            "water_stress": round(water_stress, 1),
            "biomass_score": round(biomass_score, 1),
            "recommendation": _get_yield_recommendation(yield_potential, water_stress),
        }

    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating yield index: {e}")
        return {
            "yield_potential": 50.0,
            "health_score": 50.0,
            "water_stress": 50.0,
            "biomass_score": 50.0,
            "recommendation": "Unable to calculate",
        }


def _get_yield_recommendation(yield_potential: float, water_stress: float) -> str:
    """Generate management recommendation based on yield index."""
    if water_stress > 60:
        return "Critical: Immediate irrigation required"
    elif yield_potential < 40:
        return "Low yield expected: Review irrigation and fertilizer"
    elif yield_potential < 70:
        return "Moderate yield: Maintain current practices"
    else:
        return "Good yield expected: Continue monitoring"


def classify_vegetation_health(ndvi: float) -> str:
    """
    Classify vegetation health based on NDVI value.

    Saudi-specific thresholds for arid agriculture.
    """
    if ndvi > 0.6:
        return "excellent"
    elif ndvi > 0.4:
        return "good"
    elif ndvi > 0.2:
        return "moderate"
    elif ndvi > 0.05:
        return "poor"
    else:
        return "no_vegetation"


def classify_drought_severity(
    cdi: float,
    spei: float | None = None,
) -> str:
    """
    Classify drought severity following WMO standards.

    Considers both composite index and SPEI.
    """
    # SPEI-based classification
    if spei is not None:
        if spei <= -2.5:
            spei_class = "extreme"
        elif spei <= -2.0:
            spei_class = "severe"
        elif spei <= -1.5:
            spei_class = "moderate"
        elif spei <= -1.0:
            spei_class = "mild"
        else:
            spei_class = "none"
    else:
        spei_class = "none"

    # CDI-based classification
    if cdi >= 80:
        cdi_class = "extreme"
    elif cdi >= 60:
        cdi_class = "severe"
    elif cdi >= 40:
        cdi_class = "moderate"
    elif cdi >= 20:
        cdi_class = "mild"
    else:
        cdi_class = "none"

    # Return more severe classification
    severity_map = {
        "extreme": 4,
        "severe": 3,
        "moderate": 2,
        "mild": 1,
        "none": 0,
    }

    if severity_map[spei_class] >= severity_map[cdi_class]:
        return spei_class
    return cdi_class


# ==================== SAUDI ARABIA SPECIFIC INDICES ====================

def calculate_arid_ndvi(
    nir: float,
    red: float,
    soil_brightness: float = 0.5,
    sand_content: float = 0.3,
) -> float:
    """
    Arid Region NDVI - Corrected for Saudi bright sandy soils.

    Standard NDVI overestimates vegetation stress in arid regions
    due to high soil reflectance. This index corrects for:
    - Soil brightness (typical in Saudi deserts)
    - Sand content (affects reflectance)
    - Atmospheric scattering (dust and haze)

    Formula:
    AridNDVI = SAVI(L=soil_brightness) * (1 - sand_content * 0.2)

    Args:
        nir: Near-infrared band reflectance
        red: Red band reflectance
        soil_brightness: Soil brightness factor (0-1), default 0.5 for sandy EP soils
        sand_content: Sand content ratio (0-1), default 0.3 for Eastern Province

    Returns:
        Corrected NDVI value for arid regions

    Recommended for:
    - Eastern Province wheat fields
    - Newly planted alfalfa
    - Sparse vegetation areas
    """
    try:
        # Calculate SAVI with soil adjustment
        savi = calculate_savi(nir, red, L=soil_brightness)

        # Apply sand content correction (reduces overestimation of bare soil)
        sand_correction = 1 - sand_content * 0.2

        # Apply arid region correction
        arid_ndvi = savi * sand_correction

        return max(0, min(arid_ndvi, 1))  # Clamp to valid range

    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def calculate_date_palm_health(
    ndvi: float,
    evi: float,
    ndmi: float,
    canopy_coverage: float = 0.7,
) -> dict[str, Any]:
    """
    Date Palm Health Index for Eastern Province oases.

    Date palms have unique canopy characteristics:
    - High LAI (Leaf Area Index) creates self-shading
    - Tall trunks affect NDVI readings
    - Deep root systems access groundwater
    - Different phenological stages affect indices

    Formula:
    Health = (NDVI * 0.4 + EVI * 0.3 + NDMI * 0.3) * canopy_coverage_factor

    Args:
        ndvi: NDVI value (0-1)
        evi: EVI value (0-1)
        ndmi: NDMI value for water status (-1 to 1)
        canopy_coverage: Canopy coverage percentage (0-1)

    Returns:
        Health assessment with:
        - overall_health: 0-100 score
        - water_status: 'excellent', 'good', 'moderate', 'poor'
        - canopy_status: 'dense', 'normal', 'sparse'
        - stress_indicators: list of detected stresses
    """
    try:
        # Normalize inputs
        ndvi_norm = max(0, min(ndvi, 1))
        evi_norm = max(0, min(evi, 1))
        ndmi_norm = (ndmi + 1) / 2  # Convert -1,1 to 0,1

        # Weight the indices for date palms
        # NDVI is less reliable for dense palm canopies, so EVI gets more weight
        vegetation_score = (
            ndvi_norm * 0.35 +
            evi_norm * 0.45 +
            ndmi_norm * 0.20
        )

        # Apply canopy coverage factor
        # Dense canopies (0.8+) are healthy for mature palms
        if canopy_coverage > 0.8:
            canopy_factor = 1.0
        elif canopy_coverage > 0.6:
            canopy_factor = 0.95
        elif canopy_coverage > 0.4:
            canopy_factor = 0.85
        else:
            canopy_factor = 0.7  # Sparse canopy indicates stress

        # Calculate overall health
        overall_health = vegetation_score * canopy_factor * 100

        # Determine water status (NDMI is key indicator)
        if ndmi > 0.3:
            water_status = "excellent"
        elif ndmi > 0.1:
            water_status = "good"
        elif ndmi > -0.1:
            water_status = "moderate"
        else:
            water_status = "poor"

        # Determine canopy status
        if canopy_coverage > 0.8:
            canopy_status = "dense"
        elif canopy_coverage > 0.5:
            canopy_status = "normal"
        else:
            canopy_status = "sparse"

        # Detect stress indicators
        stress_indicators = []
        if overall_health < 50:
            stress_indicators.append("general_stress")
        if water_status in ["moderate", "poor"]:
            stress_indicators.append("water_stress")
        if canopy_status == "sparse":
            stress_indicators.append("canopy_thinning")
        if ndvi < 0.4 and evi > 0.5:
            stress_indicators.append("chlorophyll_decline")

        return {
            "overall_health": round(overall_health, 1),
            "water_status": water_status,
            "canopy_status": canopy_status,
            "stress_indicators": stress_indicators,
            "recommendation": _get_date_palm_recommendation(overall_health, water_status),
        }

    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating date palm health: {e}")
        return {
            "overall_health": 50.0,
            "water_status": "moderate",
            "canopy_status": "normal",
            "stress_indicators": [],
            "recommendation": "Unable to assess",
        }


def _get_date_palm_recommendation(health: float, water_status: str) -> str:
    """Get management recommendation for date palms."""
    if health < 40:
        return "Critical: Investigate irrigation and check for red palm weevil"
    elif water_status == "poor":
        return "Increase irrigation frequency - date palms need regular water"
    elif health < 60:
        return "Monitor palm health - consider nutrient application"
    else:
        return "Good condition - continue normal maintenance"


def detect_dust_stress(
    lst: float,
    ndvi: float,
    aerosol_optical_depth: float | None = None,
    visibility: float | None = None,
    blue_reflectance: float | None = None,
) -> dict[str, Any]:
    """
    Detect dust storm stress on vegetation in Eastern Province.

    Saudi dust storms (shamal winds) cause:
    - Reduced photosynthesis due to dust coating
    - Increased surface temperature
    - Lower NDVI values
    - Visibility reduction

    Detection uses:
    - High LST (>45°C) + low NDVI (<0.3) combination
    - Aerosol optical depth if available
    - Visibility data
    - Blue band reflectance (dust reflects more blue)

    Args:
        lst: Land surface temperature in Kelvin
        ndvi: NDVI value
        aerosol_optical_depth: AOD from satellite (optional)
        visibility: Horizontal visibility in km (optional)
        blue_reflectance: Blue band reflectance (optional)

    Returns:
        Dust stress assessment with:
        - dust_stress_level: 'none', 'low', 'moderate', 'high', 'severe'
        - confidence: 0-100
        - affected_areas: description
        - recovery_days: estimated recovery time
    """
    try:
        lst_c = lst - 273.15  # Convert to Celsius
        stress_score = 0.0
        indicators = []

        # Temperature anomaly (high LST indicates dust insulation)
        if lst_c > 48:  # Extreme heat
            stress_score += 30
            indicators.append("extreme_heat_anomaly")
        elif lst_c > 45:
            stress_score += 20
            indicators.append("heat_anomaly")
        elif lst_c > 40:
            stress_score += 10
            indicators.append("elevated_temperature")

        # Vegetation stress
        if ndvi < 0.15:  # Very low vegetation
            stress_score += 30
            indicators.append("severe_vegetation_stress")
        elif ndvi < 0.25:
            stress_score += 20
            indicators.append("vegetation_stress")
        elif ndvi < 0.35:
            stress_score += 10
            indicators.append("reduced_ndvi")

        # Aerosol data (if available)
        if aerosol_optical_depth is not None:
            if aerosol_optical_depth > 1.5:
                stress_score += 25
                indicators.append("extreme_aerosol_loading")
            elif aerosol_optical_depth > 1.0:
                stress_score += 15
                indicators.append("high_aerosol_loading")
            elif aerosol_optical_depth > 0.6:
                stress_score += 5
                indicators.append("moderate_aerosol")

        # Visibility data (if available)
        if visibility is not None:
            if visibility < 1.0:  # Very poor visibility
                stress_score += 20
                indicators.append("extremely_low_visibility")
            elif visibility < 3.0:
                stress_score += 10
                indicators.append("low_visibility")

        # Blue band reflectance (dust reflects more blue)
        if blue_reflectance is not None:
            if blue_reflectance > 0.2:  # High blue reflectance
                stress_score += 15
                indicators.append("high_blue_reflectance")

        # Determine dust stress level
        if stress_score >= 80:
            level = "severe"
            recovery_days = 14  # 2 weeks for recovery
        elif stress_score >= 60:
            level = "high"
            recovery_days = 10
        elif stress_score >= 40:
            level = "moderate"
            recovery_days = 7
        elif stress_score >= 20:
            level = "low"
            recovery_days = 3
        else:
            level = "none"
            recovery_days = 0

        return {
            "dust_stress_level": level,
            "confidence": round(min(stress_score, 100), 1),
            "indicators": indicators,
            "affected_areas": _describe_dust_impact(level, ndvi, lst_c),
            "recovery_days": recovery_days,
            "recommendation": _get_dust_response_recommendation(level),
        }

    except (TypeError, ValueError) as e:
        logger.error(f"Error detecting dust stress: {e}")
        return {
            "dust_stress_level": "none",
            "confidence": 0.0,
            "indicators": [],
            "affected_areas": "Unable to assess",
            "recovery_days": 0,
            "recommendation": "Monitoring required",
        }


def _describe_dust_impact(level: str, ndvi: float, lst_c: float) -> str:
    """Describe the impact of dust stress."""
    if level == "severe":
        return (f"Severe dust storm conditions detected. "
                f"Temperature at {lst_c:.1f}°C, NDVI at {ndvi:.2f}. "
                f"Crop damage likely. 2-week recovery expected.")
    elif level == "high":
        return (f"High dust stress affecting vegetation. "
                f"Temperature {lst_c:.1f}°C, NDVI {ndvi:.2f}. "
                f"Reduced photosynthesis expected.")
    elif level == "moderate":
        return f"Moderate dust conditions. Monitor closely."
    else:
        return "Normal conditions for Eastern Province."


def _get_dust_response_recommendation(level: str) -> str:
    """Get management recommendation for dust conditions."""
    if level == "severe":
        return ("Postpone field operations. Increase irrigation to wash dust from leaves. "
                "Monitor for pest outbreaks that follow dust storms.")
    elif level == "high":
        return "Reduce field operations. Apply light irrigation if water available."
    elif level == "moderate":
        return "Monitor crop condition. Avoid chemical application during dust events."
    else:
        return "Normal operations. Continue monitoring."


def calculate_saudi_crop_water_requirement(
    crop_type: str,
    growth_stage: str,
    temperature: float,
    humidity: int,
    et_reference: float | None = None,
) -> dict[str, Any]:
    """
    Calculate crop-specific water requirements for Saudi conditions.

    Saudi irrigation uses reference evapotranspiration (ET0) with
    crop coefficients (Kc) adjusted for:
    - High temperatures (30-50°C)
    - Low humidity (10-30%)
    - Soil types (sandy, loamy)
    - Growth stage

    Args:
        crop_type: Type of crop (dates, wheat, tomatoes, alfalfa)
        growth_stage: Growth stage (initial, development, mid, late)
        temperature: Current temperature in Celsius
        humidity: Relative humidity percentage
        et_reference: Reference ET (if measured, otherwise calculated)

    Returns:
        Water requirement with:
        - daily_water_mm: Daily water requirement in mm
        - irrigation_hours: Hours needed for typical system
        - next_irrigation: When to irrigate next
        - stress_level: Current water stress level
    """
    try:
        # Crop coefficients (Kc) for Eastern Province
        kc_values = {
            "dates": {
                "initial": 0.5,
                "development": 0.7,
                "mid": 0.9,
                "late": 0.7,
            },
            "wheat": {
                "initial": 0.4,
                "development": 0.7,
                "mid": 1.1,
                "late": 0.4,
            },
            "tomatoes": {
                "initial": 0.6,
                "development": 0.8,
                "mid": 1.05,
                "late": 0.9,
            },
            "alfalfa": {
                "initial": 0.4,
                "development": 0.7,
                "mid": 1.0,
                "late": 1.0,
            },
        }

        # Get Kc for crop and stage
        if crop_type not in kc_values:
            crop_type = "dates"
        kc = kc_values[crop_type].get(growth_stage, 0.7)

        # Calculate or use provided ET0
        if et_reference is None:
            # Estimate ET0 using Hargreaves formula for Saudi conditions
            # ET0 = 0.0023 * Ra * (T + 17.8) * sqrt(Tmax - Tmin)
            # Simplified: ET0 ≈ 6-10 mm/day in Eastern Province
            base_et0 = 8.0  # mm/day average
            # Temperature adjustment
            temp_factor = 1 + (temperature - 35) * 0.02
            et0 = base_et0 * temp_factor
        else:
            et0 = et_reference

        # Calculate crop water requirement (ETc = Kc * ET0)
        daily_water_mm = kc * et0

        # Saudi-specific adjustments
        # Sandy soil needs more water due to infiltration
        sand_factor = 1.2

        # High temperature increases transpiration
        temp_adjustment = 1 + max(0, (temperature - 35) * 0.015)

        # Low humidity increases evapotranspiration
        humidity_adjustment = 1 + (30 - min(humidity, 30)) * 0.005

        # Apply adjustments
        adjusted_water = daily_water_mm * sand_factor * temp_adjustment * humidity_adjustment

        # Calculate irrigation hours for typical drip system
        # Drip irrigation: 2-4 mm/hour
        irrigation_rate = 3.0  # mm/hour
        irrigation_hours = adjusted_water / irrigation_rate

        # Determine stress level
        stress_level = "none"
        if temperature > 45:
            stress_level = "severe"
        elif temperature > 40:
            stress_level = "moderate"
        elif humidity < 15 and temperature > 35:
            stress_level = "moderate"
        elif humidity < 20:
            stress_level = "low"

        return {
            "daily_water_mm": round(adjusted_water, 1),
            "irrigation_hours": round(irrigation_hours, 1),
            "irrigation_rate_mm_hr": irrigation_rate,
            "crop_coefficient": round(kc, 2),
            "reference_et": round(et0, 1),
            "next_irrigation": _calculate_next_irrigation(
                stress_level, adjusted_water, temperature, humidity
            ),
            "stress_level": stress_level,
            "recommendation": _get_irrigation_recommendation(
                crop_type, stress_level, temperature, adjusted_water
            ),
        }

    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating water requirement: {e}")
        return {
            "daily_water_mm": 0.0,
            "irrigation_hours": 0.0,
            "irrigation_rate_mm_hr": 0.0,
            "crop_coefficient": 0.0,
            "reference_et": 0.0,
            "next_irrigation": "24 hours",
            "stress_level": "unknown",
            "recommendation": "Unable to calculate",
        }


def _calculate_next_irrigation(
    stress_level: str,
    water_mm: float,
    temperature: float,
    humidity: int,
) -> str:
    """Calculate when next irrigation should occur."""
    from datetime import datetime, timedelta

    # Base interval in hours
    base_interval = 24

    # Adjust based on conditions
    if stress_level == "severe":
        interval = base_interval // 2  # Every 12 hours
    elif stress_level == "moderate":
        interval = base_interval * 2 // 3  # Every 16 hours
    elif temperature > 40:
        interval = base_interval * 3 // 4  # Every 18 hours
    elif humidity < 15:
        interval = base_interval * 3 // 4  # Every 18 hours
    else:
        interval = base_interval

    next_time = datetime.now() + timedelta(hours=interval)
    return f"Irrigate in {interval} hours (by {next_time.strftime('%H:%M')})"


def _get_irrigation_recommendation(
    crop_type: str,
    stress_level: str,
    temperature: float,
    water_mm: float,
) -> str:
    """Get irrigation recommendation."""
    if stress_level == "severe":
        return (f"CRITICAL: Irrigate immediately. {water_mm:.1f}mm required. "
                f"Use mulch to reduce evaporation.")
    elif stress_level == "moderate":
        return f"Irrigate within 6 hours. {water_mm:.1f}mm recommended."
    elif temperature > 42:
        return f"High temperature stress. Consider evening irrigation to reduce evaporation."
    else:
        return f"Normal irrigation. {water_mm:.1f}mm daily requirement."


# ==================== VALIDATION AND QUALITY CONTROL ====================

def validate_index_value(
    index_name: str,
    value: float,
    satellite_source: str = "modis",
) -> dict[str, Any]:
    """
    Validate vegetation index values against theoretical bounds and sensor limits.

    Performs range validation, NaN/Inf checking, and physical constraint validation.
    Returns validation results with warnings and quality flags.

    Args:
        index_name: Name of the index (ndvi, evi, lst, etc.)
        value: Calculated index value
        satellite_source: Satellite data source (modis, landsat, sentinel2)

    Returns:
        Validation dict with:
        - valid: Boolean indicating if value passes all checks
        - warnings: List of validation warnings
        - quality_flag: Quality indicator (excellent, good, moderate, poor)
        - clamped_value: Value clamped to valid range if out of bounds

    Reference:
        - MODIS C6 User Guide for quality flags
        - Landsat Collection 2 Product Guide
    """
    import math

    result = {
        "valid": True,
        "warnings": [],
        "quality_flag": "excellent",
        "clamped_value": value,
        "original_value": value,
    }

    # Check for NaN and Inf
    if math.isnan(value):
        result["valid"] = False
        result["warnings"].append(f"{index_name}: NaN value detected")
        result["quality_flag"] = "poor"
        result["clamped_value"] = 0.0
        return result

    if math.isinf(value):
        result["valid"] = False
        result["warnings"].append(f"{index_name}: Infinite value detected")
        result["quality_flag"] = "poor"
        result["clamped_value"] = 0.0
        return result

    # Define theoretical bounds for each index
    index_bounds = {
        "ndvi": {"min": -1.0, "max": 1.0, "typical_min": -0.2, "typical_max": 0.9},
        "evi": {"min": -1.0, "max": 1.0, "typical_min": -0.1, "typical_max": 0.9},
        "savi": {"min": -1.0, "max": 1.0, "typical_min": -0.1, "typical_max": 0.9},
        "msavi": {"min": 0.0, "max": 1.0, "typical_min": 0.0, "typical_max": 0.9},
        "osavi": {"min": -1.0, "max": 1.0, "typical_min": -0.1, "typical_max": 0.9},
        "gndvi": {"min": -1.0, "max": 1.0, "typical_min": -0.1, "typical_max": 0.9},
        "ndre": {"min": -1.0, "max": 1.0, "typical_min": 0.0, "typical_max": 0.8},
        "ndmi": {"min": -1.0, "max": 1.0, "typical_min": -0.3, "typical_max": 0.6},
        "ndwi": {"min": -1.0, "max": 1.0, "typical_min": -0.8, "typical_max": 0.5},
        "bsi": {"min": -1.0, "max": 1.0, "typical_min": -0.2, "typical_max": 0.6},
        "nbr": {"min": -1.0, "max": 1.0, "typical_min": -0.5, "typical_max": 0.8},
        "lst": {"min": 250.0, "max": 330.0, "typical_min": 270.0, "typical_max": 325.0},  # Kelvin
        "vci": {"min": 0.0, "max": 100.0, "typical_min": 10.0, "typical_max": 95.0},
        "tci": {"min": 0.0, "max": 100.0, "typical_min": 10.0, "typical_max": 95.0},
        "vhi": {"min": 0.0, "max": 100.0, "typical_min": 15.0, "typical_max": 90.0},
    }

    bounds = index_bounds.get(index_name.lower())

    if bounds is None:
        result["warnings"].append(f"{index_name}: No validation bounds defined")
        result["quality_flag"] = "moderate"
        return result

    # Check theoretical bounds
    if value < bounds["min"] or value > bounds["max"]:
        result["valid"] = False
        result["warnings"].append(
            f"{index_name}: Value {value:.3f} outside theoretical bounds "
            f"[{bounds['min']}, {bounds['max']}]"
        )
        result["quality_flag"] = "poor"
        # Clamp to theoretical bounds
        result["clamped_value"] = max(bounds["min"], min(value, bounds["max"]))

    # Check typical range (Eastern Province context)
    if value < bounds["typical_min"] or value > bounds["typical_max"]:
        result["warnings"].append(
            f"{index_name}: Value {value:.3f} outside typical range "
            f"[{bounds['typical_min']}, {bounds['typical_max']}] for Eastern Province"
        )
        if result["quality_flag"] == "excellent":
            result["quality_flag"] = "moderate"

    # Source-specific validation
    if satellite_source == "modis":
        # MODIS has known issues with saturation at high NDVI
        if index_name.lower() == "ndvi" and value > 0.95:
            result["warnings"].append("MODIS NDVI may be saturated (dense canopy)")
            result["quality_flag"] = "moderate"

    elif satellite_source == "landsat":
        # Landsat has striping issues in some bands
        if index_name.lower() == "ndvi" and abs(value) < 0.01:
            result["warnings"].append("Possible Landsat striping or cloud contamination")
            result["quality_flag"] = "moderate"

    return result


def calculate_index_uncertainty(
    index_name: str,
    value: float,
    cloud_cover: float,
    satellite_source: str = "modis",
    sensor_azimuth: float | None = None,
    sun_azimuth: float | None = None,
) -> dict[str, Any]:
    """
    Calculate uncertainty bounds for vegetation indices.

    Propagates measurement errors through index calculations and
    provides confidence intervals based on:
    - Sensor characteristics
    - Cloud contamination
    - Viewing geometry
    - Atmospheric conditions

    Args:
        index_name: Name of the index
        value: Calculated index value
        cloud_cover: Cloud cover percentage (0-100)
        satellite_source: Satellite data source
        sensor_azimuth: Sensor viewing azimuth angle (degrees)
        sun_azimuth: Sun azimuth angle (degrees)

    Returns:
        Uncertainty dict with:
        - value: Original value
        - uncertainty: Absolute uncertainty (±)
        - lower_bound: Lower confidence bound
        - upper_bound: Upper confidence bound
        - confidence: Confidence level (0-1)
        - error_sources: List of identified error sources

    Reference:
        - MODIS Vegetation Index User Guide (Collection 6)
        - Landsat Surface Reflectance Product Guide
    """
    import math

    # Base uncertainty from sensor characteristics
    sensor_uncertainties = {
        "modis": {"ndvi": 0.025, "evi": 0.030, "lst": 1.5},
        "landsat": {"ndvi": 0.020, "evi": 0.025, "lst": 1.0},
        "sentinel2": {"ndvi": 0.015, "evi": 0.020, "lst": 0.8},
    }

    base_uncertainty = sensor_uncertainties.get(
        satellite_source, {}
    ).get(index_name.lower(), 0.03)

    # Cloud contamination increases uncertainty
    cloud_factor = 1.0
    if cloud_cover > 0:
        cloud_factor = 1.0 + (cloud_cover / 100.0) * 0.5

    # Geometry effects (BRDF)
    geometry_factor = 1.0
    if sensor_azimuth is not None and sun_azimuth is not None:
        # Large view-sun angles increase uncertainty
        angle_diff = abs(sensor_azimuth - sun_azimuth)
        if angle_diff > 90:
            geometry_factor = 1.2
        elif angle_diff > 60:
            geometry_factor = 1.1

    # Combine uncertainty sources
    combined_uncertainty = base_uncertainty * cloud_factor * geometry_factor

    # Calculate bounds
    lower_bound = value - combined_uncertainty
    upper_bound = value + combined_uncertainty

    # Clamp to physical limits
    if index_name.lower() in ["ndvi", "evi", "savi", "ndmi", "ndwi"]:
        lower_bound = max(-1.0, lower_bound)
        upper_bound = min(1.0, upper_bound)
    elif index_name.lower() == "lst":
        lower_bound = max(250.0, lower_bound)
        upper_bound = min(330.0, upper_bound)

    # Error source identification
    error_sources = []
    if cloud_cover > 10:
        error_sources.append(f"cloud_contamination_{cloud_cover:.0f}%")
    if cloud_factor > 1.2:
        error_sources.append("high_cloud_cover")
    if geometry_factor > 1.0:
        error_sources.append("viewing_geometry")

    # Calculate confidence based on uncertainty magnitude
    # Higher uncertainty = lower confidence
    relative_uncertainty = combined_uncertainty / abs(value) if value != 0 else 1.0
    if relative_uncertainty < 0.05:
        confidence = 0.95
    elif relative_uncertainty < 0.10:
        confidence = 0.85
    elif relative_uncertainty < 0.20:
        confidence = 0.70
    else:
        confidence = 0.50

    return {
        "value": value,
        "uncertainty": round(combined_uncertainty, 4),
        "lower_bound": round(lower_bound, 4),
        "upper_bound": round(upper_bound, 4),
        "confidence": round(confidence, 2),
        "error_sources": error_sources,
        "relative_uncertainty": round(relative_uncertainty, 3),
    }


def quality_flag_to_bool(quality_flag: str) -> bool:
    """Convert quality flag to boolean for data filtering."""
    return quality_flag in ["excellent", "good"]


def filter_indices_by_quality(
    indices: dict[str, float],
    quality_flags: dict[str, str],
    min_quality: str = "good",
) -> dict[str, float]:
    """
    Filter indices by quality threshold.

    Args:
        indices: Dictionary of index values
        quality_flags: Dictionary of quality flags for each index
        min_quality: Minimum quality level (excellent, good, moderate)

    Returns:
        Filtered dictionary with only indices meeting quality threshold
    """
    quality_levels = {"excellent": 3, "good": 2, "moderate": 1, "poor": 0}
    min_level = quality_levels.get(min_quality, 2)

    filtered = {}
    for name, value in indices.items():
        quality = quality_flags.get(name, "moderate")
        if quality_levels.get(quality, 0) >= min_level:
            filtered[name] = value

    return filtered
