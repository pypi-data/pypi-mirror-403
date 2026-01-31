# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from ipulse_shared_base_ftredge import AIModelTrainingType, ComputeResourceStatus


class AITrainingOrUpdateRun(BaseModel):
    """
    🏃 AI TRAINING RUN - The Actual Execution
    
    CORE CONCEPT:
    This captures the EXACT details of a single training execution - what data was actually used,
    what happened during training, what was the result. This is the "what really happened" record.
    
    KEY RELATIONSHIPS:
    • ONE training configuration → MULTIPLE training runs (over time)
    • ONE training run → ZERO or ONE model version (if successful)
    • ONE training run CAN BE USED BY multiple training configurations (shared runs)
    
    SHARED TRAINING RUNS:
    Training runs can be shared between multiple training configurations:
    ✅ Initial training: Both "daily retrain" and "weekly retrain" configs use same initial run
    ✅ Complete retraining: Multiple configs can share the same full retrain run
    ❌ Fine-tuning runs: Usually NOT shared as models diverge after different training schedules
    
    DATA PRECISION:
    • Training Config: "Use market data from last 2 years" (blueprint)
    • Training Run: "Used market_data_v2.3, 2022-01-15 to 2024-01-15, 45,231 records" (actual)
    
    TRACKING VALUE:
    By comparing training runs from different configs, we can answer:
    • Does daily retraining improve performance vs weekly?
    • What's the cost/benefit of more frequent updates?
    • Which training frequency gives best ROI?
    """

    VERSION: ClassVar[int] = 2
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aitrainingrun"

    # --- Identifiers and Relationships ---
    training_run_id: str = Field(..., description="The unique identifier for this specific training run execution.")
    training_config_id: str = Field(..., description="Reference to the AITrainingAndUpdateConfiguration that defined this run.")
    training_type: AIModelTrainingType = Field(..., description="Type of training: Initial training, Complete retraining, Fine-tuning, State update, etc.")
    model_spec_id: str = Field(..., description="Reference to the AIModelSpecification being trained.")
    input_model_version_id: str = Field(..., description="The version of the model being re-trained, finetuned etc.")
    output_model_version_id: str = Field(..., description="The version of the model produced by this training run.")
    
    experiment_id: Optional[str] = Field(default=None, description="Experiment ID for grouping related training runs.")
    parent_run_id: Optional[str] = Field(default=None, description="Parent training run ID if this is a continuation or fine-tuning.")


    # --- Training Targets Used (What was actually trained on) ---
    target_subjects_selection_criteria_used: Dict[str, Any] = Field(..., description="The actual target selection criteria that were applied in this training run.")
    prediction_variables_trained: List[str] = Field(..., description="List of prediction variables that were actually trained for in this run.")
    
    # --- Execution Context ---
    run_name: str = Field(..., description="Human-readable name for this training run, e.g., 'AAPL_daily_retrain_2024_08_06'.")
    run_environment: str = Field(..., description="Environment where training was executed, e.g., 'production', 'staging', 'development'.")
    compute_environment: Optional[Dict[str, Any]] = Field(default=None, description="Details about compute resources used, e.g., instance type, GPU, memory.")
    
    # --- Training Data Used (Multi-dimensional) ---
    training_data_sources_used: List[Dict[str, Any]] = Field(..., description="Training data sources used in this run with their final characteristics after preprocessing.")
    # Example structure:
    # {
    #   "schema_id": "market_eod_data_realtime",
    #   "schema_name": "Market EOD Real-time Feed", 
    #   "rows_count": 252,  # trading days used
    #   "index_or_date_column_name": "date_id",  # primary temporal/index column
    #   "feature_columns_used": ["open_normalized", "volume_log", "sentiment_score"],
    #   "temporal_range_start": "2024-01-15",
    #   "temporal_range_end": "2024-12-31",
    #   "data_freshness_minutes": 15,  # how old the latest data is
    #   "preprocessing_applied": {"outlier_removal": True, "normalization": "z_score"},
    #   "dataset_filter_used": {"asset_id_in": ["AAPL", "GOOGL"], "asset_category_pulse":"equity",  "trading_status": "traded_on_exchange"},
    #   "dataset_scope": "training_universe"
    # }
    
    feature_engineering_applied: Optional[Dict[str, Any]] = Field(default=None, description="Feature engineering transformations applied during this training run.")
    data_quality_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Data quality metrics from this training run, e.g., missing value rates, outlier counts.")
    
    # --- Execution Timing ---
    training_start_datetime: datetime = Field(..., description="Timestamp when the training process started.")
    training_end_datetime: Optional[datetime] = Field(default=None, description="Timestamp when the training process concluded.")
    training_duration_seconds: Optional[float] = Field(default=None, description="Total training duration in seconds.")
    
    # --- Training Process Details ---
    hyperparameters_used: Optional[Dict[str, Any]] = Field(default=None, description="Actual hyperparameters used if different from configuration. Only populated when runtime parameters differ from the training configuration template.")
    training_stopping_reason: Optional[str] = Field(default=None, description="Reason training stopped, e.g., 'convergence', 'early_stopping', 'max_epochs'.")
    epochs_completed: Optional[int] = Field(default=None, description="Number of training epochs completed.")
    best_epoch: Optional[int] = Field(default=None, description="Epoch that produced the best validation performance.")
    
    # --- Cost and Resource Tracking ---
    training_run_cost_usd: Optional[float] = Field(default=None, description="Cost of this specific training run in USD.")
    compute_hours: Optional[float] = Field(default=None, description="Total compute hours consumed.")
    peak_memory_usage_gb: Optional[float] = Field(default=None, description="Peak memory usage during training in GB.")
    
    # --- Model Output and Artifacts ---
    model_artifact_id: Optional[str] = Field(default=None, description="Identifier for the serialized model artifact produced.")
    model_artifact_location: Optional[str] = Field(default=None, description="Storage location of the trained model artifact.")
    model_artifact_size_mb: Optional[float] = Field(default=None, description="Size of the model artifact in MB.")
    checkpoint_locations: Optional[List[str]] = Field(default=None, description="List of checkpoint storage locations saved during training.")
    
    # --- Performance Metrics ---
    final_training_loss: Optional[float] = Field(default=None, description="Final training loss value.")
    final_validation_loss: Optional[float] = Field(default=None, description="Final validation loss value.")
    performance_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Detailed performance metrics from this run.")
    convergence_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Metrics tracking convergence behavior.")
    
    # --- Status and State ---
    run_status: ComputeResourceStatus = Field(..., description="Current status of this training run.")
    error_message: Optional[str] = Field(default=None, description="Error message if training failed.")
    warnings: Optional[List[str]] = Field(default=None, description="List of warnings encountered during training.")
    
    # --- Reproducibility ---
    random_seed: Optional[int] = Field(default=None, description="Random seed used for reproducibility.")
    code_version: Optional[str] = Field(default=None, description="Git commit hash or version of training code used.")
    framework_version: Optional[Dict[str, str]] = Field(default=None, description="Versions of ML frameworks used, e.g., {'tensorflow': '2.13.0'}.")
    
    # --- Metadata ---
    triggered_by: Optional[str] = Field(default=None, description="What triggered this training run, e.g., 'scheduled', 'manual', 'drift_detected'.")
    notes: Optional[str] = Field(default=None, description="Additional notes about this specific training run.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization and filtering.")

    # --- Namespace and Identity ---
    pulse_namespace: Optional[str] = Field(default=None, description="Namespace for this AI training run.")
    namespace_id_seed_phrase: Optional[str] = Field(default=None, description="Seed phrase used for namespace-based UUID generation.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)