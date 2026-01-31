# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import List, Optional, Dict, Any, ClassVar, Union
from pydantic import Field, BaseModel, field_validator
from datetime import datetime, timezone
import json
from ipulse_shared_base_ftredge import (AIModelStatus, ObjectOverallStatus,
                                        DataModality, DataStructureLevel,
                                        ModalityContentDynamics, DataResource,
                                        SectorRecordsCategory, AIModelTrainingType)
from ..common import BaseVersionedModel


class AIModelIOCapabilities(BaseModel):
    """Defines what I/O formats and capabilities a model supports."""

    # Modality support
    modalities: List[DataModality] = Field(default_factory=list, description="Supported data modalities")
    structure_levels: List[DataStructureLevel] = Field(default_factory=list, description="Supported structure levels")
    content_dynamics: List[ModalityContentDynamics] = Field(default_factory=list, description="Supported content dynamics")
    resource_formats: Optional[List[DataResource]] = Field(default_factory=list, description="Specific resource/data content formats supported, e.g., ['in_memory_data', 'file_json', 'file_png']")
    sector_records_categories: Optional[List[SectorRecordsCategory]] = Field(default_factory=list, description="Specific sector/record categories supported, e.g., ['market', 'indicator', 'fundamental', 'knowledge' etc.]")
    
    # Consolidated modality-specific capabilities (stored as JSON string in BigQuery)
    general_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="General capabilities: max_total_size_mb, max_modalities, context_window_tokens, etc.")
    text_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Text capabilities: max_tokens, max_input_tokens, max_output_tokens, supports_streaming, etc.")
    json_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="JSON capabilities: supports_structured_json_output, max_schema_depth, supports_json_mode, etc.")
    tabular_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tabular capabilities: max_rows, max_columns, supported_formats (csv, parquet, etc.), etc.")
    image_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Image capabilities: max_images, max_image_size_mb, image_formats (png, jpeg, webp), max_resolution, etc.")
    audio_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Audio capabilities: max_audio_length_seconds, max_audio_tokens, audio_formats, sample_rates, etc.")
    video_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Video capabilities: max_videos, max_video_length_seconds, max_video_length_with_audio_seconds, max_video_length_without_audio_seconds, video_formats, etc.")
    file_capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="File/Document capabilities: max_documents, max_pages_per_document, max_size_per_document_mb, document_formats (pdf, txt, docx), etc.")

    notes: Optional[str] = Field(default=None, max_length=2000, description="Additional notes or considerations")


class AIModelVersion(BaseVersionedModel):
    """
    📦 AI MODEL VERSION - The Trained Implementation with Specific Capabilities

    CORE CONCEPT:
    Represents a specific, trained instance of an AI model with VERSION-SPECIFIC I/O CAPABILITIES.
    This is the successful result of executing a training configuration against a model specification,
    producing a versioned artifact with concrete capability definitions ready for serving.

    KEY INNOVATION - VERSION-SPECIFIC I/O CAPABILITIES:
    AIModelVersion includes input_capabilities and output_capabilities (AIModelIOCapabilities) to track
    how model capabilities evolve between versions. This is critical for external models where providers
    update capabilities:
    • Gemini 2.5 Pro Dec 2024: 1M tokens, text+image
    • Gemini 2.5 Pro Jun 2025: 1M tokens, text+image+audio+video

    KEY RELATIONSHIPS:
    • ONE model specification (AIModelSpecification) → MULTIPLE model versions
    • ONE training configuration → MULTIPLE model versions (over time)
    • ONE training run → ZERO or ONE model version (if training succeeded)
    • ONE model version → MULTIPLE serving instances (AIModelServingInstance)

    ARCHITECTURE SEPARATION:
    • AIModelSpecification: Defines model FAMILY identity and general approach
    • AIModelVersion: Defines VERSION-SPECIFIC capabilities (I/O limits, features, etc.)
    • AIModelServingInstance: Defines ACCESS METHOD (how to call the model)

    VERSION LINEAGE & EVOLUTION:
    Model versions form evolutionary lineages through parent_version_id:
    • Base Model: v1.0.0 (initial training from specification)
    • Retrained: v1.1.0 → v1.2.0 → v1.3.0 (scheduled retraining cycles)
    • Fine-tuned: v1.1.1 → v1.1.2 (incremental improvements)
    • Branched: v2.0.0 (architectural changes or new training approach)
    • External: v20250626 → v20250815 (provider releases with capability changes)

    TRAINING INTEGRATION (Internal Models):
    • training_config_id: Links to the training plan that produced this version
    • training_run_id: Links to the specific execution that created this artifact
    • parent_version_id: Links to previous version for lineage tracking
    • model_artifact_location: Physical storage of trained model (GCS, S3, etc.)
    • model_artifact_checksum: Integrity verification for deployments

    EXTERNAL MODEL VERSIONING:
    For third-party models (GPT, Gemini, Claude), versions track:
    • API model identifier (e.g., "gemini-2.5-pro")
    • Release date and deprecation information
    • Version-specific I/O capabilities (input_capabilities, output_capabilities)
    • Performance benchmarks and cost characteristics
    • Null values for: training_config_id, training_run_id, model_artifact_location

    I/O CAPABILITIES (AIModelIOCapabilities):
    Comprehensive specification of what this version can handle:
    • Modalities: TEXT, IMAGE, AUDIO, VIDEO, TABULAR, JSON_TEXT
    • Capacity Limits: max_tokens, max_total_size_mb, max_images, max_videos, etc.
    • Document Support: max_documents, max_pages_per_document, document_formats
    • Image Support: max_images, max_image_size_mb, image_formats
    • Audio Support: max_audio_length_seconds, max_audio_tokens, audio_formats
    • Video Support: max_videos, max_video_length_with/without_audio, video_formats

    REAL-WORLD EXAMPLE - Gemini 2.5 Pro June 2025:
    ```python
    AIModelVersion(
        model_version_name="gemini_2_5_pro_20250626",
        api_model_identifier="gemini-2.5-pro",
        release_date=datetime(2025, 6, 26),
        
        input_capabilities=AIModelIOCapabilities(
            modalities=[TEXT, IMAGE, AUDIO, VIDEO],
            max_tokens=1048576,  # 1M context
            max_images=3000,
            max_image_size_mb=7.0,
            max_videos=10,
            max_video_length_with_audio_seconds=2700,  # 45 min
            max_audio_length_seconds=30240,  # 8.4 hours
        ),
        
        output_capabilities=AIModelIOCapabilities(
            modalities=[TEXT],
            max_tokens=65535,
        )
    )
    ```

    LIFECYCLE STATES (version_status):
    DRAFT → TRAINING → TRAINED → VALIDATED → DEPLOYED → SERVING → RETIRED
    
    SERVING PATTERN:
    Version artifacts remain immutable. Access methods and hosting details are managed
    by AIModelServingInstance to support:
    • Multiple access methods (genai.Client, Vertex AI, custom endpoints)
    • Multi-region deployments (same version accessible from different regions)
    • A/B testing (same version with different configurations)
    • Environment separation (though external models typically don't have env separation)

    PERFORMANCE TRACKING:
    Each version tracks real-world performance to enable:
    • Comparative analysis between versions
    • Performance degradation detection over time
    • ROI analysis of version upgrades
    • Cost optimization for external model usage
    • Automated rollback triggers for quality control

    WHY I/O AT VERSION LEVEL (NOT SPECIFICATION):
    • External model capabilities evolve with each release
    • Different versions have different limits and features
    • Enables accurate historical tracking of what was available when
    • Prevents assumptions that "Gemini 2.5 Pro" always means the same capabilities
    • Supports data-driven decision making about version upgrades
    
    INHERITED FROM BaseVersionedModel:
    - description, major_version, minor_version, metadata_version
    - pulse_status, changelog_registry, lessons_learned, notes, tags
    - pulse_namespace, namespace_id_seed_phrase
    - created_at, created_by, updated_at, updated_by
    """

    VERSION: ClassVar[int] = 8
    SCHEMA_ID: ClassVar[str] = "schema_7a741968-292e-5a1d-a3a4-6321ae1548de"
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction__controls.ai_model_versions"
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aimodelversion"

    # --- Identifiers and Relationships ---
    model_version_id: str = Field(..., max_length=200, description="The unique identifier for this specific model version.")
    model_version_name: str = Field(..., max_length=200, description="Machine-readable identifier for programmatic use (e.g., 'gemini_2_5_pro_20250626', 'gpt_4_turbo_2024_04_09')")
    model_version_display_name: Optional[str] = Field(default=None, max_length=300, description="Human-readable version name for UI display, e.g., 'Summer 2024 Production', 'Gemini 2.5 Pro June 2025')")
    # Note: metadata_version is now inherited from BaseVersionedModel
    model_spec_id: str = Field(..., max_length=200, description="Reference to the AIModelSpecification this version implements.")
    training_config_id: Optional[str] = Field(default=None, max_length=200, description="Reference to the AITrainingAndUpdateConfiguration following which this model was created. I.E. the training plan. (Unknown for external models)")
    training_run_id: Optional[str] = Field(default=None, max_length=200, description="Reference to the AITrainingOrUpdateRun that produced this version (Unknown for external models).")
    parent_version_id: Optional[str] = Field(default=None, max_length=200, description="Reference to the parent model version from which this one was retrained, fine-tuned or updated.")

    # --- Version Specifications and Capabilities ---
    knowledge_cutoff_timestamp_utc: Optional[datetime] = Field(default=None, description="UTC timestamp when training data knowledge cutoff occurred (when training data ends)")
    training_finished_on_datetime_utc: Optional[datetime] = Field(default=None, description="UTC timestamp when model training was completed")
    last_training_type: Optional[AIModelTrainingType] = Field(default=None, description="Type of last training performed (initial_training, complete_retraining, incremental_training, fine_tuning, etc.)")
    version_specs: Optional[Union[Dict[str, Any], str]] = Field(default_factory=dict, description="Version-specific specifications (stored as JSON string in BigQuery): parameters_count, training_data_size, compute_used, etc.")
    
    # --- Mode Support ---
    supported_modes_single_request: Optional[Union[Dict[str, Dict[str, str]], str]] = Field(default=None, description="Supported analyst modes for single requests. Dict of mode_id:{\"name\": mode_name}. None = all modes supported. Stored as JSON string in BigQuery.")
    supported_modes_batch_request: Optional[Union[Dict[str, Dict[str, str]], str]] = Field(default=None, description="Supported analyst modes for batch requests. Dict of mode_id:{\"name\": mode_name}. None = all modes supported. Stored as JSON string in BigQuery.")
    
    # --- I/O Capabilities (Moved from AIModelSpecification) ---
    # Rationale: Capabilities can evolve between versions, especially for external LLMs
    # Example: Gemini 2.5 Pro Dec 2024 (1M context) → Feb 2025 (2M context + vision)
    input_capabilities: Optional[AIModelIOCapabilities] = Field(default=None, description="Input format capabilities and constraints for THIS version")
    output_capabilities: Optional[AIModelIOCapabilities] = Field(default=None, description="Output format capabilities and constraints for THIS version")

    # --- External Model Tracking ---
    api_model_identifier: Optional[str] = Field(default=None, max_length=200, description="API identifier to use when calling external service (e.g., 'gemini-2.5-pro-002', 'gpt-4-turbo-2024-04-09')")
    release_date: Optional[datetime] = Field(default=None, description="Official release date from provider (when this capability set became available)")
    available_from: Optional[datetime] = Field(default=None, description="When this version became available in our system")
    deprecated_on: Optional[datetime] = Field(default=None, description="When provider deprecated this version (NULL if still active)")

    # --- Model State and Status ---
    # Note: pulse_status, changelog_registry, lessons_learned inherited from BaseVersionedModel
    version_status: AIModelStatus = Field(..., description="Current lifecycle status of this model version.")
    version_overall_pulse_performance_score: Optional[float] = Field(default=None, ge=0, le=100, description="Overall performance assessment score for this version (0-100). Used for ranking and comparison.")
   
    # --- Lifecycle Timestamps and Governance ---
    deployment_to_production_approved_by: Optional[str] = Field(default=None, max_length=100, description="Who approved this model version for deployment.")
    approval_notes: Optional[str] = Field(default=None, max_length=2000, description="Notes from the approval process.")
    deployed_to_production_datetime: Optional[datetime] = Field(default=None, description="When this model version was first used for production inference.")
    version_retired_datetime: Optional[datetime] = Field(default=None, description="When this model version was retired from active use.")
   
    # --- Model Artifacts ---
    version_artifact_location: Optional[str] = Field(default=None, max_length=2000, description="Primary storage location of the trained model artifact (GCS path, S3 path, etc.)")
    version_artifact_details: Optional[Union[Dict[str, Any], str]] = Field(default_factory=dict, description="Artifact details (stored as JSON string in BigQuery): checksum, size_mb, format, compression, etc.")
    
    # NOTE: Hosting and deployment information is handled by AIModelServingInstance 
    # to support multiple serving instances per model version (multi-region, A/B testing, different hosting patterns)

    # --- Metadata ---
    # Note: notes, tags, pulse_namespace, namespace_id_seed_phrase, created_at, created_by, updated_at, updated_by
    # are now inherited from BaseVersionedModel
    
    model_description: Optional[str] = Field(default=None, max_length=2000, description="Description of what makes this model version unique.")
    release_notes: Optional[str] = Field(default=None, max_length=5000, description="Release notes describing changes and improvements.")
    known_limitations: Optional[str] = Field(default=None, max_length=2000, description="Known limitations or issues with this model version.")
    strengths: Optional[str] = Field(default=None, max_length=2000, description="Strengths of this model version, e.g., 'high accuracy on recent data'.")
    weaknesses: Optional[str] = Field(default=None, max_length=2000, description="Weaknesses of this model version (e.g., 'struggles with outliers').")
    recommended_use_cases: Optional[Union[List[str], str]] = Field(default=None, description="Recommended use cases for this model version (stored as JSON string in BigQuery).")

    # --- Validators for JSON Fields (BigQuery stores as STRING) ---
    
    @field_validator('version_specs', mode='before')
    @classmethod
    def parse_version_specs(cls, v):
        """Parse version_specs from JSON string (BigQuery) to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v or {}
    
    @field_validator('supported_modes_single_request', 'supported_modes_batch_request', mode='before')
    @classmethod
    def parse_supported_modes(cls, v):
        """Parse supported_modes from JSON string (BigQuery) to dict of dicts."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else None
            except json.JSONDecodeError:
                return None
        return v
    
    @field_validator('version_artifact_details', mode='before')
    @classmethod
    def parse_version_artifact_details(cls, v):
        """Parse version_artifact_details from JSON string (BigQuery) to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        return v or {}
    
    @field_validator('recommended_use_cases', mode='before')
    @classmethod
    def parse_recommended_use_cases(cls, v):
        """Parse recommended_use_cases from JSON string (BigQuery) to list."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return v or []
