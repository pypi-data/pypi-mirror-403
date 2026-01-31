"""
Applicability Utilities for AI Components

This module provides utilities for working with applicability constraints
across AI personas, input/output formats, and assembly components.
"""

from .applicability_calculation_utils import (
    ApplicabilityIntersection,
    calculate_applicability_intersection,
    generate_applicability_summary,
    validate_component_alignment,
    validate_input_modality_match,
    validate_output_modality_match
)

# from .applicability_filters_to_sql import (
#     # Add exports as needed
# )

# from .applicability_filter_on_prefetched_data import (
#     # Add exports as needed
# )

__all__ = [
    # Applicability Calculation
    "ApplicabilityIntersection",
    "calculate_applicability_intersection",
    "generate_applicability_summary",
    "validate_component_alignment",
    "validate_input_modality_match",
    "validate_output_modality_match",
]
