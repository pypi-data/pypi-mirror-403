"""
Task Config with Embedded Prompt Assembly - DNA v2 Architecture.

This module defines the new task configuration architecture where prompt assembly
is embedded as a JSON field, eliminating the need for separate assembly_variant table.

AUTHOR: Russlan Ramdowar; russlan@ftredge.com
CREATED: 2026-01-09
"""

from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import (
    PredictionTaskType,
    DataSourcingApproach,
    AnalystModeCategory,
    ThinkingHorizon,
    AIAssemblyComponentType
)
from ipulse_shared_base_ftredge.enums.enums_pulse import (
    SectorRecordsCategory,
    SubjectCategory
)
import json
import hashlib


class PromptAssemblyComponent(BaseModel):
    """Single component in prompt assembly.
    
    Represents one building block of the complete prompt structure.
    Contains denormalized display fields for catalog optimization.
    """
    component_type: AIAssemblyComponentType = Field(..., description="Component type (analyst_persona, general_guidelines, task_instructions, etc.)")
    component_id: str = Field(..., description="UUID from source table (ai_analyst_personas, ai_input_formats, ai_assembly_components, etc.)")
    component_name: str = Field(..., description="Technical component name for runtime resolution")
    component_display_name: str = Field(..., description="Human-readable display name for catalog UI")
    component_description: Optional[str] = Field(default=None, description="Short summary for UI tooltips/previews")
    variant: Optional[str] = Field(default=None, description="Optional variant hash (e.g., io_format_variant_hash)")
    major_version: Optional[int] = Field(default=None, description="Major version for version pinning (None = use latest)")
    minor_version: Optional[int] = Field(default=None, description="Minor version for version pinning (None = use latest)")


class PromptAssembly(BaseModel):
    """Complete prompt assembly definition.
    
    Stored as JSON string in BigQuery ai_task_configs.prompt_assembly column.
    Contains all components needed to construct the full prompt at runtime.
    """
    # Assembly metadata
    assembly_id: str = Field(..., description="Unique identifier for this assembly configuration")
    assembly_name: str = Field(..., description="Human-readable assembly name (e.g., 'content_driven_equity_price_forecast_v1')")
    assembly_type: str = Field(..., description="Assembly pattern type: system_instruction_driven, content_driven, hybrid")
    assembly_variant_hash: str = Field(..., description="Auto-calculated from all component IDs + variants (full 64-char SHA256)")
    
    # Component lists
    system_instruction_components: List[PromptAssemblyComponent] = Field(..., description="Components for system message (personas, guidelines, output instructions)")
    prompt_content_components: List[PromptAssemblyComponent] = Field(..., description="Components for user prompt content (task instructions, subject context, input data)")
    
    def calculate_variant_hash(self) -> str:
        """Auto-calculate hash from all component IDs and their variants.
        
        Uses full 64-char SHA256 for maximum collision resistance.
        Includes variant hashes to differentiate assemblies with same components but different versions.
        
        Returns:
            str: Full 64-character SHA256 hex digest
        """
        # Build hierarchical structure: {system: [(id, variant)], content: [(id, variant)]}
        hash_structure = {
            'system': sorted([
                (c.component_id, c.variant or '') 
                for c in self.system_instruction_components
            ]),
            'content': sorted([
                (c.component_id, c.variant or '') 
                for c in self.prompt_content_components
            ])
        }
        
        # Generate deterministic JSON and hash (full 64 chars)
        hash_input = json.dumps(hash_structure, sort_keys=True)
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    @model_validator(mode='before')
    @classmethod
    def auto_calculate_hash(cls, values):
        """Auto-calculate assembly_variant_hash if not provided."""
        if values.get('assembly_variant_hash'):
            return values
        
        # Temporarily create PromptAssembly instance to calculate hash
        system_comps = values.get('system_instruction_components', [])
        content_comps = values.get('prompt_content_components', [])
        
        if not system_comps and not content_comps:
            return values
        
        # Parse components if they're dicts
        system_instruction_components = [
            PromptAssemblyComponent(**c) if isinstance(c, dict) else c 
            for c in system_comps
        ]
        prompt_content_components = [
            PromptAssemblyComponent(**c) if isinstance(c, dict) else c 
            for c in content_comps
        ]
        
        # Build hash structure
        hash_structure = {
            'system': sorted([
                (c.component_id, c.variant or '') 
                for c in system_instruction_components
            ]),
            'content': sorted([
                (c.component_id, c.variant or '') 
                for c in prompt_content_components
            ])
        }
        
        hash_input = json.dumps(hash_structure, sort_keys=True)
        values['assembly_variant_hash'] = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return values


class AITaskConfig(BaseVersionedModel):
    """Task configuration with embedded prompt assembly - DNA v2 Architecture.
    
    Replaces the old ai_analysts table and eliminates separate assembly_variant table.
    Prompt assembly is embedded as JSON for flexibility and catalog optimization.
    
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.ai_task_configs
    
    JSON fields stored as JSON strings in BigQuery but represented as Dict/List in Python.
    """
    # Core Identifiers
    task_config_id: str = Field(..., description="Unique identifier (UUID). Primary Key.")
    task_config_name: str = Field(..., description="Human-readable task config name")
    task_executed_in_batch: bool = Field(..., description="Whether task is executed in batch mode (True) or single-request mode (False)")
    
    # AI Analyst Reference (denormalized for catalog display)
    ai_analyst_id: str = Field(..., description="Foreign Key to ai_analysts table")
    ai_analyst_name: str = Field(..., description="Denormalized analyst name for catalog queries")
    analyst_mode_id: str = Field(..., description="Foreign Key to ai_analyst_modes table (source of mode_sdk_params)")
    analyst_mode_name: str = Field(..., description="Denormalized mode name (e.g., standard_deep_thinker)")
    
    # Model Configuration
    model_sdk_api_reference: str = Field(..., description="Model SDK identifier (google_genai, openai, anthropic)")
    model_version_sdk_api_reference: str = Field(..., description="Model version reference in SDK (gemini-2.0-flash-exp, gpt-4, claude-3.5-sonnet)")
    model_sdk_params: Optional[Union[dict, str]] = Field(
        default=None,
        description="SDK-specific parameters (temperature, tools, thinking config, etc.). Stored as JSON string in BigQuery."
    )
    
    # Prompt Assembly (JSON string in BigQuery, PromptAssembly object in Python)
    prompt_assembly: Union[PromptAssembly, str] = Field(
        ...,
        description="Complete prompt assembly definition with all components. Stored as JSON string in BigQuery."
    )
    
    # Pipeline Metadata
    task_type: PredictionTaskType = Field(..., description="price_forecast, investment_thesis, risk_assessment. Matches PredictionTaskType enum.")
    input_data_sourcing_approach: DataSourcingApproach = Field(..., description="Pipeline batching group (equity_comprehensive, crypto_market_data). Determines subject grouping.")
    
    # Forecast Specification (from output format)
    forecast_horizon_value: Optional[int] = Field(
        default=None,
        description="Forecast horizon value (e.g., 5 for 5-year forecast). Extracted from output format."
    )
    forecast_horizon_unit: Optional[str] = Field(
        default=None,
        description="Forecast horizon unit (YEAR, MONTH, DAY). Extracted from output format."
    )
    forecast_timeseries_step_value: Optional[int] = Field(
        default=None,
        description="Forecast timeseries step value (e.g., 6 for 6-month steps). Extracted from output format."
    )
    forecast_timeseries_step_unit: Optional[str] = Field(
        default=None,
        description="Forecast timeseries step unit (YEAR, MONTH, DAY). Extracted from output format."
    )
    
    # === 4-LEVEL APPLICABILITY ARCHITECTURE (Auto-calculated from prompt_assembly) ===
    # DIMENSION 1: SUBJECT APPLICABILITY (4 levels)
    applicable_sector_records_categories: Optional[Union[List[SectorRecordsCategory], str]] = Field(
        default=None,
        description="LEVEL 0: Data types (MARKET, FUNDAMENTAL, EVENT). None/[] = ALL categories. Stored as comma-separated in BigQuery."
    )
    
    applicable_subject_categories: Optional[Union[List[SubjectCategory], str]] = Field(
        default=None,
        description="LEVEL 1: Asset classes (EQUITY, INDEX, ETF, CRYPTO). None/[] = ALL categories. Stored as comma-separated in BigQuery."
    )
    
    applicability_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 2: Fine-grained filtering (industry, region, tier). None/{} = no constraints. Stored as JSON string in BigQuery."
    )
    
    applicability_manual_subjects_overrides: Optional[Union[Dict[str, List[str]], str]] = Field(
        default=None,
        description="LEVEL 3: Explicit include/exclude lists. Keys: 'include_subjects', 'exclude_subjects'. None/{} = no overrides. Stored as JSON string in BigQuery."
    )
    
    # Auto-calculated Applicability Metadata
    applicability_calculated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when applicability was auto-calculated from prompt_assembly components"
    )
    
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of task config applicability (e.g., 'EQUITY market assets, 1-30 day horizons')"
    )
    
    # Validators for JSON/List serialization
    @field_validator('prompt_assembly', 'model_sdk_params', 'applicability_constraints', 
                     'applicability_manual_subjects_overrides', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """Convert JSON strings from BigQuery to dicts/objects."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                # For prompt_assembly, convert to PromptAssembly object
                if isinstance(parsed, dict) and 'assembly_id' in parsed:
                    return PromptAssembly(**parsed)
                return parsed
            except json.JSONDecodeError:
                return v
        return v
    
    @field_validator('prompt_assembly', 'model_sdk_params', 'applicability_constraints',
                     'applicability_manual_subjects_overrides', mode='after')
    @classmethod
    def serialize_to_json(cls, v):
        """Convert dicts/objects back to JSON strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, dict) and len(v) == 0:
            return None
        if isinstance(v, PromptAssembly):
            return json.dumps(v.model_dump())
        if isinstance(v, dict):
            return json.dumps(v)
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories', mode='after')
    @classmethod
    def serialize_lists_to_string(cls, v):
        """Convert lists back to comma-separated strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, list) and len(v) == 0:
            return None
        if isinstance(v, list):
            # Convert enum members to string values if necessary
            return ','.join([str(item.value) if hasattr(item, 'value') else str(item) for item in v])
        return v
