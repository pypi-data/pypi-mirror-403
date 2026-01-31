"""
Applicability Calculation Utilities - Auto-calculate analyst/task config applicability.

Provides functions to:
1. Calculate applicability intersection of multiple components
2. Validate component alignment (non-empty intersection)
3. Generate human-readable applicability summaries

Used by:
- AIAnalyst generation (auto-calculate from persona + assembly + model)
- AITaskConfig generation (auto-calculate from analyst + input + output)
- Validation before deployment
"""

from typing import List, Dict, Any, Optional, Union, Set
from datetime import datetime
import copy

from ipulse_shared_base_ftredge.enums.enums_pulse import (
    SectorRecordsCategory,
    SubjectCategory,
    ScopingField
)
from ipulse_shared_base_ftredge.enums.enums_analysts import ThinkingHorizon


class ApplicabilityIntersection:
    """
    Calculate intersection of applicability constraints across multiple components.
    
    Rules:
    1. None (ALL) intersect with List = List (more restrictive wins)
    2. List intersect with List = intersection (set intersection)
    3. Empty intersection = incompatible components
    4. JSON constraints are merged (more restrictive wins)
    """
    
    @staticmethod
    def intersect_lists(
        list1: Optional[Union[List, str]],
        list2: Optional[Union[List, str]]
    ) -> Optional[Union[List, str]]:
        """
        Intersect two applicability lists.
        
        Args:
            list1: First list (or None for ALL)
            list2: Second list (or None for ALL)
            
        Returns:
            Intersection (or None if result is ALL)
            
        Raises:
            ValueError if intersection is empty (incompatible)
        """
        # Parse string lists if needed
        if isinstance(list1, str):
            list1 = [item.strip() for item in list1.split(',') if item.strip()]
        if isinstance(list2, str):
            list2 = [item.strip() for item in list2.split(',') if item.strip()]
        
        # None (ALL) intersect with anything = the other thing
        if list1 is None:
            return list2
        if list2 is None:
            return list1
        
        # Both are lists - compute set intersection
        set1 = set(list1)
        set2 = set(list2)
        result = set1 & set2
        
        if not result:
            raise ValueError(f"Empty intersection: {list1} ∩ {list2} = ∅")
        
        return sorted(list(result))
    
    @staticmethod
    def intersect_json_constraints(
        constraints1: Optional[Union[Dict, str]],
        constraints2: Optional[Union[Dict, str]]
    ) -> Optional[Dict]:
        """
        Intersect two JSON constraint dictionaries.
        
        Strategy:
        - If a field exists in both, take the MORE RESTRICTIVE constraint
        - If a field exists in only one, include it (AND logic)
        - For numeric comparisons, take the tighter bound
        - For IN/NOT_IN, take the intersection/union
        
        Args:
            constraints1: First constraint dict
            constraints2: Second constraint dict
            
        Returns:
            Merged constraints (more restrictive)
        """
        import json
        
        # Parse JSON strings if needed
        if isinstance(constraints1, str):
            constraints1 = json.loads(constraints1) if constraints1 else None
        if isinstance(constraints2, str):
            constraints2 = json.loads(constraints2) if constraints2 else None
        
        # None (no constraints) = ALL, so return the other
        if constraints1 is None:
            return constraints2
        if constraints2 is None:
            return constraints1
        
        # Merge constraints
        result = copy.deepcopy(constraints1)
        
        for field, constraint2 in constraints2.items():
            if field not in result:
                # Field only in constraints2 - add it
                result[field] = constraint2
                continue
            
            constraint1 = result[field]
            
            # Both have this field - merge
            # Handle different constraint formats
            if isinstance(constraint1, dict) and isinstance(constraint2, dict):
                # Structured constraint with operator
                result[field] = ApplicabilityIntersection._merge_structured_constraints(
                    field, constraint1, constraint2
                )
            elif isinstance(constraint1, list) and isinstance(constraint2, list):
                # Simple list (e.g., industry: ["software", "semiconductors"])
                # Intersection
                result[field] = sorted(list(set(constraint1) & set(constraint2)))
                if not result[field]:
                    raise ValueError(f"Empty intersection for {field}: {constraint1} ∩ {constraint2} = ∅")
            else:
                # Mixed types or simple values - take constraint2 (assumes it's more specific)
                result[field] = constraint2
        
        return result
    
    @staticmethod
    def _merge_structured_constraints(
        field: str,
        c1: Dict[str, Any],
        c2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two structured constraints (with operator + value).
        
        Examples:
        - GT(10B) ∩ GT(50B) = GT(50B) (more restrictive)
        - GT(10B) ∩ LT(100B) = BETWEEN(10B, 100B)
        - IN([A,B,C]) ∩ IN([B,C,D]) = IN([B,C])
        """
        op1 = c1.get("operator")
        op2 = c2.get("operator")
        val1 = c1.get("value")
        val2 = c2.get("value")
        
        # IN operators - intersection
        if op1 == "IN" and op2 == "IN":
            intersection = sorted(list(set(val1) & set(val2)))
            if not intersection:
                raise ValueError(f"Empty intersection for {field}: {val1} ∩ {val2} = ∅")
            return {"operator": "IN", "value": intersection}
        
        # NOT_IN operators - union (exclude more subjects)
        if op1 == "NOT_IN" and op2 == "NOT_IN":
            union = sorted(list(set(val1) | set(val2)))
            return {"operator": "NOT_IN", "value": union}
        
        # Numeric comparisons - take tighter bound
        if op1 in ["GT", "GTE", "LT", "LTE"] and op2 in ["GT", "GTE", "LT", "LTE"]:
            return ApplicabilityIntersection._merge_numeric_constraints(field, c1, c2)
        
        # BETWEEN - intersect ranges
        if op1 == "BETWEEN" and op2 == "BETWEEN":
            min1, max1 = val1
            min2, max2 = val2
            new_min = max(min1, min2)
            new_max = min(max1, max2)
            if new_min > new_max:
                raise ValueError(f"Empty intersection for {field}: [{min1},{max1}] ∩ [{min2},{max2}] = ∅")
            return {"operator": "BETWEEN", "value": [new_min, new_max]}
        
        # Mixed operators - more complex logic
        # For simplicity, take the second constraint (assumes it's more specific)
        return c2
    
    @staticmethod
    def _merge_numeric_constraints(
        field: str,
        c1: Dict[str, Any],
        c2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge numeric comparison constraints.
        
        GT(10) ∩ GT(50) = GT(50)
        LT(100) ∩ LT(50) = LT(50)
        GT(10) ∩ LT(100) = BETWEEN(10, 100)
        """
        op1, val1 = c1["operator"], c1["value"]
        op2, val2 = c2["operator"], c2["value"]
        
        # Both GT/GTE - take max
        if op1 in ["GT", "GTE"] and op2 in ["GT", "GTE"]:
            if val1 >= val2:
                return c1
            else:
                return c2
        
        # Both LT/LTE - take min
        if op1 in ["LT", "LTE"] and op2 in ["LT", "LTE"]:
            if val1 <= val2:
                return c1
            else:
                return c2
        
        # GT/GTE vs LT/LTE - create BETWEEN
        if op1 in ["GT", "GTE"] and op2 in ["LT", "LTE"]:
            if val1 >= val2:
                raise ValueError(f"Empty intersection for {field}: {op1}({val1}) ∩ {op2}({val2}) = ∅")
            return {"operator": "BETWEEN", "value": [val1, val2]}
        
        if op2 in ["GT", "GTE"] and op1 in ["LT", "LTE"]:
            if val2 >= val1:
                raise ValueError(f"Empty intersection for {field}: {op1}({val1}) ∩ {op2}({val2}) = ∅")
            return {"operator": "BETWEEN", "value": [val2, val1]}
        
        # Fallback
        return c2
    
    @staticmethod
    def intersect_manual_overrides(
        overrides1: Optional[Union[Dict, str]],
        overrides2: Optional[Union[Dict, str]]
    ) -> Optional[Dict]:
        """
        Intersect manual subject overrides.
        
        Logic:
        - include_subjects: intersection (both must allow)
        - exclude_subjects: union (exclude if either excludes)
        """
        import json
        
        # Parse JSON strings if needed
        if isinstance(overrides1, str):
            overrides1 = json.loads(overrides1) if overrides1 else None
        if isinstance(overrides2, str):
            overrides2 = json.loads(overrides2) if overrides2 else None
        
        if overrides1 is None:
            return overrides2
        if overrides2 is None:
            return overrides1
        
        result = {}
        
        # Include subjects - intersection (both must allow)
        include1 = set(overrides1.get("include_subjects", []))
        include2 = set(overrides2.get("include_subjects", []))
        
        if include1 and include2:
            include_intersection = include1 & include2
            if not include_intersection:
                raise ValueError(f"Empty include_subjects intersection: {include1} ∩ {include2} = ∅")
            result["include_subjects"] = sorted(list(include_intersection))
        elif include1:
            result["include_subjects"] = sorted(list(include1))
        elif include2:
            result["include_subjects"] = sorted(list(include2))
        
        # Exclude subjects - union (exclude if either excludes)
        exclude1 = set(overrides1.get("exclude_subjects", []))
        exclude2 = set(overrides2.get("exclude_subjects", []))
        
        if exclude1 or exclude2:
            exclude_union = exclude1 | exclude2
            result["exclude_subjects"] = sorted(list(exclude_union))
        
        return result if result else None
    
    @staticmethod
    def intersect_horizon_constraints(
        constraints1: Optional[Union[Dict, str]],
        constraints2: Optional[Union[Dict, str]]
    ) -> Optional[Dict]:
        """
        Intersect horizon constraint dictionaries.
        
        Strategy:
        - min_horizon_months: take max (more restrictive)
        - max_horizon_months: take min (more restrictive)
        - compatible_step_units: intersection
        - min_step_value: take max
        - max_step_value: take min
        """
        import json
        
        # Parse JSON strings if needed
        if isinstance(constraints1, str):
            constraints1 = json.loads(constraints1) if constraints1 else None
        if isinstance(constraints2, str):
            constraints2 = json.loads(constraints2) if constraints2 else None
        
        if constraints1 is None:
            return constraints2
        if constraints2 is None:
            return constraints1
        
        result = {}
        
        # Min horizon - take max (more restrictive)
        min1 = constraints1.get("min_horizon_months")
        min2 = constraints2.get("min_horizon_months")
        if min1 is not None and min2 is not None:
            result["min_horizon_months"] = max(min1, min2)
        elif min1 is not None:
            result["min_horizon_months"] = min1
        elif min2 is not None:
            result["min_horizon_months"] = min2
        
        # Max horizon - take min (more restrictive)
        max1 = constraints1.get("max_horizon_months")
        max2 = constraints2.get("max_horizon_months")
        if max1 is not None and max2 is not None:
            result["max_horizon_months"] = min(max1, max2)
        elif max1 is not None:
            result["max_horizon_months"] = max1
        elif max2 is not None:
            result["max_horizon_months"] = max2
        
        # Validate min <= max
        if "min_horizon_months" in result and "max_horizon_months" in result:
            if result["min_horizon_months"] > result["max_horizon_months"]:
                raise ValueError(
                    f"Empty horizon intersection: min={result['min_horizon_months']} > max={result['max_horizon_months']}"
                )
        
        # Compatible step units - intersection
        units1 = constraints1.get("compatible_step_units", [])
        units2 = constraints2.get("compatible_step_units", [])
        if units1 and units2:
            units_intersection = sorted(list(set(units1) & set(units2)))
            if not units_intersection:
                raise ValueError(f"Empty step units intersection: {units1} ∩ {units2} = ∅")
            result["compatible_step_units"] = units_intersection
        elif units1:
            result["compatible_step_units"] = units1
        elif units2:
            result["compatible_step_units"] = units2
        
        # Min step value - take max
        min_step1 = constraints1.get("min_step_value")
        min_step2 = constraints2.get("min_step_value")
        if min_step1 is not None and min_step2 is not None:
            result["min_step_value"] = max(min_step1, min_step2)
        elif min_step1 is not None:
            result["min_step_value"] = min_step1
        elif min_step2 is not None:
            result["min_step_value"] = min_step2
        
        # Max step value - take min
        max_step1 = constraints1.get("max_step_value")
        max_step2 = constraints2.get("max_step_value")
        if max_step1 is not None and max_step2 is not None:
            result["max_step_value"] = min(max_step1, max_step2)
        elif max_step1 is not None:
            result["max_step_value"] = max_step1
        elif max_step2 is not None:
            result["max_step_value"] = max_step2
        
        # Copy other fields
        for key in constraints1:
            if key not in result and key not in ["min_horizon_months", "max_horizon_months", "compatible_step_units", "min_step_value", "max_step_value"]:
                result[key] = constraints1[key]
        for key in constraints2:
            if key not in result and key not in ["min_horizon_months", "max_horizon_months", "compatible_step_units", "min_step_value", "max_step_value"]:
                result[key] = constraints2[key]
        
        return result if result else None


def calculate_applicability_intersection(
    components: List[Any],
    include_runtime_injected: bool = False
) -> Dict[str, Any]:
    """
    Calculate applicability intersection across multiple components.
    
    Args:
        components: List of objects with applicability fields (Persona, InputFormat, OutputFormat, AssemblyComponent, etc.)
        include_runtime_injected: If False, skip components with content_resolution="runtime_injection"
        
    Returns:
        Dict with intersected applicability fields:
        {
            "applicable_sector_records_categories": [...],
            "applicable_subject_categories": [...],
            "applicability_constraints": {...},
            "manual_subjects_overrides": {...},
            "applicable_thinking_horizons": [...],
            "applicable_horizon_constraints": {...}
        }
        
    Raises:
        ValueError if intersection is empty (incompatible components)
    """
    
    if not components:
        raise ValueError("No components provided for intersection calculation")
    
    # Filter out runtime-injected components if requested
    if not include_runtime_injected:
        components = [
            c for c in components
            if not (hasattr(c, 'content_resolution') and c.content_resolution == "runtime_injection")
        ]
    
    if not components:
        # All were runtime-injected - return universal applicability
        return {
            "applicable_sector_records_categories": None,
            "applicable_subject_categories": None,
            "applicability_constraints": None,
            "manual_subjects_overrides": None,
            "applicable_thinking_horizons": None,
            "applicable_horizon_constraints": None
        }
    
    # Start with first component
    result = {
        "applicable_sector_records_categories": getattr(components[0], "applicable_sector_records_categories", None),
        "applicable_subject_categories": getattr(components[0], "applicable_subject_categories", None),
        "applicability_constraints": getattr(components[0], "applicability_constraints", None),
        "manual_subjects_overrides": getattr(components[0], "manual_subjects_overrides", None),
        "applicable_thinking_horizons": getattr(components[0], "applicable_thinking_horizons", None),
        "applicable_horizon_constraints": getattr(components[0], "applicable_horizon_constraints", None)
    }
    
    # Intersect with remaining components
    for component in components[1:]:
        # Subject applicability
        result["applicable_sector_records_categories"] = ApplicabilityIntersection.intersect_lists(
            result["applicable_sector_records_categories"],
            getattr(component, "applicable_sector_records_categories", None)
        )
        
        result["applicable_subject_categories"] = ApplicabilityIntersection.intersect_lists(
            result["applicable_subject_categories"],
            getattr(component, "applicable_subject_categories", None)
        )
        
        result["applicability_constraints"] = ApplicabilityIntersection.intersect_json_constraints(
            result["applicability_constraints"],
            getattr(component, "applicability_constraints", None)
        )
        
        result["manual_subjects_overrides"] = ApplicabilityIntersection.intersect_manual_overrides(
            result["manual_subjects_overrides"],
            getattr(component, "manual_subjects_overrides", None)
        )
        
        # Horizon applicability
        result["applicable_thinking_horizons"] = ApplicabilityIntersection.intersect_lists(
            result["applicable_thinking_horizons"],
            getattr(component, "applicable_thinking_horizons", None)
        )
        
        result["applicable_horizon_constraints"] = ApplicabilityIntersection.intersect_horizon_constraints(
            result["applicable_horizon_constraints"],
            getattr(component, "applicable_horizon_constraints", None)
        )
    
    # Add metadata
    result["applicability_calculated_at"] = datetime.utcnow()
    result["applicability_calculation_method"] = "intersection_v1"
    result["applicability_component_count"] = len(components)
    
    return result


def generate_applicability_summary(applicability: Dict[str, Any]) -> str:
    """
    Generate human-readable summary of applicability constraints.
    
    Args:
        applicability: Dict with applicability fields
        
    Returns:
        Human-readable string
        
    Example:
        "EQUITY only, large-cap US tech (>$50B), 5Y strategic, semi-annual"
    """
    parts = []
    
    # Subject categories
    subject_cats = applicability.get("applicable_subject_categories")
    if subject_cats:
        if isinstance(subject_cats, str):
            subject_cats = [s.strip() for s in subject_cats.split(',')]
        if len(subject_cats) == 1:
            parts.append(f"{subject_cats[0].upper()} only")
        else:
            parts.append(f"{', '.join([s.upper() for s in subject_cats])}")
    else:
        parts.append("ALL categories")
    
    # Constraints
    constraints = applicability.get("applicability_constraints")
    if constraints:
        if isinstance(constraints, str):
            import json
            constraints = json.loads(constraints)
        
        constraint_parts = []
        
        # Market cap
        if "market_cap" in constraints:
            mc = constraints["market_cap"]
            if isinstance(mc, dict):
                op = mc.get("operator")
                val = mc.get("value")
                if op == "GT":
                    constraint_parts.append(f">${val/1e9:.0f}B")
                elif op == "LT":
                    constraint_parts.append(f"<${val/1e9:.0f}B")
        
        # Industry
        if "industry" in constraints:
            ind = constraints["industry"]
            if isinstance(ind, dict) and ind.get("operator") == "IN":
                industries = ind["value"]
                if len(industries) <= 2:
                    constraint_parts.append(", ".join(industries))
                else:
                    constraint_parts.append(f"{len(industries)} industries")
            elif isinstance(ind, list):
                if len(ind) <= 2:
                    constraint_parts.append(", ".join(ind))
                else:
                    constraint_parts.append(f"{len(ind)} industries")
        
        # Region
        if "region" in constraints:
            reg = constraints["region"]
            if isinstance(reg, dict) and reg.get("operator") == "IN":
                constraint_parts.append(", ".join(reg["value"]))
            elif isinstance(reg, list):
                constraint_parts.append(", ".join(reg))
        
        if constraint_parts:
            parts.append(" ".join(constraint_parts))
    
    # Horizons
    horizons = applicability.get("applicable_thinking_horizons")
    horizon_constraints = applicability.get("applicable_horizon_constraints")
    
    if horizons:
        if isinstance(horizons, str):
            horizons = [h.strip() for h in horizons.split(',')]
        if len(horizons) == 1:
            parts.append(horizons[0].replace("_", " ").title())
        else:
            parts.append("Multi-horizon")
    
    if horizon_constraints:
        if isinstance(horizon_constraints, str):
            import json
            horizon_constraints = json.loads(horizon_constraints)
        
        min_months = horizon_constraints.get("min_horizon_months")
        max_months = horizon_constraints.get("max_horizon_months")
        exact_months = horizon_constraints.get("exact_horizon_months")
        
        if exact_months:
            years = exact_months // 12
            parts.append(f"{years}Y")
        elif min_months and max_months:
            min_years = min_months // 12
            max_years = max_months // 12
            if min_years == max_years:
                parts.append(f"{min_years}Y")
            else:
                parts.append(f"{min_years}-{max_years}Y")
        elif min_months:
            years = min_months // 12
            parts.append(f"≥{years}Y")
        elif max_months:
            years = max_months // 12
            parts.append(f"≤{years}Y")
        
        step_months = horizon_constraints.get("exact_step_months")
        if step_months:
            if step_months == 6:
                parts.append("semi-annual")
            elif step_months == 3:
                parts.append("quarterly")
            elif step_months == 1:
                parts.append("monthly")
            else:
                parts.append(f"{step_months}mo steps")
    
    return ", ".join(parts)


def validate_component_alignment(
    *components,
    raise_on_empty: bool = True
) -> Dict[str, Any]:
    """
    Validate that components have non-empty applicability intersection.
    
    Args:
        *components: Variable number of component objects
        raise_on_empty: If True, raise ValueError on empty intersection
        
    Returns:
        Applicability dict if valid
        
    Raises:
        ValueError if intersection is empty and raise_on_empty=True
    """
    try:
        applicability = calculate_applicability_intersection(list(components))
        applicability["applicability_summary"] = generate_applicability_summary(applicability)
        return applicability
    except ValueError as e:
        if raise_on_empty:
            raise ValueError(f"Component alignment validation failed: {e}")
        return None


def validate_input_modality_match(input_format, model_version) -> bool:
    """
    Validate that input format modalities are supported by model version input capabilities.
    
    Args:
        input_format: AIInputFormat instance
        model_version: AIModelVersion instance
        
    Returns:
        True if modalities are compatible, False otherwise
    """
    if not model_version.input_capabilities:
        return False
    
    # Primary modality check
    if input_format.primary_data_modality not in model_version.input_capabilities.modalities:
        return False
    
    # Encapsulated modalities check
    if input_format.encapsulated_data_modalities:
        for mod in input_format.encapsulated_data_modalities:
            if mod not in model_version.input_capabilities.modalities:
                return False
    
    # Content dynamics check
    if input_format.content_dynamics:
        for dyn in input_format.content_dynamics:
            if dyn not in model_version.input_capabilities.content_dynamics:
                return False
    
    return True


def validate_output_modality_match(output_format, model_version) -> bool:
    """
    Validate that output format modalities are supported by model version output capabilities.
    
    Args:
        output_format: AIOutputFormat instance
        model_version: AIModelVersion instance
        
    Returns:
        True if modalities are compatible, False otherwise
    """
    if not model_version.output_capabilities:
        return False
    
    # Primary modality check
    if output_format.primary_data_modality not in model_version.output_capabilities.modalities:
        return False
    
    # Encapsulated modalities check
    if output_format.encapsulated_data_modalities:
        for mod in output_format.encapsulated_data_modalities:
            if mod not in model_version.output_capabilities.modalities:
                return False
    
    # Content dynamics check
    if output_format.content_dynamics:
        for dyn in output_format.content_dynamics:
            if dyn not in model_version.output_capabilities.content_dynamics:
                return False
    
    return True
