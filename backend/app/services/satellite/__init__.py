"""SAWS Satellite Services Module."""

from app.services.satellite.gee import GeeClient, initialize_gee
from app.services.satellite.indices import (
    calculate_aridity_index,
    calculate_ci_green,
    calculate_ci_rededge,
    calculate_composite_drought_index,
    calculate_crop_yield_index,
    calculate_desertification_index,
    calculate_evi,
    calculate_gndvi,
    calculate_lst,
    calculate_mcari,
    calculate_msavi,
    calculate_ndmi,
    calculate_ndre,
    calculate_ndvi,
    calculate_ndsi,
    calculate_ndwi,
    calculate_oasis_health_index,
    calculate_osavi,
    calculate_savi,
    calculate_thermal_stress_index,
    calculate_tci,
    calculate_vci,
    calculate_vdi,
    calculate_vhi,
    calculate_wdrvi,
    classify_drought_severity,
    classify_vegetation_health,
)

__all__ = [
    # GEE Client
    "GeeClient",
    "initialize_gee",
    # Core Indices
    "calculate_ndvi",
    "calculate_evi",
    "calculate_savi",
    "calculate_msavi",
    "calculate_osavi",
    # Advanced Vegetation Indices
    "calculate_gndvi",
    "calculate_ndre",
    "calculate_wdrvi",
    "calculate_ci_green",
    "calculate_ci_rededge",
    "calculate_mcari",
    "calculate_mtvi2",
    # Drought Indices
    "calculate_ndmi",
    "calculate_ndwi",
    "calculate_vdi",
    "calculate_tci",
    "calculate_vci",
    "calculate_vhi",
    # Soil and Stress Indices
    "calculate_bsi",
    "calculate_nbr",
    "calculate_nbr2",
    "calculate_ndsi",
    "calculate_lst",
    # Saudi Arabia Specific
    "calculate_aridity_index",
    "calculate_desertification_index",
    "calculate_thermal_stress_index",
    "calculate_oasis_health_index",
    # Composite and Crop Indices
    "calculate_composite_drought_index",
    "calculate_crop_yield_index",
    # Classification
    "classify_vegetation_health",
    "classify_drought_severity",
]
