from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import Field, field_validator, model_validator, BaseModel
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import DataSourcingApproach, ThinkingHorizon, AnalystModeCategory
from ipulse_shared_base_ftredge.enums.enums_data import DataModality, ModalityContentDynamics
from ipulse_shared_base_ftredge.enums.enums_resources import DataResource
from ipulse_shared_base_ftredge.enums.enums_pulse import SubjectCategory, SectorRecordsCategory
import json
import hashlib

class DataSourceSpec(BaseModel):
    # === Data Source Type (REQUIRED) ===
    data_source_type: Literal["INMEMORY", "RAG", "ATTACHMENT"] = Field(..., description="How model SDK consumes this data")
    # INMEMORY: Fetched from DB/API → parsed → embedded in prompt text
    # RAG: Retrieved via vector search → injected into prompt
    # ATTACHMENT: File/chart/PDF → referenced via multimodal API (not embedded in text)
    
    # === Category (REQUIRED - for validation) ===
    category: Literal["historic", "analytics", "features", "prediction"] = Field(..., description="Must match data group category")
    # Ensures data group keys are correctly categorized for user transparency
    # Validated on save: keys in inmemory_input_data_groups["historic"] must have category="historic"
    
    # === Schema Registry Reference (REQUIRED) ===
    source_schema_id: Union[List[str], str] = Field(..., description="UUID(s) - Query schema_registry for base location/API details")
    source_schema_name: Union[List[str], str] = Field(..., description="Human-readable name(s) (e.g., 'fact_ohlcva_eod', 'api_macro_gdp')")
    
    # === Custom Query/Transformation Logic (OPTIONAL) ===
    source_columns: Optional[List[str]] = Field(default=None, description="Subset of columns to fetch")
    source_query: Optional[str] = Field(default=None, description="Custom SQL Template (overrides default SELECT *). Must use {{variable}} syntax.")
    query_parameters: Optional[List[str]] = Field(default=None, description="List of variables required in the query template (e.g., ['subject_id'])")
    max_rows_limit: Optional[int] = Field(default=100, description="Maximum number of rows to fetch to prevent context overflow")
    fallback_behavior: Literal["error", "skip", "use_default"] = Field(default="error", description="Behavior when data fetch fails")
    default_value: Optional[str] = Field(default=None, description="Default value to use if fallback_behavior is 'use_default'")
    
    data_transformation_logic: Optional[str] = Field(default=None, description="Aggregation, calculations, transformations")
                                                       # e.g., "CALCULATE_PCT_CHANGE(...)"
                                                       # e.g., "RESAMPLE_TO_MONTHLY(MEAN(close))"
    filters: Optional[List[str]] = Field(default=None, description="WHERE clauses")
    subject_filter_template: Optional[str] = Field(default=None, description="e.g., \"asset_id = '{subject_id}'\"")
    
    # === Presentation Template (OPTIONAL - for NARRATIVE_TEXT mode only) ===
    presentation_template: Optional[str] = Field(default=None, description="Micro-template: How to format this data group's raw data")
                                                  # e.g., "1-year price change: {value:+.1f}% ({currency})"
                                                  # e.g., "RSI (14-day): {value:.0f} ({interpretation})"
                                                  # Only needed for NARRATIVE_TEXT mode (LLMs)
                                                  # Not needed for TABULAR (raw numbers) or JSON (auto-structured)
    
    # === API-Specific Fields (OPTIONAL - for external APIs) ===
    api_endpoint: Optional[str] = Field(default=None, description="Specific endpoint path (appended to base URL from schema)")
                                        # e.g., "/v1/macro/gdp_growth", "/api/sentiment/analyze"
                                        # Schema registry stores base URL, this adds the specific path
    response_path: Optional[str] = Field(default=None, description="JSON path for API responses (e.g., '$.data.value')")
    cache_ttl_seconds: Optional[int] = Field(default=None, description="Cache duration for API responses")
    
    # === RAG-Specific Fields (OPTIONAL - only when data_source_type = "RAG") ===
    vector_index_name: Optional[str] = Field(default=None, description="Vector search index name")
    similarity_threshold: Optional[float] = Field(default=None, description="Minimum similarity score (0-1)")
    max_results: Optional[int] = Field(default=None, description="Maximum chunks to retrieve")
    
    # === ATTACHMENT-Specific Fields (OPTIONAL - only when data_source_type = "ATTACHMENT") ===
    attachment_format: Optional[DataResource] = Field(default=None, description="e.g., DataResource.GCS, DataResource.S3, DataResource.LOCAL_STORAGE")
    attachment_location_template: Optional[str] = Field(default=None, description="e.g., 'gs://bucket/charts/{subject_id}_chart.png'")

    @field_validator('source_schema_id', 'source_schema_name', mode='before')
    @classmethod
    def parse_list_fields(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v


class AIInputFormat(BaseVersionedModel):
    """
    Defines input data assembly - WHAT data gets assembled and HOW it's presented for AI model consumption.
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.ai_input_formats
    
    JSON fields stored as JSON strings in BigQuery but represented as Dict in Python.
    Comma-separated fields stored as strings in BigQuery but represented as List[str] in Python.
    """
    io_format_id: str = Field(..., description="Unique IO format identifier (UUID). Primary Key.")
    io_format_name: str = Field(..., description="Format name")
    io_format_display_name: str = Field(..., description="Human-readable display name.")
    data_sourcing_approach: DataSourcingApproach = Field(..., description="Defines how input data should be sourced and processed.")
    variant: Optional[str] = Field(default=None, description="SHA256 of sorted data group keys (auto-calculated). Full 64-char hash for collision resistance.")
    
    # Data Groups (JSON strings in BigQuery, Dict in Python)
    inmemory_input_data_groups: Union[Dict[str, List[str]], str] = Field(..., description="JSON with data group categories and field arrays. Stored as JSON string in BigQuery.")
    rag_data_groups: Optional[Union[Dict[str, List[str]], str]] = Field(None, description="JSON with RAG retrieval groups (optional). Stored as JSON string in BigQuery.")
    attachments_data_groups: Optional[Union[Dict[str, List[str]], str]] = Field(None, description="JSON with attachment groups (optional). Stored as JSON string in BigQuery.")
    
    # Content Type & Modality Architecture
    content_type: str = Field(..., description="MIME type: application/json, text/plain, text/markdown")
    primary_data_modality: DataModality = Field(..., description="Primary data modality (TEXT, TABULAR, JSON_TEXT, etc.). Directly aligns with AIModelIOCapabilities.modalities.")
    encapsulated_data_modalities: Optional[Union[List[DataModality], str]] = Field(
        default=None,
        description="Encapsulated modalities (e.g., TABULAR within TEXT). None/[] = no encapsulation. Stored as comma-separated in BigQuery."
    )
    content_dynamics: Optional[Union[List[ModalityContentDynamics], str]] = Field(
        default=None,
        description="Content dynamics (STATIC, TIMESERIES, STREAMING, etc.). None/[] = any dynamics. Stored as comma-separated in BigQuery."
    )
    
    # Assembly Instructions (mode-specific)
    narrative_wrapper_instructions: Optional[str] = Field(None, description="Optional macro narrative wrapper for NARRATIVE_TEXT mode.")
    json_wrapper_instructions: Optional[str] = Field(None, description="Optional custom schema for JSON mode.")
    tabular_wrapper_instructions: Optional[str] = Field(None, description="Instructions for TABULAR mode only.")
    
    # Data Source Mapping (JSON in BigQuery, Dict in Python)
    data_source_mapping: Union[Dict[str, DataSourceSpec], str] = Field(..., description="JSON mapping data groups to source configurations. Stored as JSON string in BigQuery.")
    
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
    
    # LEVEL 7: Model execution constraints (merged: filtering + capabilities)
    applicable_model_constraints: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="LEVEL 7: Model SDK constraints, modality support, performance requirements. None/{} = no constraints (universal). Stored as JSON string in BigQuery."
    )
    
    # Human-Readable Applicability Summary
    applicability_summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of input format applicability. Examples: 'All equity assets', 'Market data with numerical encapsulation', 'Universal (all contexts)'."
    )
    
    @field_validator('inmemory_input_data_groups', 'rag_data_groups', 'attachments_data_groups', 
                     'data_source_mapping', 'applicable_model_constraints', 
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
    
    @field_validator('inmemory_input_data_groups', 'rag_data_groups', 'attachments_data_groups', 
                     'data_source_mapping', 'applicable_model_constraints', 
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
            # Helper to convert values to dicts if they are Pydantic models
            def to_dict(obj):
                if isinstance(obj, BaseModel):
                    return obj.model_dump()
                return obj
            
            v_dict = {k: to_dict(val) for k, val in v.items()}
            return json.dumps(v_dict)
        return v
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories', 
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
    
    @field_validator('applicable_sector_records_categories', 'applicable_subject_categories', 
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
            # Convert enum members to string values if necessary
            return ','.join([str(item.value) if hasattr(item, 'value') else str(item) for item in v])
        return v
    
    @model_validator(mode='before')
    @classmethod
    def auto_calculate_hash(cls, values):
        """
        Auto-calculate variant hash if not provided.
        
        Hash is based on ALL data groups (inmemory, rag, attachments) with:
        - Group type differentiation (inmemory vs rag vs attachment)
        - Category preservation (historic, analytics, features, prediction)
        - Case normalization (lowercase)
        - Deterministic sorting (within each array, then combined)
        
        This ensures same data structure = same hash, different structure = different hash.
        """
        # Skip if hash is already provided (e.g., when loading from DB)
        if values.get('variant'):
            return values
        
        # Build hierarchical structure for hashing
        hash_structure = {}
        
        # Process inmemory groups
        inmemory = values.get('inmemory_input_data_groups')
        if inmemory:
            # Parse if it's a JSON string from DB
            if isinstance(inmemory, str):
                try:
                    inmemory = json.loads(inmemory)
                except json.JSONDecodeError:
                    pass
            
            if isinstance(inmemory, dict):
                hash_structure['inmemory'] = {
                    category: sorted([key.lower() for key in keys])
                    for category, keys in inmemory.items()
                }
        
        # Process RAG groups
        rag = values.get('rag_data_groups')
        if rag:
            if isinstance(rag, str):
                try:
                    rag = json.loads(rag)
                except json.JSONDecodeError:
                    pass
            
            if isinstance(rag, dict):
                hash_structure['rag'] = {
                    category: sorted([key.lower() for key in keys])
                    for category, keys in rag.items()
                }
        
        # Process attachment groups
        attachments = values.get('attachments_data_groups')
        if attachments:
            if isinstance(attachments, str):
                try:
                    attachments = json.loads(attachments)
                except json.JSONDecodeError:
                    pass
            
            if isinstance(attachments, dict):
                hash_structure['attachment'] = {
                    category: sorted([key.lower() for key in keys])
                    for category, keys in attachments.items()
                }
        
        # Generate hash (full 64 chars for maximum collision resistance)
        hash_input = json.dumps(hash_structure, sort_keys=True)
        variant_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        values['variant'] = variant_hash
        return values
