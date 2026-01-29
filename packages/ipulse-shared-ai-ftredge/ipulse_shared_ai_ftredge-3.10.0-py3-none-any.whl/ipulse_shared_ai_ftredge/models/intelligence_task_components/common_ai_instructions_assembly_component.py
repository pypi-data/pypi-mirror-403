from typing import Optional, List, Dict, Any, Union, Literal
import json
from pydantic import Field, field_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import AIAssemblyComponentType, ThinkingHorizon, AnalystModeCategory
from ipulse_shared_base_ftredge.enums.enums_pulse import SectorRecordsCategory, SubjectCategory, ScopingField

class CommonAIInstructionsAssemblyComponent(BaseVersionedModel):
    """
    DNA v2 Assembly Component - Modular pieces of prompt construction.
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.common_ai_instructions_assembly_components
    
    Note: component_type uses AIAssemblyComponentType which includes both generic types 
    (general_guidelines, subject_context) and specific task types (task_generate_investment_thesis_...).
    """
    component_id: str = Field(..., description="Unique identifier for the component. Primary Key.")
    component_name: str = Field(..., description="Format: {component_type}__{specificity}__{content_resolution}__{variant?}. Examples: general_guidelines__equity__static, task_generate_investment_thesis_and_timeseries_close_price_pct_change_3y3m__market__minimal1__static.")
    component_type: AIAssemblyComponentType = Field(..., description="Type of component. Uses AIAssemblyComponentType enum which includes both generic types (general_guidelines, subject_context) and specific task types (task_generate_investment_thesis_and_timeseries_close_price_pct_change).")
    variant: str = Field(..., description="Variant distinguisher: standard, strict, lenient, verbose, concise.")
    
    # Human-Readable Applicability Summary
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of component applicability. Examples: 'All equity assets', 'Tech & Healthcare equities, market cap >$1B', 'Long-term horizons (>180 days)', 'Universal (all contexts)'."
    )
    
    # Instance Scoping Granularity & Content Resolution
    instance_scoping_granularity: Optional[ScopingField] = Field(
        default=None,
        description="Granularity level at which this component is scoped (SUBJECT_ID, SECTOR_RECORDS_CATEGORY, SUBJECT_CATEGORY, REGION, etc.). None = universal component."
    )
    content_resolution: Literal["static", "assembly_injection_template", "runtime_injection_template"] = Field(
        default="static",
        description="How component content is resolved: 'static' (fixed text), 'assembly_injection_template' (placeholders filled at assembly time), 'runtime_injection_template' (dynamic data inserted at execution time)."
    )
    
    # Content
    component_content: str = Field(..., description="Template with {{TABLE.FIELD}} placeholders or static text.")
    
    # === 8-LEVEL APPLICABILITY ARCHITECTURE ===
    # DIMENSION 1: SUBJECT APPLICABILITY (4 levels)
    # LEVEL 0: Data type categorization (broadest filter)
    applicable_sector_records_categories: Optional[Union[List[SectorRecordsCategory], str]] = Field(
        default=None,
        description="LEVEL 0: Data types (MARKET, FUNDAMENTAL, EVENT, NEWSFEED, etc.). None/[] = ALL categories (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 1: Asset class categorization (broad filter, indexed)
    applicable_subject_categories: Optional[Union[List[SubjectCategory], str]] = Field(
        default=None,
        description="LEVEL 1: Asset classes (EQUITY, INDEX, ETF, CRYPTO, etc.). None/[] = ALL categories (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 2: Fine-grained constraints (flexible JSON)
    applicability_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 2: Fine-grained filtering on industry, region, tier, numeric metrics. Supports operators: IN, NOT_IN, GT, LTE, BETWEEN. None/{} = no constraints (universal). Stored as JSON string in BigQuery. Keys match ScopingField enum values."
    )
    
    # LEVEL 3: Manual subject overrides (explicit edge cases)
    applicability_manual_subjects_overrides: Optional[Union[Dict[str, List[str]], str]] = Field(
        default=None,
        description="LEVEL 3: Explicit include/exclude lists. Keys: 'include_subjects', 'exclude_subjects'. Overrides all other rules. None/{} = no overrides (universal). Stored as JSON string in BigQuery."
    )
    
    # DIMENSION 2: HORIZON APPLICABILITY (2 levels)
    # LEVEL 4: Thinking horizon enumeration
    applicable_thinking_horizons: Optional[Union[List[ThinkingHorizon], str]] = Field(
        default=None,
        description="LEVEL 4: Thinking horizons (VERY_SHORT_TERM, SHORT_TERM, MEDIUM_TERM, etc.). None/[] = ALL horizons (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 5: Horizon numeric constraints
    applicable_horizon_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 5: Numeric horizon bounds. Keys: min_horizon_value/timeunit, max_horizon_value/timeunit, min_step_value/timeunit, max_step_value/timeunit. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # DIMENSION 3: EXECUTION APPLICABILITY (2 levels)
    # LEVEL 6: Analyst mode enumeration
    applicable_analyst_modes: Optional[Union[List[Any], str]] = Field(
        default=None,
        description="LEVEL 6: Analyst modes (COMPREHENSIVE, FOCUSED, QUICK, etc.). None/[] = ALL modes (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 7: Model execution constraints
    applicable_model_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 7: Model SDK constraints, modality support, performance requirements. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # Validators for serialization/deserialization
    @field_validator('applicability_constraints', 'applicability_manual_subjects_overrides', 
                     'applicable_horizon_constraints', 'applicable_model_constraints', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Convert JSON strings from BigQuery to dicts."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v
    
    @field_validator('applicability_constraints', 'applicability_manual_subjects_overrides', 
                     'applicable_horizon_constraints', 'applicable_model_constraints', mode='after')
    @classmethod
    def serialize_to_json(cls, v):
        """Convert dicts back to JSON strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, dict) and len(v) == 0:
            return None
        if isinstance(v, dict):
            return json.dumps(v)
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories',
                     'applicable_thinking_horizons', 'applicable_analyst_modes', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories',
                     'applicable_thinking_horizons', 'applicable_analyst_modes', mode='after')
    @classmethod
    def serialize_lists_to_string(cls, v):
        """Convert lists back to comma-separated strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        if isinstance(v, list):
            return ','.join([str(item.value) if hasattr(item, 'value') else str(item) for item in v])
        return v
