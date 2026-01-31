from typing import List, Optional, Dict, Any, Union
from pydantic import Field, field_validator, model_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_units import TimeUnit
from ipulse_shared_base_ftredge.enums.enums_analysts import PredictionTarget, ThinkingHorizon, AnalystModeCategory
from ipulse_shared_base_ftredge.enums.enums_data import DataModality, ModalityContentDynamics
from ipulse_shared_base_ftredge.enums.enums_pulse import SubjectCategory, SectorRecordsCategory
import json
import hashlib

class AIOutputFormat(BaseVersionedModel):
    """
    Defines WHAT structure the model produces and WHICH field groups are required.
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.ai_output_formats
    
    References schema_registry for validation. Handles field group filtering for dimensionality reduction.
    Comma-separated fields stored as strings in BigQuery but represented as List[str] in Python.
    JSON fields stored as JSON strings in BigQuery but represented as Dict in Python.
    """
    io_format_id: str = Field(..., description="Unique IO format identifier (UUID). Primary Key.")
    io_format_name: str = Field(..., description="Format name example : {subject_category}__{horizon}")
    io_format_display_name: str = Field(..., description="Human-readable display name.")
    variant: Optional[str] = Field(default=None, description="SHA256 of sorted field groups (for A/B testing). Auto-calculated if not provided.")
    
    # Schema Reference (Schema Registry Integration)
    content_type: str = Field(..., description="MIME type: application/json, text/plain, text/markdown")
    primary_data_modality: DataModality = Field(..., description="Primary data modality (TEXT, JSON_TEXT, TABULAR, etc.). Directly aligns with AIModelIOCapabilities.modalities.")
    encapsulated_data_modalities: Optional[Union[List[DataModality], str]] = Field(
        default=None,
        description="Encapsulated modalities (e.g., JSON_TEXT within TEXT). None/[] = no encapsulation. Stored as comma-separated in BigQuery."
    )
    content_dynamics: Optional[Union[List[ModalityContentDynamics], str]] = Field(
        default=None,
        description="Content dynamics (STATIC, TIMESERIES, STREAMING, etc.). None/[] = any dynamics. Stored as comma-separated in BigQuery."
    )
    output_schema_id: Optional[str] = Field(default=None, description="Foreign Key to schema_registry (required for application/json content_type).")
    output_schema_family: Optional[str] = Field(default=None, description="Parser routing: equity_invest_thesis_ts_num_rsk_drv")
    output_instructions: Optional[str] = Field(default=None, description="Multi-line text describing expected output format structure (horizon specs, timeseries specs, field requirements). Strongly linked 1:1 to output_schema_id.")
    
    # Field Groups (Pipeline Execution - Dimensionality Reduction)
    horizon_wide_field_groups: Optional[Union[List[str], str]] = Field(default=None, description="Field groups: investment_thesis_core, risk_analysis. Stored as comma-separated in BigQuery.")
    timeseries_field_groups: Optional[Union[List[str], str]] = Field(default=None, description="Field groups: price_forecast_core, confidence_intervals. Stored as comma-separated in BigQuery.")
    prediction_targets: Union[List[PredictionTarget], str] = Field(..., description="REQUIRED targets: close_price_pct_change, etc. Matches PredictionTarget enum. Stored as comma-separated in BigQuery.")
    
    # Timeseries Specification (Pipeline Execution)
    forecast_horizon_value: Optional[int] = Field(default=None, description="Business-friendly horizon: 1, 5, 3")
    forecast_horizon_unit: Optional[TimeUnit] = Field(default=None, description="Business-friendly unit: year, month, quarter. Matches TimeUnit enum.")
    forecast_timeseries_step_value: Optional[int] = Field(default=None, description="Number of forecast steps.")
    forecast_timeseries_step_unit: Optional[TimeUnit] = Field(default=None, description="Technical step unit: D, M, Q, Y. Matches TimeUnit enum.")
    
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
    # NOTE: Dict keys are filtering field names (industry, market_cap, region, etc.) defined in ScopingField enum.
    # Model uses Dict[str, Any] because data comes from BigQuery as JSON. Enum usage happens at application layer via get_field() helper.
    applicability_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 2: Fine-grained filtering on industry, region, tier, numeric metrics. Supports operators: IN, NOT_IN, GT, LTE, BETWEEN. None/{} = no constraints (universal). Stored as JSON string in BigQuery. Keys match ScopingField enum values."
    )
    
    # LEVEL 3: Manual subject overrides (explicit edge cases)
    # NOTE: Dict keys are fixed strings ('include_subjects', 'exclude_subjects'), NOT ScopingField enum members.
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
    
    # LEVEL 7: Model execution constraints (merged: output specs + capabilities)
    applicable_model_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 7: Model-specific output parameters (min_output_tokens, response_schema, etc.) + SDK constraints. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # Human-Readable Applicability Summary
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of output format applicability. Examples: 'All equity assets', 'Mixed JSON output with timeseries', 'Universal (all contexts)'."
    )
    
    @field_validator('applicable_model_constraints', 
                     'applicability_constraints', 'applicability_manual_subjects_overrides', 
                     'applicable_horizon_constraints', mode='before')
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
    
    @field_validator('applicable_model_constraints', 
                     'applicability_constraints', 'applicability_manual_subjects_overrides', 
                     'applicable_horizon_constraints', mode='after')
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
    
    @field_validator('horizon_wide_field_groups', 'timeseries_field_groups', 'prediction_targets',
                     'applicable_sector_records_categories', 'applicable_subject_categories',
                     'applicable_thinking_horizons', 'applicable_analyst_modes',
                     'encapsulated_data_modalities', 'content_dynamics', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    @model_validator(mode='before')
    @classmethod
    def auto_calculate_hash(cls, values):
        """
        Auto-calculate variant hash if not provided.
        
        Hash is based on structural components:
        - horizon_wide_field_groups
        - timeseries_field_groups
        - prediction_targets
        
        Applies case normalization (lowercase) and deterministic sorting.
        """
        # Skip if hash is already provided (e.g., when loading from DB)
        if values.get('variant'):
            return values
            
        hash_structure = {}
        
        # Helper to process list fields (handles list or comma-separated string)
        def process_field(field_name, key_name):
            val = values.get(field_name)
            if val:
                if isinstance(val, str):
                    # Handle comma-separated string
                    items = [x.strip() for x in val.split(',') if x.strip()]
                elif isinstance(val, list):
                    # Handle list (strings or enums)
                    items = [str(x.value) if hasattr(x, 'value') else str(x) for x in val]
                else:
                    items = []
                
                if items:
                    hash_structure[key_name] = sorted([x.lower() for x in items])

        process_field('horizon_wide_field_groups', 'horizon_wide')
        process_field('timeseries_field_groups', 'timeseries')
        process_field('prediction_targets', 'targets')
        
        # Generate hash
        hash_input = json.dumps(hash_structure, sort_keys=True)
        variant_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        values['variant'] = variant_hash
        return values    
    @field_validator('horizon_wide_field_groups', 'timeseries_field_groups', 'prediction_targets',
                     'applicable_sector_records_categories', 'applicable_subject_categories',
                     'applicable_thinking_horizons', 'applicable_analyst_modes',
                     'encapsulated_data_modalities', 'content_dynamics', mode='after')
    @classmethod
    def serialize_lists_to_string(cls, v):
        """Convert lists back to comma-separated strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        if isinstance(v, list):
            # Handle both enum objects and strings
            return ','.join([str(item.value) if hasattr(item, 'value') else str(item) for item in v])
        return v
