# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import List, Optional, Dict, Any, ClassVar, Literal, Union
from pydantic import Field, field_validator
from datetime import datetime, timezone
import json
from ipulse_shared_base_ftredge import (
    AILearningParadigm,
    ObjectOverallStatus,
    AIProblemType,
    AIAlgorithm,
    AIArchitectureStructure,
    TSize,
)
from ..common import BaseVersionedModel


class AIModelSpecification(BaseVersionedModel):
    """
    🏗️ AI MODEL SPECIFICATION - The Architectural Blueprint

    CORE CONCEPT:
    Defines the fundamental architecture and capabilities of an AI model FAMILY - what it CAN do
    conceptually, not specific version implementations. This is the "specification sheet" that 
    describes the model family's purpose, architectural patterns, and general problem-solving approach
    before any training or deployment occurs.

    KEY RELATIONSHIPS:
    • ONE specification → MULTIPLE model versions (AIModelVersion)
    • ONE specification → MULTIPLE training configurations  
    • ONE specification → MULTIPLE serving instances (via versions)
    • Specification defines FAMILY IDENTITY, versions define VERSION-SPECIFIC CAPABILITIES

    WHAT SPECIFICATIONS DEFINE:
    • Model family name and provider (e.g., "Google Gemini 2.5 Pro family")
    • Learning paradigm (supervised, unsupervised, generative, foundation)
    • Problem types supported (regression, classification, time series, multi-modal)
    • Algorithm categories and architectural structures
    • Target specification system (what the model can predict)

    WHAT SPECIFICATIONS DO NOT DEFINE:
    • Specific version capabilities (handled by AIModelVersion.input_capabilities/output_capabilities)
    • Deployment configurations (handled by AIModelServingInstance)
    • API endpoints or access methods (handled by AIModelServingInstance)
    • Version-specific I/O limits (e.g., context window sizes - handled by AIModelVersion)

    GENERALIZATION STRATEGIES:
    • Specialized Models: Fixed input/output schemas, optimized for specific tasks
      - Example: Stock price predictor (AAPL OHLCV → price_target)
      - Static typing, predictable I/O, high performance for narrow use cases
    
    • Generalized Models: Dynamic I/O via prompting, adaptable to multiple tasks
      - Example: Foundation models (GPT-4, Gemini) with flexible capabilities
      - Runtime typing, morphic I/O (text → JSON → SQL → image → code)
      - I/O capabilities evolve per version (tracked in AIModelVersion)

    EXTERNAL MODEL SUPPORT:
    • Foundation Models: GPT-4, Gemini Pro, Claude-3 families
    • Managed Services: BigQuery ML, Vertex AI, SageMaker, Databricks ML
    • Specification = Family identity, Version = Specific release with capabilities

    TARGET SPECIFICATION SYSTEM:
    Flexible criteria for defining prediction scope:
    ```json
    {
        "domain": ["fincore_market_assets"],
        "asset_class": ["equity", "crypto"], 
        "market_cap_min": 1000000000,
        "specific_object_ids": ["AAPL", "GOOGL"]
    }
    ```

    ARCHITECTURAL FAMILIES:
    • Regression: Continuous value prediction with confidence intervals
    • Classification: Category prediction with probability distributions  
    • Time Series: Temporal pattern analysis and forecasting
    • Foundation Model: Multi-task capability via natural language interfaces
    • Multimodal: Cross-modal understanding and generation

    REAL-WORLD EXAMPLE - Gemini 2.5 Pro:
    • Specification: Defines "Google Gemini 2.5 Pro family" as a foundation model
    • Version 20250626: Defines 1M tokens, text+image+audio+video capabilities
    • Version 20250815: Defines 2M tokens, enhanced audio capabilities (example future)
    • Instance genai_client: Defines access via genai.Client SDK with API key

    LIFECYCLE INTEGRATION:
    Specifications flow into training configurations → training runs → model versions (with I/O capabilities) 
    → serving instances (with access methods), providing the architectural foundation for the entire ML 
    pipeline while maintaining clear separation of concerns:
    - Specification: FAMILY IDENTITY
    - Version: VERSION-SPECIFIC CAPABILITIES  
    - Instance: ACCESS METHOD CONFIGURATION
    
    INHERITED FROM BaseVersionedModel:
    - description, major_version, minor_version, metadata_version
    - pulse_status, changelog_registry, lessons_learned, notes, tags
    - pulse_namespace, namespace_id_seed_phrase
    - created_at, created_by, updated_at, updated_by
    """

    SCHEMA_ID: ClassVar[str] = "schema_6a0c8d28-547f-57d4-ad95-74bc9696ef00"
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction__controls.ai_model_specifications"
    VERSION: ClassVar[int] = 8
    DOMAIN: ClassVar[str] = "dp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aimodelspec"

    # Core identification
    model_spec_id: str = Field(..., description="Unique identifier for this AI model specification")
    model_spec_name: str = Field(..., max_length=200, description="Machine-readable identifier for programmatic use (e.g., 'google_gemini_2_5_pro', 'openai_gpt_4_turbo')")
    model_spec_display_name: str = Field(..., max_length=500, description="Human-readable name for UI display (e.g., 'Gemini 2.5 Pro', 'GPT-4 Turbo')")
    # Note: metadata_version is now inherited from BaseVersionedModel

    # Model classification
    model_generalization_level: Literal["specialized", "generalized"] = Field(..., description="'specialized' for fixed I/O models, 'generalized' for foundation models")
    
    # Target specification (for specialized models)
    target_object_id: Optional[str] = Field(default=None, description="In highly specialized models: single object ID this model targets, e.g., 'AAPL' (NULL for generalized models)")
    target_record_type: Optional[str] = Field(default=None, description="In highly specialized models: record type of this model's targets, e.g., 'eod_close_pct_change', 'intraday_adjc', 'eod_vol'")

    # NOTE: input_capabilities and output_capabilities moved to AIModelVersion
    # Rationale: Capabilities can evolve between versions (especially for LLMs)
    # Example: GPT-4 → GPT-4V (added vision), Gemini 2.5 context updates

    # Model source and architecture
    model_source: Literal["internal", "external_foundational", "external_service"] = Field(..., description="internal: trained by us, external_foundational: like LLAMA, external_service: GPT, Gemini, Claude")
    model_author: str = Field(..., description="Author or team responsible for the model")
    model_provider_organization: str = Field(..., description="Comma-separated list of provider organizations (e.g., OpenAI, Google, Anthropic)")
    model_license: Optional[str] = Field(default=None, description="License under which the model is released")
    model_rights_description: Optional[str] = Field(default=None, description="Description of rights associated with the model")

    # --- Training & Features ---
    learning_paradigm: AILearningParadigm = Field(..., description="Learning paradigm: supervised, unsupervised, reinforcement, etc.")
    supported_ai_problem_types: List[AIProblemType] = Field(..., description="List of AI problem types this model can solve: regression, classification, time_series_forecasting, etc.")
    ai_algorithms: Optional[List[AIAlgorithm]] = Field(default=None, description="List of algorithms used by this model: [linear_regression], [transformer], [random_forest, xgboost], etc.")
    ai_architecture_structure: AIArchitectureStructure = Field(default=AIArchitectureStructure.SINGLE, description="How algorithms are combined: single, ensemble, stacked_ensemble, sequential, etc.")

    # Custom validators for BigQuery string array deserialization
    @field_validator('supported_ai_problem_types', mode='before')
    @classmethod
    def parse_problem_types(cls, v):
        """Convert string array from BigQuery to list of enums."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return [AIProblemType(item) for item in parsed]
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid supported_ai_problem_types format: {e}")
        return v

    @field_validator('ai_algorithms', mode='before')
    @classmethod
    def parse_algorithms(cls, v):
        """Convert string array from BigQuery to list of enums."""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return [AIAlgorithm(item) for item in parsed]
            except (json.JSONDecodeError, ValueError) as e:
                raise ValueError(f"Invalid ai_algorithms format: {e}")
        return v

    foundation_model_type: Optional[str] = Field(default=None, description="Model family, e.g., 'gpt-4', 'gemini-pro', 'claude-3', applicable for foundational models only.")
    external_managed_model_service_name: Optional[str] = Field(default=None, description="External service name (e.g., 'bigquery_ml', 'bigquery_ai', 'vertex_ai', 'sagemaker', 'databricks_ml').")

    # Development details
    model_development_framework: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="Information about the model framework (stored as JSON string in BigQuery), e.g., {'framework': 'TensorFlow', 'version': '2.14', 'gpu_support': True}.")
    model_description: Optional[str] = Field(default=None, description="Detailed description of the model, purpose, and architecture")
    model_overall_pulse_performance_score: Optional[float] = Field(default=None, description="A single overall performance score for the model.")
    parameters_count: Optional[int] = Field(default=None, description="Number of parameters in the model for complexity assessment")
    hyperparameters_schema: Optional[Union[Dict[str, Any], str]] = Field(default=None, description="The hyperparameters used to train the model (stored as JSON string in BigQuery), e.g., {'learning_rate': 0.001, 'batch_size': 32, 'epochs': 100}.")
    model_complexity_score: Optional[float] = Field(default=None, description="Complexity score for model comparison and resource planning")
    model_size: Optional[TSize] = Field(default=None, description="Model size category for resource planning (s, m, l, xl, xxl, xxxl)")

    model_features: Optional[Union[Dict[str, Any], str]] = Field(default_factory=dict, description="Additional model modes/features (stored as JSON string in BigQuery): {'deep_thinking':'description....'', 'function_calling':'...', 'internet_browsing':'...', 'code_execution':'...', 'vision_analysis':'...', 'multimodal_reasoning':'...'}")

    # --- Validators for JSON Dict Fields (BigQuery stores as STRING) ---
    
    @field_validator('model_development_framework', mode='before')
    @classmethod
    def parse_model_development_framework(cls, v):
        """Parse model_development_framework from JSON string (BigQuery) to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else None
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator('hyperparameters_schema', mode='before')
    @classmethod
    def parse_hyperparameters_schema(cls, v):
        """Parse hyperparameters_schema from JSON string (BigQuery) to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else None
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator('model_features', mode='before')
    @classmethod
    def parse_model_features(cls, v):
        """Parse model_features from JSON string (BigQuery) to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v or {}

    # --- USE CASES--- # Below is COMMENTED OUT , BECAUSE THERE ARE POTENTIALLY MANY VERSIONS FOR A SINGLE MODEL
    # Note: notes, tags, pulse_namespace, namespace_id_seed_phrase, created_at, created_by, updated_at, updated_by
    # are now inherited from BaseVersionedModel
    
    strengths: Optional[str] = Field(default=None, description="Description of the model specification strengths")
    weaknesses: Optional[str] = Field(default=None, description="Description of the model specification weaknesses")
    recommended_use_cases: Optional[str] = Field(default=None, description="Comma-separated list of recommended use cases")
    recommended_consumers: Optional[str] = Field(default=None, description="Comma-separated list of recommended consumers (trading_system, retail_customer, financial_analyst, financial_advisor, enterprise_customer, etc.)")
    model_conceived_on: Optional[datetime] = Field(default=None, description="The timestamp when the model was created.")



    

    