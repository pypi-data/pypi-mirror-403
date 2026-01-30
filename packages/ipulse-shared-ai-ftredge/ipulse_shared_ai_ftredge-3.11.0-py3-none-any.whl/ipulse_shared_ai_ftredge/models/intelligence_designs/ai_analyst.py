from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
from pydantic import Field, field_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import ThinkingHorizon, AnalystModeCategory
from ipulse_shared_base_ftredge.enums.enums_pulse import SectorRecordsCategory, SubjectCategory

class AIAnalyst(BaseVersionedModel):
    """
    Represents an instantiation of an Analyst Persona with a specific Model and Assembly Variant.
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.ai_analysts
    """
    analyst_id: str = Field(..., description="Unique identifier for the instantiated analyst. Primary Key.")
    analyst_name: str = Field(..., description="Derived name: persona_name + model_spec_name + optional model_version_name.")
    
    # Core Identity Components
    analyst_persona_id: str = Field(..., description="Foreign Key to analyst_personas - WHO the analyst is.")
    model_spec_id: str = Field(..., description="Foreign Key to ai_model_specifications - WHICH MODEL.")
    model_spec_name: str = Field(..., description="Model spec name for display.")
    model_version_id: str = Field(..., description="Foreign Key to ai_model_versions - WHICH VERSION.")
    model_version_name: str = Field(..., description="Model version name for display.")
    model_training_config_id: Optional[str] = Field(default=None, description="Foreign Key to training config (for internal models, None for external LLMs).")
    model_version_agnostic: bool = Field(..., description="If True, excludes model_version_id from analyst_id seed phrase.")
    
    # === 8-LEVEL AUTO-CALCULATED APPLICABILITY ARCHITECTURE ===
    # These fields are automatically calculated based on intersection of:
    # - Analyst Persona applicability
    # - Model Spec/Version capabilities
    # - Assembly Variant constraints
    
    # DIMENSION 1: SUBJECT APPLICABILITY (4 levels)
    # LEVEL 0: Data type categorization (broadest filter)
    applicable_sector_records_categories: Optional[Union[List[SectorRecordsCategory], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Data types (MARKET, FUNDAMENTAL, EVENT, NEWSFEED, etc.). None/[] = ALL categories (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 1: Asset class categorization (broad filter, indexed)
    applicable_subject_categories: Optional[Union[List[SubjectCategory], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Asset classes (EQUITY, INDEX, ETF, CRYPTO, etc.). None/[] = ALL categories (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 2: Fine-grained constraints (flexible JSON)
    applicability_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Fine-grained filtering on industry, region, tier, numeric metrics. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # LEVEL 3: Manual subject overrides (explicit edge cases)
    applicability_manual_subjects_overrides: Optional[Union[Dict[str, List[str]], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Explicit include/exclude lists. Keys: 'include_subjects', 'exclude_subjects'. None/{} = no overrides (universal). Stored as JSON string in BigQuery."
    )
    
    # DIMENSION 2: HORIZON APPLICABILITY (2 levels)
    # LEVEL 4: Thinking horizon enumeration
    applicable_thinking_horizons: Optional[Union[List[ThinkingHorizon], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Thinking horizons (VERY_SHORT_TERM, SHORT_TERM, MEDIUM_TERM, etc.). None/[] = ALL horizons (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 5: Horizon numeric constraints
    applicable_horizon_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Numeric horizon bounds. Keys: min_horizon_value/timeunit, max_horizon_value/timeunit. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # DIMENSION 3: EXECUTION APPLICABILITY (2 levels)
    # LEVEL 6: Analyst mode enumeration
    applicable_analyst_modes: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="AUTO-CALCULATED from model version. Dict with 'single_request' and 'batch_request' keys. Can contain list of supported analyst modes or raw mode configuration. None/{} = ALL modes (universal). Stored as JSON string in BigQuery."
    )
    
    # LEVEL 7: Model execution constraints
    applicable_model_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="AUTO-CALCULATED: Model SDK constraints, modality support, performance requirements. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # Applicability Metadata
    applicability_calculated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when applicability fields were last calculated. Stored as TIMESTAMP in BigQuery."
    )
    
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of applicability (e.g., 'Equity only, MEDIUM_TERM, COMPREHENSIVE mode'). Stored as STRING in BigQuery."
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
                     'applicable_thinking_horizons', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories',
                     'applicable_thinking_horizons', mode='after')
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
    
    @field_validator('applicable_analyst_modes', mode='before')
    @classmethod
    def parse_analyst_modes_json(cls, v):
        """Convert JSON string from BigQuery to dict with single_request/batch_request keys."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v
    
    @field_validator('applicable_analyst_modes', mode='after')
    @classmethod
    def serialize_analyst_modes_to_json(cls, v):
        """Convert dict back to JSON string for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, dict) and len(v) == 0:
            return None
        if isinstance(v, dict):
            # Convert enum values to strings if needed
            result = {}
            for key, modes_list in v.items():
                if isinstance(modes_list, list):
                    result[key] = [str(mode.value) if hasattr(mode, 'value') else str(mode) for mode in modes_list]
                else:
                    result[key] = modes_list
            return json.dumps(result)
        return v
