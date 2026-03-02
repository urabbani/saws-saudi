"""SAWS Drought Services Module."""

from app.services.drought.classifier import (
    classify_drought,
    generate_drought_report,
)
from app.services.drought.spei import (
    calculate_multi_scale_spei,
    calculate_spei_for_location,
    get_spei_classification,
)

__all__ = [
    "calculate_spei_for_location",
    "calculate_multi_scale_spei",
    "get_spei_classification",
    "classify_drought",
    "generate_drought_report",
]
