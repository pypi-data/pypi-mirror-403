import json
from typing import Optional, List, Union, Dict, Any
from pydantic import Field, field_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import (
    CognitiveStyle,
    Mood,
    ThinkingHorizon,
    AnalystModeCategory
)
from ipulse_shared_base_ftredge.enums.enums_pulse import SubjectCategory, SectorRecordsCategory

class AnalystPersona(BaseVersionedModel):
    """
    DNA v2 Analyst Persona - Defines WHO the analyst is (pure identity).
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.analyst_personas
    """
    # Core Identity
    persona_id: str = Field(..., description="Unique persona identifier (UUID from seed phrase). Primary Key.")
    persona_name: str = Field(..., description="Generated name: persona_character__persona_archetype (e.g., 'warren_buffett__the_chairman').")
    persona_character: str = Field(..., description="Well-known character: warren_buffett, ray_dalio, cathie_wood, superintelligence.")
    persona_character_display_name: str = Field(..., description="Character display name (e.g., 'Warren Buffett', 'Ray Dalio').")
    persona_archetype: str = Field(..., description="Archetype derived from variant+horizons+modes: the_supercomputer, the_chairman, the_glitch.")
    persona_archetype_display_name: str = Field(..., description="Archetype display name (e.g., 'The Supercomputer', 'The Chairman').")
    persona_identity_display_brief: str = Field(..., description="Brief identity summary for UI display.")
    
    # Cognitive Style Dimensions
    primary_cognitive_style: CognitiveStyle = Field(..., description="Core investment philosophy (e.g., 'value_purist'). Matches CognitiveStyle enum.")
    primary_cognitive_style_display_name: str = Field(..., description="Display name for primary style (e.g., 'Value Purist').")
    secondary_cognitive_styles: Optional[Union[List[CognitiveStyle], str]] = Field(default=None, description="Complementary styles (0-2): contrarian, quant_scientist. Stored as comma-separated in BigQuery.")
    secondary_cognitive_styles_display_names: Optional[str] = Field(default=None, description="Comma-separated display names.")
    variant: str = Field(..., description="Variant identifier (e.g., 'minimal1', 'simple1', 'standard', 'extreme'). Check PersonaVariant enum for inspiration.")
    variant_display_name: str = Field(..., description="Variant display name (e.g., 'Minimal Definition 1', 'Standard', 'Extreme').")
    moods: Union[List[Mood], str] = Field(..., description="List of moods: aggressive, fearful, greedy, balanced, sad. Stored as comma-separated in BigQuery.")
    moods_display_names: str = Field(..., description="Comma-separated mood display names.")
    
    # === 8-LEVEL APPLICABILITY ARCHITECTURE (DNA v2) ===
    
    # --- SUBJECT APPLICABILITY (4 levels - WHO/WHAT) ---
    
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
        description="LEVEL 3: Explicit include/exclude lists. Keys: 'include_subjects', 'exclude_subjects'. Overrides all other rules. None/{} = no overrides. Stored as JSON string in BigQuery."
    )
    
    # --- HORIZON APPLICABILITY (2 levels - WHEN/HOW LONG) ---
    
    # LEVEL 4: Thinking horizons (categorical)
    applicable_thinking_horizons: Optional[Union[List[ThinkingHorizon], str]] = Field(
        default=None,
        description="LEVEL 4: Horizons analyst can analyze (TACTICAL_INVESTMENT, STRATEGIC_INVESTMENT, etc.). None/[] = ALL horizons (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 5: Horizon constraints (numeric/temporal fine-tuning)
    applicable_horizon_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 5: Horizon constraints (min_horizon_value, max_horizon_value, min_step_value with timeunits). None/{} = no constraints (universal). Auto-derives from applicable_thinking_horizons if not specified. Stored as JSON string in BigQuery."
    )
    
    # --- EXECUTION APPLICABILITY (2 levels - HOW) ---
    
    # LEVEL 6: Analyst modes (categorical)
    applicable_analyst_modes: Optional[Union[List[Any], str]] = Field(
        default=None,
        description="LEVEL 6: Modes analyst can use (THINKER, SCHOLAR, RESEARCHER, QUANT). None/[] = ALL modes (universal). Stored as comma-separated in BigQuery."
    )
    
    # LEVEL 7: Model constraints (merged: filtering + capabilities)
    applicable_model_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 7: Model constraints including both filtering (compatible_model_families, min_context_window) AND required capabilities (web_search, json_mode, vision, function_calling). None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # Human-Readable Applicability Summary
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of persona applicability. Examples: 'All equity assets', 'Long-term fundamental analysis', 'Tech sector specialist', 'Universal (all contexts)'."
    )
    
    # Persona Definition (THE CORE PROMPT)
    analyst_persona_definition: str = Field(..., description="Complete character description - THE prompt defining analyst personality.")
    
    @field_validator('secondary_cognitive_styles', 'moods', 'applicable_thinking_horizons', 'applicable_analyst_modes',
                     'applicable_sector_records_categories', 'applicable_subject_categories', mode='before')
    @classmethod
    def parse_comma_separated_enums(cls, v):
        """Convert comma-separated strings from BigQuery to lists of enum values."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('secondary_cognitive_styles', 'moods', 'applicable_thinking_horizons', 'applicable_analyst_modes',
                     'applicable_sector_records_categories', 'applicable_subject_categories', mode='after')
    @classmethod
    def serialize_enums_to_string(cls, v):
        """Convert lists of enums back to comma-separated strings for BigQuery storage."""
        if v is None or (isinstance(v, list) and len(v) == 0):
            return None
        if isinstance(v, list):
            # Handle both enum objects and strings
            return ','.join([str(item.value) if hasattr(item, 'value') else str(item) for item in v])
        return v
    
    @field_validator('applicability_constraints', 'applicability_manual_subjects_overrides', 'applicable_horizon_constraints', 
                     'applicable_model_constraints', mode='before')
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
    
    @field_validator('applicability_constraints', 'applicability_manual_subjects_overrides', 'applicable_horizon_constraints',
                     'applicable_model_constraints', mode='after')
    @classmethod
    def serialize_to_json(cls, v):
        """Convert dicts back to JSON strings for BigQuery storage."""
        if v is None or (isinstance(v, dict) and len(v) == 0):
            return None
        if isinstance(v, dict):
            return json.dumps(v)
        return v
