"""
Reverse Applicability Filtering - Find subjects that match component constraints.

This module provides utilities for reverse filtering: given an AI component (input format,
output format, or analyst persona), find all subjects that the component is applicable to.

This is the inverse operation of applicability_filtering.py:
- Forward filtering: Given a subject, which components are applicable?
- Reverse filtering: Given a component, which subjects is it applicable to?

Use cases:
- Query planning: Generate SQL WHERE clauses to fetch applicable subjects
- Analytics: Count how many subjects each component applies to
- Validation: Verify component applicability scope before deployment
"""

from typing import Dict, Any, List, Optional, Union
from ipulse_shared_base_ftredge.enums.enums_pulse import ScopingField
from ipulse_shared_base_ftredge.enums.enums_status import ObjectOverallStatus
from ipulse_shared_ai_ftredge.models.intelligence_task_components.ai_input_format import AIInputFormat
from ipulse_shared_ai_ftredge.models.intelligence_task_components.ai_output_format import AIOutputFormat
from ipulse_shared_ai_ftredge.models.intelligence_designs.analyst_persona import AnalystPersona


def generate_bigquery_where_clause(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    subject_table_alias: str = "s",
    exclude_fields: Optional[List[Union[ScopingField, str]]] = None,
    pulse_statuses_to_have: Optional[List[Union[ObjectOverallStatus, str]]] = None,
    pulse_statuses_to_avoid: Optional[List[Union[ObjectOverallStatus, str]]] = None,
    field_mapping: Optional[Dict[Union[ScopingField, str], str]] = None
) -> str:
    """
    Generate a BigQuery WHERE clause to find subjects applicable to the component.
    
    This function translates the 4-level applicability filtering into SQL conditions:
    - LEVEL 0: sector_records_category IN (...)
    - LEVEL 1: subject_category IN (...)
    - LEVEL 2: JSON constraints → SQL conditions (market_cap > X, industry IN (...), etc.)
    - LEVEL 3: subject_id IN (include_subjects) OR subject_id NOT IN (exclude_subjects)
    - Plus: pulse_status filtering
    
    Args:
        component: AI component with applicability constraints
        subject_table_alias: SQL table alias for the subject table (default "s")
        exclude_fields: Fields to skip (e.g., if table doesn't have sector_records_category)
        pulse_statuses_to_have: List of ObjectOverallStatus values to include (OR logic)
        pulse_statuses_to_avoid: List of ObjectOverallStatus values to exclude
        field_mapping: Map component field names to table column names
            Example: {ScopingField.MARKET_CAP: "mkt_cap_usd"}
    
    Returns:
        SQL WHERE clause string (without "WHERE" keyword)
    
    Example:
        >>> persona = get_persona("large_cap_tech_specialist")
        >>> where_clause = generate_bigquery_where_clause(
        ...     persona,
        ...     "assets",
        ...     exclude_fields=[ScopingField.SECTOR_RECORDS_CATEGORY],
        ...     pulse_statuses_to_have=[ObjectOverallStatus.ACTIVE],
        ...     field_mapping={ScopingField.MARKET_CAP: "market_capitalization"}
        ... )
        >>> print(where_clause)
        assets.subject_category = 'equity'
        AND assets.industry IN ('software', 'semiconductors')
        AND assets.market_capitalization > 10000000000
        AND assets.pulse_status = 'active'
        AND assets.subject_id NOT IN ('EXCLUDED_TICKER')
        
        >>> # Use in query
        >>> query = f"SELECT * FROM subjects WHERE {where_clause}"
    """
    # Initialize helpers
    exclude_fields = exclude_fields or []
    field_mapping = field_mapping or {}
    
    # Normalize exclude_fields to strings
    exclude_set = set()
    for f in exclude_fields:
        if isinstance(f, ScopingField):
            exclude_set.add(str(f.value).lower())
        elif isinstance(f, str):
            exclude_set.add(f.lower())
    
    # Helper to get mapped field name
    def get_field_name(field: Union[ScopingField, str]) -> str:
        """Get actual table column name, considering field_mapping."""
        field_key = field if isinstance(field, ScopingField) else field
        if field_key in field_mapping:
            return str(field_mapping[field_key])
        if isinstance(field, ScopingField):
            return str(field.value)
        return str(field)
    
    conditions = []
    
    # LEVEL 0: sector_records_categories
    if ScopingField.SECTOR_RECORDS_CATEGORY.value not in exclude_set:
        if component.applicable_sector_records_categories:
            categories = component.applicable_sector_records_categories
            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(",")]
            
            if categories and categories != ["all"]:
                field_name = get_field_name(ScopingField.SECTOR_RECORDS_CATEGORY)
                categories_sql = ", ".join([f"'{cat}'" for cat in categories])
                conditions.append(f"{subject_table_alias}.{field_name} IN ({categories_sql})")
    
    # LEVEL 1: subject_categories
    if ScopingField.SUBJECT_CATEGORY.value not in exclude_set:
        if component.applicable_subject_categories:
            subject_cats = component.applicable_subject_categories
            if isinstance(subject_cats, str):
                subject_cats = [c.strip() for c in subject_cats.split(",")]
            
            if subject_cats and subject_cats != ["all"]:
                field_name = get_field_name(ScopingField.SUBJECT_CATEGORY)
                cats_sql = ", ".join([f"'{cat}'" for cat in subject_cats])
                conditions.append(f"{subject_table_alias}.{field_name} IN ({cats_sql})")
    
    # LEVEL 2: applicability_constraints
    if component.applicability_constraints:
        constraints = component.applicability_constraints
        if isinstance(constraints, str):
            import json
            constraints = json.loads(constraints)
        
        if constraints:
            constraint_conditions = _parse_constraints_to_sql(
                constraints, subject_table_alias, exclude_set, field_mapping
            )
            if constraint_conditions:
                conditions.append(constraint_conditions)
    
    # LEVEL 3: manual_subjects_overrides
    if ScopingField.SUBJECT_ID.value not in exclude_set:
        if component.manual_subjects_overrides:
            overrides = component.manual_subjects_overrides
            if isinstance(overrides, str):
                import json
                overrides = json.loads(overrides)
            
            if overrides:
                field_name = get_field_name(ScopingField.SUBJECT_ID)
                
                # Whitelist (include_subjects)
                if "include_subjects" in overrides and overrides["include_subjects"]:
                    include_list = overrides["include_subjects"]
                    include_sql = ", ".join([f"'{sid}'" for sid in include_list])
                    conditions.append(f"{subject_table_alias}.{field_name} IN ({include_sql})")
                
                # Blacklist (exclude_subjects)
                if "exclude_subjects" in overrides and overrides["exclude_subjects"]:
                    exclude_list = overrides["exclude_subjects"]
                    exclude_sql = ", ".join([f"'{sid}'" for sid in exclude_list])
                    conditions.append(f"{subject_table_alias}.{field_name} NOT IN ({exclude_sql})")
    
    # Pulse status filtering
    if ScopingField.PULSE_STATUS.value not in exclude_set:
        field_name = get_field_name(ScopingField.PULSE_STATUS)
        
        if pulse_statuses_to_have:
            # Convert enum to string values
            statuses = [
                s.value if isinstance(s, ObjectOverallStatus) else s
                for s in pulse_statuses_to_have
            ]
            status_sql = ", ".join([f"'{s}'" for s in statuses])
            conditions.append(f"{subject_table_alias}.{field_name} IN ({status_sql})")
        
        if pulse_statuses_to_avoid:
            # Convert enum to string values
            statuses = [
                s.value if isinstance(s, ObjectOverallStatus) else s
                for s in pulse_statuses_to_avoid
            ]
            status_sql = ", ".join([f"'{s}'" for s in statuses])
            conditions.append(f"{subject_table_alias}.{field_name} NOT IN ({status_sql})")
    
    return " AND ".join(conditions) if conditions else "TRUE"


def _parse_constraints_to_sql(
    constraints: Dict[str, Any],
    table_alias: str,
    exclude_set: Optional[set] = None,
    field_mapping: Optional[Dict] = None
) -> str:
    """
    Parse LEVEL 2 JSON constraints into SQL WHERE conditions.
    
    Supports:
    - IN: {"industry": ["software", "semiconductors"]}
    - NOT_IN: {"industry": {"operator": "NOT_IN", "values": [...]}}
    - GT/GTE/LT/LTE: {"market_cap": {"operator": "GT", "value": 10000000000}}
    - BETWEEN: {"pe_ratio": {"operator": "BETWEEN", "values": [10, 25]}}
    - EQUALS: {"region": {"operator": "EQUALS", "value": "north_america"}}
    - OR logic: {"_logic": "OR", "constraint_groups": [...]}
    
    Args:
        constraints: Dictionary of constraint definitions
        table_alias: SQL table alias
        exclude_set: Set of field names to skip
        field_mapping: Map of component field names to table column names
    """
    exclude_set = exclude_set or set()
    field_mapping = field_mapping or {}
    
    # Helper to get mapped field name
    def get_field_name(field: str) -> str:
        """Get actual table column name, considering field_mapping."""
        # Check if field matches an enum value
        for filter_field in ScopingField:
            if filter_field.value == field.lower():
                if filter_field in field_mapping:
                    return field_mapping[filter_field]
                return field
        # Not an enum, return as-is or mapped
        return field_mapping.get(field, field)
    
    if "_logic" in constraints and constraints["_logic"] == "OR":
        # Handle OR logic
        or_conditions = []
        for group in constraints.get("constraint_groups", []):
            group_sql = _parse_constraints_to_sql(group, table_alias, exclude_set, field_mapping)
            if group_sql:
                or_conditions.append(f"({group_sql})")
        return " OR ".join(or_conditions) if or_conditions else ""
    
    conditions = []
    
    for field, constraint in constraints.items():
        if field in ["_logic", "constraint_groups"]:
            continue  # Skip meta fields
        
        # Skip excluded fields
        if field.lower() in exclude_set:
            continue
        
        # Get mapped field name
        mapped_field = get_field_name(field)
        
        # Simple IN (default)
        if isinstance(constraint, list):
            values_sql = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in constraint])
            conditions.append(f"{table_alias}.{mapped_field} IN ({values_sql})")
        
        # Operator-based constraints
        elif isinstance(constraint, dict) and "operator" in constraint:
            operator = constraint["operator"]
            
            if operator == "IN":
                values = constraint.get("values", [])
                values_sql = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
                conditions.append(f"{table_alias}.{mapped_field} IN ({values_sql})")
            
            elif operator == "NOT_IN":
                values = constraint.get("values", [])
                values_sql = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in values])
                conditions.append(f"{table_alias}.{mapped_field} NOT IN ({values_sql})")
            
            elif operator == "EQUALS":
                value = constraint.get("value")
                value_sql = f"'{value}'" if isinstance(value, str) else str(value)
                conditions.append(f"{table_alias}.{mapped_field} = {value_sql}")
            
            elif operator == "GT":
                value = constraint.get("value")
                conditions.append(f"{table_alias}.{mapped_field} > {value}")
            
            elif operator == "GTE":
                value = constraint.get("value")
                conditions.append(f"{table_alias}.{mapped_field} >= {value}")
            
            elif operator == "LT":
                value = constraint.get("value")
                conditions.append(f"{table_alias}.{mapped_field} < {value}")
            
            elif operator == "LTE":
                value = constraint.get("value")
                conditions.append(f"{table_alias}.{mapped_field} <= {value}")
            
            elif operator == "BETWEEN":
                values = constraint.get("values", [])
                if len(values) == 2:
                    conditions.append(f"{table_alias}.{mapped_field} BETWEEN {values[0]} AND {values[1]}")
    
    return " AND ".join(conditions)


def count_applicable_subjects(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    bq_client,
    subject_table_id: str
) -> int:
    """
    Count how many subjects the component is applicable to.
    
    Args:
        component: AI component with applicability constraints
        bq_client: BigQuery client instance
        subject_table_id: Full BigQuery table ID (e.g., "project.dataset.table")
    
    Returns:
        Count of applicable subjects
    
    Example:
        >>> from google.cloud import bigquery
        >>> client = bigquery.Client(project="data-platform-436809")
        >>> persona = get_persona("tech_growth_specialist")
        >>> count = count_applicable_subjects(
        ...     persona,
        ...     client,
        ...     "data-platform-436809.staging__dp_oracle_fincore__controls.dim_fincore_market_assets"
        ... )
        >>> print(f"Applicable to {count} subjects")
    """
    where_clause = generate_bigquery_where_clause(component, "s")
    query = f"""
        SELECT COUNT(*) as count
        FROM `{subject_table_id}` s
        WHERE {where_clause}
    """
    
    result = bq_client.query(query).result()
    for row in result:
        return row["count"]
    return 0


def fetch_applicable_subjects(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    bq_client,
    subject_table_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all subjects the component is applicable to.
    
    Args:
        component: AI component with applicability constraints
        bq_client: BigQuery client instance
        subject_table_id: Full BigQuery table ID
        limit: Optional limit on number of results
    
    Returns:
        List of subject dictionaries
    
    Example:
        >>> subjects = fetch_applicable_subjects(
        ...     persona,
        ...     client,
        ...     "data-platform-436809.staging__dp_oracle_fincore__controls.dim_fincore_market_assets",
        ...     limit=100
        ... )
        >>> print(f"Found {len(subjects)} applicable subjects")
        >>> for subject in subjects:
        ...     print(f"  - {subject['subject_id']}: {subject['subject_name']}")
    """
    where_clause = generate_bigquery_where_clause(component, "s")
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
        SELECT s.*
        FROM `{subject_table_id}` s
        WHERE {where_clause}
        {limit_clause}
    """
    
    result = bq_client.query(query).result()
    return [dict(row) for row in result]


def validate_component_scope(
    component: Union[AIInputFormat, AIOutputFormat, AnalystPersona],
    bq_client,
    subject_table_id: str
) -> Dict[str, Any]:
    """
    Validate the applicability scope of a component before deployment.
    
    Returns statistics about the component's reach:
    - Total subjects in database
    - Subjects passing each filtering level
    - Final applicable count
    - Coverage percentage
    
    Args:
        component: AI component to validate
        bq_client: BigQuery client instance
        subject_table_id: Full BigQuery table ID
    
    Returns:
        Dictionary with validation statistics
    
    Example:
        >>> stats = validate_component_scope(persona, client, table_id)
        >>> print(f"Coverage: {stats['coverage_pct']:.2f}%")
        >>> print(f"Applicable subjects: {stats['final_count']}")
    """
    # Total subjects
    total_query = f"SELECT COUNT(*) as count FROM `{subject_table_id}`"
    total_result = bq_client.query(total_query).result()
    total_count = next(total_result)["count"]
    
    # Applicable subjects
    applicable_count = count_applicable_subjects(component, bq_client, subject_table_id)
    
    coverage_pct = (applicable_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "total_subjects": total_count,
        "final_count": applicable_count,
        "coverage_pct": coverage_pct,
        "component_id": getattr(component, "ai_input_format_id", None) or 
                       getattr(component, "ai_output_format_id", None) or 
                       getattr(component, "analyst_persona_id", None),
        "component_name": getattr(component, "format_name", None) or 
                         getattr(component, "persona_name", None)
    }
