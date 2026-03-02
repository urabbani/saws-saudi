"""SAWS Services Module."""

from app.services.alert import (
    generate_alerts_for_field,
    generate_harvest_alert,
    generate_irrigation_alert,
)
from app.services.drought import (
    calculate_multi_scale_spei,
    calculate_spei_for_location,
    classify_drought,
    generate_drought_report,
)
from app.services.satellite import (
    GeeClient,
    calculate_ndvi,
    calculate_evi,
    calculate_savi,
    calculate_ndmi,
    calculate_composite_drought_index,
)
from app.services.weather import PMEClient

__all__ = [
    # Satellite
    "GeeClient",
    "calculate_ndvi",
    "calculate_evi",
    "calculate_savi",
    "calculate_ndmi",
    "calculate_composite_drought_index",
    # Drought
    "calculate_spei_for_location",
    "calculate_multi_scale_spei",
    "classify_drought",
    "generate_drought_report",
    # Alerts
    "generate_alerts_for_field",
    "generate_irrigation_alert",
    "generate_harvest_alert",
    # Weather
    "PMEClient",
]
