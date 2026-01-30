from typing import Optional, Union, List, Dict
import json
from pydantic import Field, field_validator, model_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import (
    AnalystModeCategory,
    ThinkingLevel,
    CreativityLevel,
    WebSearchMode,
    RagRetrievalMode
)

class AIAnalystMode(BaseVersionedModel):
    """
    Represents the 'HOW' of the AI Analyst - their execution capabilities and tools.
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.ai_analyst_modes
    """
    analyst_mode_id: str = Field(..., description="Unique identifier for the analyst mode (e.g., 'thinker__standard_high_depth'). Primary Key.")
    analyst_mode_name: str = Field(..., description="Technical name of the analyst mode (e.g., 'thinker__standard_high_depth').")
    analyst_mode_display_name: str = Field(..., description="Human-readable distinct display name for this specific mode (e.g., 'Standard Thinker (High Depth)').")
    analyst_mode_category: AnalystModeCategory = Field(..., description="The high-level mode category (e.g., 'thinker'). Matches AnalystModeCategory enum.")
    analyst_mode_category_display_name: str = Field(..., description="Human-readable display name for the category (e.g., 'Thinker').")
    variant: Optional[str] = Field(None, description="Variant identifier for specific configurations (e.g. 'deep_thinking_standard_creativity_1').")
    analyst_mode_instructions: str = Field(..., description="Prompt text defining the mode's behavioral instructions.")
    web_search: bool = Field(..., description="Whether web search capability is enabled.")
    web_search_mode: Optional[WebSearchMode] = Field(None, description="The intensity of web search (e.g., 'standard', 'deep'). Required if web_search is True.")
    rag_search: bool = Field(..., description="Whether RAG (Retrieval Augmented Generation) capability is enabled.")
    rag_retrieval_mode: Optional[RagRetrievalMode] = Field(None, description="The precision of RAG retrieval (e.g., 'standard', 'precise'). Required if rag_search is True.")
    thinking_level: ThinkingLevel = Field(..., description="The depth of reasoning required (e.g., 'fast', 'high', 'deep'). Matches ThinkingLevel enum.")
    creativity_level: CreativityLevel = Field(..., description="The creativity/temperature setting (e.g., 'deterministic', 'balanced', 'creative'). Matches CreativityLevel enum.")
    
    # Model Compatibility
    compatible_model_specs: Optional[Union[List[str], str]] = Field(
        default=None,
        description="List of compatible model_spec_ids. None = ALL models compatible. Stored as comma-separated in BigQuery."
    )
    
    # Standard Model Parameters (SDK-agnostic)
    model_params: Optional[Union[Dict, str]] = Field(
        default=None,
        description="Standard model parameters (temperature, max_tokens, top_p, top_k, seed, etc.). Runtime pipeline translates to SDK-specific params. Stored as JSON string in BigQuery."
    )
    
    @model_validator(mode='after')
    def validate_tool_modes(self):
        """Ensure tool modes are set if tools are enabled."""
        if self.web_search and self.web_search_mode is None:
            raise ValueError("web_search_mode must be set when web_search is True")
        if self.rag_search and self.rag_retrieval_mode is None:
            raise ValueError("rag_retrieval_mode must be set when rag_search is True")
        return self
    
    @field_validator('compatible_model_specs', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None:
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('compatible_model_specs', mode='after')
    @classmethod
    def serialize_to_string(cls, v):
        """Convert lists back to comma-separated strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, list):
            return ','.join(v)
        return v
    
    @field_validator('model_params', mode='before')
    @classmethod
    def parse_model_params(cls, v):
        """Parse JSON string from BigQuery into dict."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator('model_params', mode='after')
    @classmethod
    def serialize_model_params(cls, v):
        """Convert dict back to JSON string for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, dict):
            return json.dumps(v)
        return v
