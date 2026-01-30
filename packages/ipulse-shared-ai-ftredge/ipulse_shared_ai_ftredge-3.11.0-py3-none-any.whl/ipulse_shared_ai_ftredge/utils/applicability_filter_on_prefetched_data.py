"""
Applicability Filtering Helpers - 4-Level Hierarchical Filtering

Provides helper functions for filtering AI components (personas, I/O formats) based on
subject/asset metadata using the 4-level applicability architecture.

LEVEL 0: Data type (sector_records_category) - 70% reduction
LEVEL 1: Asset class (subject_category) - 80% reduction of remaining
LEVEL 2: Fine-grained constraints (JSON) - 90% reduction of remaining
LEVEL 3: Manual overrides (explicit lists) - Edge cases

Total reduction: 99.9%+ (3 trillion → 3 million combinations)

Field names use ScopingField enum for consistency across filtering operations.
"""

import json
from typing import List, Union, Dict, Any, Optional
from ipulse_shared_base_ftredge.enums.enums_pulse import ScopingField
from ipulse_shared_ai_ftredge.models.intelligence_task_components.ai_input_format import AIInputFormat
from ipulse_shared_ai_ftredge.models.intelligence_task_components.ai_output_format import AIOutputFormat
from ipulse_shared_ai_ftredge.models.intelligence_designs.analyst_persona import AnalystPersona


def filter_components_by_applicability(
    components: List[Union[AIInputFormat, AIOutputFormat, AnalystPersona]],
    subject_meta: Dict[str, Any]
) -> List[Union[AIInputFormat, AIOutputFormat, AnalystPersona]]:
    """
    Apply LEVEL 0-3 filtering to components based on subject metadata.
    
    Args:
        components: List of AI components (input formats, output formats, or analyst personas)
        subject_meta: Dictionary with subject metadata using ScopingField keys:
            - ScopingField.SECTOR_RECORDS_CATEGORY or "sector_records_category"
            - ScopingField.SUBJECT_CATEGORY or "subject_category"
            - ScopingField.INDUSTRY or "industry"
            - ScopingField.REGION or "region"
            - ScopingField.ASSET_TIER or "asset_tier"
            - ScopingField.MARKET_CAP or "market_cap"
            - ScopingField.PE_RATIO or "pe_ratio"
            - ScopingField.REVENUE_GROWTH or "revenue_growth"
            - ScopingField.COUNTRY or "country"
            - ScopingField.SUBJECT_CATEGORY_DETAILED or "subject_category_detailed"
            - ScopingField.SUBJECT_ID or "subject_id" (for LEVEL 3 overrides)
    
    Returns:
        Filtered list of components that match the subject's applicability criteria
    
    Example:
        >>> subject = {
        ...     ScopingField.SECTOR_RECORDS_CATEGORY: "market",
        ...     ScopingField.SUBJECT_CATEGORY: "equity",
        ...     ScopingField.INDUSTRY: "software",
        ...     ScopingField.ASSET_TIER: "tier_1",
        ...     ScopingField.MARKET_CAP: 2500000000000,  # $2.5T
        ...     ScopingField.SUBJECT_ID: "AAPL"
        ... }
        >>> personas = get_all_personas()
        >>> applicable = filter_components_by_applicability(personas, subject)
    """
    filtered = []
    
    # Helper to get field value, supporting both enum and string keys
    def get_field(key: Union[ScopingField, str]) -> Any:
        """Get field value from subject_meta, trying both enum and string keys."""
        if isinstance(key, ScopingField):
            # Try enum first, then string
            return subject_meta.get(key) or subject_meta.get(str(key.value))
        return subject_meta.get(key)
    
    for component in components:
        # LEVEL 3: Manual overrides (check FIRST - has highest priority)
        subject_id = get_field(ScopingField.SUBJECT_ID)
        if subject_id:  # Only check manual overrides if subject_id is provided
            if is_manually_excluded(component, subject_id):
                continue  # Skip this component (blacklisted)
            
            if is_manually_included(component, subject_id):
                filtered.append(component)  # Add immediately (whitelisted)
                continue
            
            # Check if whitelist exists but subject not in it (should reject)
            if component.manual_subjects_overrides is not None:
                overrides = component.manual_subjects_overrides
                if isinstance(overrides, str):
                    try:
                        overrides = json.loads(overrides)
                    except json.JSONDecodeError:
                        overrides = {}
                
                include_subjects = overrides.get("include_subjects", [])
                if include_subjects:  # Whitelist exists
                    # Subject not in whitelist (is_manually_included returned False)
                    continue  # Skip this component
        
        # LEVEL 0: Check sector records category (fastest, broadest)
        if component.applicable_sector_records_categories is not None:
            # Parse if it's a comma-separated string
            categories = component.applicable_sector_records_categories
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(',') if c.strip()]
            
            sector_records_category = get_field(ScopingField.SECTOR_RECORDS_CATEGORY)
            if sector_records_category not in categories:
                continue  # Skip this component
        
        # LEVEL 1: Check subject category (fast, indexed)
        if component.applicable_subject_categories is not None:
            # Parse if it's a comma-separated string
            categories = component.applicable_subject_categories
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(',') if c.strip()]
            
            subject_category = get_field(ScopingField.SUBJECT_CATEGORY)
            if subject_category not in categories:
                continue  # Skip this component
        
        # LEVEL 2: Check fine-grained constraints
        if component.applicability_constraints is not None:
            constraints = component.applicability_constraints
            
            # Parse if it's a JSON string
            if isinstance(constraints, str):

                try:
                    constraints = json.loads(constraints)
                except json.JSONDecodeError:
                    # If parsing fails, skip this component (invalid constraints)
                    continue
            
            # Check if subject passes all constraints
            if not check_applicability_constraints(constraints, subject_meta):
                continue  # Skip this component
        
        # If we reach here, component passed all filters
        filtered.append(component)
    
    return filtered


def check_applicability_constraints(
    constraints: Dict[str, Any],
    subject_meta: Dict[str, Any]
) -> bool:
    """
    Check if subject metadata satisfies the applicability constraints.
    
    Supports operators: IN (default), NOT_IN, EQUALS, GT, GTE, LT, LTE, BETWEEN
    
    Args:
        constraints: Dictionary of constraints from applicability_constraints field
        subject_meta: Dictionary with subject metadata
    
    Returns:
        True if subject satisfies all constraints, False otherwise
    
    Examples:
        >>> # Simple IN constraint
        >>> check_applicability_constraints(
        ...     {"industry": ["software", "semiconductors"]},
        ...     {"industry": "software"}
        ... )
        True
        
        >>> # Comparison operator
        >>> check_applicability_constraints(
        ...     {"market_cap": {"operator": "GT", "value": 10000000000}},
        ...     {"market_cap": 2500000000000}
        ... )
        True
        
        >>> # Range operator
        >>> check_applicability_constraints(
        ...     {"pe_ratio": {"operator": "BETWEEN", "values": [10, 25]}},
        ...     {"pe_ratio": 15.5}
        ... )
        True
    """
    # Handle OR logic (if specified)
    if "_logic" in constraints and constraints["_logic"] == "OR":
        constraint_groups = constraints.get("constraint_groups", [])
        # At least one group must match
        return any(
            check_applicability_constraints(group, subject_meta)
            for group in constraint_groups
        )
    
    # Default: AND logic (all constraints must match)
    for field, constraint_value in constraints.items():
        if field == "_logic":  # Skip meta fields
            continue
        
        subject_value = subject_meta.get(field)
        
        # Handle different constraint types
        if isinstance(constraint_value, list):
            # Simple IN operator
            if subject_value not in constraint_value:
                return False
        
        elif isinstance(constraint_value, dict):
            # Advanced operator
            operator = constraint_value.get("operator", "IN")
            
            if operator == "IN":
                values = constraint_value.get("values", [])
                if subject_value not in values:
                    return False
            
            elif operator == "NOT_IN":
                values = constraint_value.get("values", [])
                if subject_value in values:
                    return False
            
            elif operator == "EQUALS":
                value = constraint_value.get("value")
                if subject_value != value:
                    return False
            
            elif operator == "GT":
                value = constraint_value.get("value")
                if subject_value is None or subject_value <= value:
                    return False
            
            elif operator == "GTE":
                value = constraint_value.get("value")
                if subject_value is None or subject_value < value:
                    return False
            
            elif operator == "LT":
                value = constraint_value.get("value")
                if subject_value is None or subject_value >= value:
                    return False
            
            elif operator == "LTE":
                value = constraint_value.get("value")
                if subject_value is None or subject_value > value:
                    return False
            
            elif operator == "BETWEEN":
                values = constraint_value.get("values", [])
                if len(values) != 2:
                    return False  # Invalid BETWEEN constraint
                if subject_value is None or not (values[0] <= subject_value <= values[1]):
                    return False
            
            else:
                # Unknown operator, fail safe
                return False
        
        else:
            # Simple equality check
            if subject_value != constraint_value:
                return False
    
    # All constraints passed
    return True


def is_manually_excluded(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    subject_id: str
) -> bool:
    """
    Check if subject is explicitly excluded via LEVEL 3 manual overrides.
    
    Args:
        component: AI component with manual_subjects_overrides field
        subject_id: Subject identifier (e.g., "AAPL", "BTC-USD")
    
    Returns:
        True if subject is blacklisted, False otherwise
    """
    if component.manual_subjects_overrides is None:
        return False
    
    overrides = component.manual_subjects_overrides
    
    # Parse if it's a JSON string
    if isinstance(overrides, str):
        try:
            overrides = json.loads(overrides)
        except json.JSONDecodeError:
            return False
    
    # Check exclude list
    exclude_subjects = overrides.get("exclude_subjects", [])
    return subject_id in exclude_subjects


def is_manually_included(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    subject_id: str
) -> bool:
    """
    Check if subject is explicitly included via LEVEL 3 manual overrides.
    
    When include_subjects is specified, ONLY those subjects are allowed (whitelist mode).
    
    Args:
        component: AI component with manual_subjects_overrides field
        subject_id: Subject identifier (e.g., "AAPL", "BTC-USD")
    
    Returns:
        True if subject is whitelisted (or no whitelist exists), False otherwise
    """
    if component.manual_subjects_overrides is None:
        return False  # No manual overrides, continue with normal filtering
    
    overrides = component.manual_subjects_overrides
    
    # Parse if it's a JSON string
    if isinstance(overrides, str):
        try:
            overrides = json.loads(overrides)
        except json.JSONDecodeError:
            return False
    
    # Check include list
    include_subjects = overrides.get("include_subjects", [])
    
    if not include_subjects:
        # No whitelist specified, not manually included
        return False
    
    # Whitelist exists - subject must be in it
    return subject_id in include_subjects


def get_applicable_components_summary(
    components: List[Union[AIInputFormat, AIOutputFormat, AnalystPersona]],
    subject_meta: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get detailed summary of filtering results for debugging/analytics.
    
    Args:
        components: List of AI components to filter
        subject_meta: Subject metadata dictionary
    
    Returns:
        Dictionary with filtering statistics:
            - total_components: int
            - passed_level_0: int
            - passed_level_1: int
            - passed_level_2: int
            - manually_included: int
            - manually_excluded: int
            - final_applicable: int
            - reduction_pct: float
    """
    stats = {
        "total_components": len(components),
        "passed_level_0": 0,
        "passed_level_1": 0,
        "passed_level_2": 0,
        "manually_included": 0,
        "manually_excluded": 0,
        "final_applicable": 0,
        "reduction_pct": 0.0
    }
    
    # Helper function for dual key support (enum or string)
    def get_field(key: Union[ScopingField, str]) -> Any:
        if isinstance(key, ScopingField):
            return subject_meta.get(key) or subject_meta.get(str(key.value))
        return subject_meta.get(key)
    
    subject_id = get_field(ScopingField.SUBJECT_ID)
    
    for component in components:
        # LEVEL 3 check (only if subject_id provided)
        if subject_id:
            if is_manually_excluded(component, subject_id):
                stats["manually_excluded"] += 1
                continue
            
            if is_manually_included(component, subject_id):
                stats["manually_included"] += 1
                stats["final_applicable"] += 1
                continue
        
        # LEVEL 0
        if component.applicable_sector_records_categories is not None:
            categories = component.applicable_sector_records_categories
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(',') if c.strip()]
            
            if get_field(ScopingField.SECTOR_RECORDS_CATEGORY) not in categories:
                continue
        
        stats["passed_level_0"] += 1
        
        # LEVEL 1
        if component.applicable_subject_categories is not None:
            categories = component.applicable_subject_categories
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(',') if c.strip()]
            
            if get_field(ScopingField.SUBJECT_CATEGORY) not in categories:
                continue
        
        stats["passed_level_1"] += 1
        
        # LEVEL 2
        if component.applicability_constraints is not None:
            constraints = component.applicability_constraints
            if isinstance(constraints, str):
                import json
                try:
                    constraints = json.loads(constraints)
                except json.JSONDecodeError:
                    continue
            
            if not check_applicability_constraints(constraints, subject_meta):
                continue
        
        stats["passed_level_2"] += 1
        stats["final_applicable"] += 1
    
    # Calculate reduction percentage
    if stats["total_components"] > 0:
        stats["reduction_pct"] = round(
            (1 - stats["final_applicable"] / stats["total_components"]) * 100,
            2
        )
    
    return stats
