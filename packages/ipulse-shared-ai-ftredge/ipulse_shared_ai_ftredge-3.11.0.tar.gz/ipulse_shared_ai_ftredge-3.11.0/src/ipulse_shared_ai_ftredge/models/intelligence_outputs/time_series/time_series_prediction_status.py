"""Common base model for all time series predictions (LLM and Quant)."""
from typing import ClassVar, Dict, Any, Literal, Optional, Union, List
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from ipulse_shared_base_ftredge.enums import (ModelOutputPurpose, ProgressStatus, TimeFrame, ReviewStatus, PredictionPipelineStatus, ObjectOverallStatus)

class TimeSeriesPredictionStatus(BaseModel):
    """
    Universal prediction status tracking ALL time series predictions regardless of method.
    
    Tracks prediction requests from creation → execution → response retrieval → parsing.
    Used by: LLM predictions, Quant models, Expert predictions, any time series forecast.
    
    Workflow:
    1. Request Pipeline: Creates log with status=IN_PROGRESS, populates request metadata
    2. Model Execution: Updates with job_id, batch details (for async models like Gemini)
    3. Response Pipeline: Fetches results, updates status=PROCESSING_RESPONSE
    4. Parser: Validates response, saves to tables, updates status=COMPLETED/FAILED
    5. Retry Pipeline: Re-processes FAILED predictions (separate pipeline)
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction_market__datasets.prediction_status"
    VERSION: ClassVar[int] = 3
    DOMAIN: ClassVar[str] = "oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "predrqstlog"
    
    # --- Core Identity ---
    prediction_request_batch_id: Optional[str] = Field(default=None, description="Reference to the TimeSeriesPredictionBatch if part of a batch prediction")
    prediction_request_task_id: str = Field(..., description="Reference to the exact prediction request task that, associated with a specific subject, model, and IO format, initiated this prediction")
    prediction_request_metadata_version: int = Field(1, ge=1, description="Metadata version for tracking non-breaking changes to this prediction record (1, 2, 3...)")
    prediction_response_id: Optional[str] = Field(default=None, description="Same or different from prediction_request_id, used to link to the response entity if applicable")
    prediction_job_id: Optional[str] = Field(default=None, description="Reference to the TimeSeriesPredictionJob if part of a larger prediction job")
    predictions_other_ids: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Additional identifiers related to this prediction log")
    xref_subject_model_ioformat_charging_id: Optional[str] = Field(default=None, description="Cross-reference ID linking subject, model, and IO format for accurate charging and tracking")
    prediction_purpose: ModelOutputPurpose = Field(..., description="Training, Validation, Serving..")

    # --- Target Context ---
    subject_id: str = Field(..., max_length=300, description="ID of the subject being predicted")
    subject_name: str = Field(..., max_length=200, description="Name of the subject being predicted")
    predicted_records_type: Optional[str] = Field(default=None, max_length=100, description="Type of records being predicted in the timeseries, e.g., 'eod_adjc', 'intraday_adjc', 'eod_sentiment_score' etc")
   
    # --- AI Model Context ---
    analyst_id: str = Field(..., max_length=300, description="Unique identifier for the analyst (human or AI) making this prediction")
    model_version_id: str = Field(..., max_length=300, description="AI model version identifier")
    model_version_name: str = Field(..., max_length=200, description="Machine-readable model version name")
    model_serving_instance_id: Optional[str] = Field(default=None, max_length=300, description="ID of the specific serving instance used for this prediction")
    model_training_config_id: Optional[str] = Field(default=None, max_length=300, description="Model training configuration identifier (null for pre-trained models)")
    model_setups_used: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="JSON serialized model runtime configuration/setup, e.g., {'temperature': 0.3, 'top_p': 0.95}")
    model_knowledge_info: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="JSON with knowledge cutoffs, release dates, and capabilities")

    # Input sources with strong typing (stored as JSON string in BigQuery)
    input_confirmed_details: Optional[Union[str, List[Dict[str, Any]]]] = Field(default=None, description="JSON serialized input IO details or list of input sources used for this prediction")
    # Example structure:
    # [
    #   {
    #     "input_type": "AIIOFormat",
    #     "io_format_id": "equity_ohlcv_daily_v1",
    #     "source_location": "bigquery://project.dataset.table",
    #     "rows_count": 252,
    #     "feature_store_version": "v1.2.3",
    #     "temporal_range_start": "2024-01-15",
    #     "temporal_range_end": "2024-12-31",
    #     "feature_columns_used": ["open_normalized", "volume_log"],
    #     "preprocessing_applied": {"outlier_removal": True}
    #   },
    #   {
    #     "input_type": "AIIOFormat", 
    #     "io_format_id": "financial_prompt_v1",
    #     "prompt_text": "Analyze AAPL stock performance...",
    #   }
    # ]
    
    # Traditional output schema reference (for fixed models) (stored as JSON string in BigQuery)
    output_confirmed_details: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="JSON serialized output IO details or output data schema used for this prediction")
    # Example structure:
    # {
    #   "output_type": "AIIOFormat",
    #   "io_format_id": "equity_price_forecast_v1",

    # --- Value Context Summary (not the actual values) ---
    # These fields are populated from response - first/last timeseries timestamps and count
    prediction_values_start_timestamp_utc: Optional[Union[datetime, str]] = Field(default=None, description="Start timestamp of prediction horizon (populated from response - first timeseries timestamp)")
    prediction_values_end_timestamp_utc: Optional[Union[datetime, str]] = Field(default=None, description="End timestamp of prediction horizon (populated from response - last timeseries timestamp)")
    prediction_steps_count: Optional[int] = Field(default=None, description="Number of time steps predicted (populated from response - count of timeseries records)")
    prediction_step_timeframe: Optional[Union[TimeFrame, str]] = Field(default=None, description="Time frequency of predictions (populated from response or inferred from timestamps)")
    
    # --- Prediction Status ---
    prediction_pipeline_status: PredictionPipelineStatus = Field(..., description="Overall pipeline status: PREDICTION_REQUEST_SUBMISSION, AWAITING_PREDICTION_RESPONSE, QA_PRE_SAVING_TO_DP...")
    prediction_request_progress_status: ProgressStatus = Field(ProgressStatus.NOT_STARTED, description="Status of the prediction generation process.")
    prediction_request_job_status: Optional[str] = Field(default=None, description="Status of the underlying model job if applicable. eg.: JOB_STATE_PENDING, JOB_STATE_RUNNING, JOB_STATE_SUCCEEDED, JOB_STATE_FAILED")
    prediction_generation_finish_reason: Optional[str] = Field(default=None, description="Reason the prediction process finished (e.g., completed, error, timeout)")
    prediction_response_processing_progress_status: ProgressStatus = Field(ProgressStatus.NOT_STARTED, description="Status of the prediction response saving process.")
   
    prediction_response_latest_qa_for_display: ReviewStatus = Field(ReviewStatus.OPEN, description="Latest QA review status for display approval (OPEN, APPROVED, REJECTED, etc.)")
    prediction_response_qa_registry: Optional[Union[str, List[Dict[str, Any]]]] = Field(default=None, description="Array of QA review records with timestamp, reviewer, status, comments")
    prediction_response_latest_qa_done_by: Optional[str] = Field(default=None, description="User ID who performed the latest QA review")
    prediction_response_latest_qa_timestamp_utc: Optional[datetime] = Field(default=None, description="Timestamp when the latest QA review was performed")

    retry_nb_attempts: Optional[int] = Field(default=None, ge=0, description="Number of retry attempts made (LLM predictions only)")
    prediction_errors: Optional[str] = Field(default=None, max_length=2000, description="Error message if prediction failed (max 2000 chars)")
    pulse_status: Optional[ObjectOverallStatus] = Field(ObjectOverallStatus.ACTIVE, description="ObjectOverallStatus enum: ACTIVE, STASHED, etc.")
    changelog_registry: Optional[Union[str, Dict[str, str]]] = Field(default=None, description="JSON changelog with timestamp keys (yyyymmddhhmm) and 'updater_id:: description' values")

    # --- Prediction Execution Context ---
    prediction_approach: Literal["single", "batch", "multistep"] = Field(..., description="Method used to generate this prediction")
    prediction_response_generation_approach: Optional[Literal["immediate", "deferred"]] = Field(default=None, description="Whether the prediction response was ingested immediately or deferred for later processing")
    prediction_batch_details: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Details of the batch prediction if applicable (e.g., batch size, number of batches)")
    prediction_response_info_from_model: Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Information about the model used for prediction (e.g., responseId, thinkingTokens, totalTokens, etc.")
    prediction_requested_datetime_utc: datetime = Field(..., description="When prediction was requested")
    prediction_response_generated_at_utc: Optional[datetime] = Field(default=None, description="When response was generated/received")
    prediction_info_details : Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Additional detailed information about the prediction process and context, such as prediction_cost_usd, latency metrics, etc.")
    request_raw_extract:Optional[str] = Field(default=None, max_length=100000, description="Raw extract of the prediction request for auditing and debugging purposes (max 100K chars)")
    response_raw_extract:Optional[str] = Field(default=None, max_length=100000, description="Raw extract of the prediction response for auditing and debugging purposes (max 100K chars)")
    response_storage_locations:Optional[Union[str, Dict[str, Any]]] = Field(default=None, description="Storage locations of the prediction response for auditing and debugging purposes")
    # thinking_trace: Optional[str] = Field(default=None, description="LLM reasoning trace if available (LLM predictions only)") THIS SHALL BE CAPTURED AS PART OF THE RESPONSE ITSELF

    # --- Metadata ---
    tags: Optional[str] = Field(default=None, max_length=500, description="Comma-separated tags for categorization and filtering (max 500 chars)")
    metadata: Optional[Union[str, Dict[str, Any]]] = Field(default_factory=dict, description="Additional metadata")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)
    
    def add_changelog(self, description: str, updater_id: str) -> None:
        """
        Add a changelog entry and increment metadata version.
        
        Args:
            description: Description of the change
            updater_id: ID of the user making the change
        """
        # Generate timestamp in yyyymmddhhmm format
        now = datetime.now(timezone.utc)
        timestamp_key = now.strftime("%Y%m%d%H%M")
        
        # Initialize changelog_registry if None
        if self.changelog_registry is None:
            self.changelog_registry = {}
        
        # Add entry with format "updater_id:: description"
        changelog_entry = f"{updater_id}:: {description}"
        self.changelog_registry[timestamp_key] = changelog_entry
        
        # Increment metadata version
        self.prediction_request_metadata_version += 1
        
        # Update audit fields
        self.updated_at = now
        self.updated_by = updater_id