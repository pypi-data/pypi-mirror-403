"""Base model for investment ratings and horizon-level analysis."""
from typing import ClassVar, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from ipulse_shared_base_ftredge.enums import ObjectOverallStatus


class TimeSeriesPredictionRatingBase(BaseModel):
    """
    Base class for horizon-level investment ratings and analysis.
    
    Works for: LLM predictions, expert predictions, quant model summaries.
    Maps to BigQuery table: prediction_based_investment_rating
    
    Design Philosophy:
    - Flexible Optional fields to work across different model types
    - LLM models populate scenario fields
    - Quant models use key_influencing_factors_summary_for_horizon instead
    - All drivers/risks for LLM are stored in prediction_events table (not here)
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction_market__datasets.prediction_based_investment_rating"
    VERSION: ClassVar[int] = 1
    DOMAIN: ClassVar[str] = "oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "predrating"
    
    # --- Core Identity ---
    prediction_request_task_id: str = Field(..., description="Reference to the prediction request task")
    prediction_request_metadata_version: int = Field(1, ge=1, description="Metadata version for tracking non-breaking changes (1, 2, 3...)")
    prediction_response_id: Optional[str] = Field(None, description="Response ID if different from task_id")
    prediction_response_generated_at_utc: datetime = Field(..., description="When this analysis was generated")
    
    # --- Target Context ---
    subject_id: str = Field(..., description="ID of the subject being predicted")
    subject_name: str = Field(..., description="Name of the subject being predicted")
    
    # --- Model Context ---
    model_version_id: str = Field(..., description="ID of the model version used")
    
    # --- Horizon Context ---
    prediction_horizon_timeframe: Optional[str] = Field(None, description="Horizon timeframe (e.g., '1Y', '5Y')")
    prediction_horizon_timeframe_days: Optional[int] = Field(None, description="Horizon timeframe in days")
    prediction_values_start_timestamp_utc: datetime = Field(..., description="Horizon start timestamp")
    prediction_values_end_timestamp_utc: datetime = Field(..., description="Horizon end timestamp")
    
    # --- Investment Rating (common to all models) ---
    investment_rating_by_model: Optional[str] = Field(None, description="Rating from model: sell_all, partially_sell, hold, buy, strong_buy")
    investment_rating_confidence_subjective_by_model: Optional[float] = Field(None, ge=0.0, le=100.0, description="Confidence score (0-100)")
    investment_rating_by_formula: Optional[str] = Field(None, description="Rating from internal formula based on return/volatility")
    investment_rating_explanation: Optional[str] = Field(None, description="Manual explanation of how rating was calculated")
    advised_to_reevaluate_rating_by_timestamp_utc: Optional[datetime] = Field(None, description="When to reevaluate this rating")
    
    # --- Investment Thesis Scenarios (LLM only, ~80-120 words each) ---
    bull_case_scenario: Optional[str] = Field(None, description="Bull case scenario (LLM predictions only)")
    bear_case_scenario: Optional[str] = Field(None, description="Bear case scenario (LLM predictions only)")
    most_reasonable_investment_thesis_scenario: Optional[str] = Field(None, description="Most reasonable scenario (LLM predictions only)")
    
    # --- Analysis Summaries (Quant models only - LLM uses prediction_events table) ---
    key_influencing_factors_summary_for_horizon: Optional[str] = Field(
        None,
        description="JSON string with feature importance, SHAP values (Quant models only)"
    )

    # --- Price Targets & Returns ---
    bull_case_price_target: Optional[float] = Field(None, description="Bull case price target")
    bear_case_price_target: Optional[float] = Field(None, description="Bear case price target")
    most_reasonable_price_target: Optional[float] = Field(None, description="Reasonable price target")
    latest_known_price: Optional[float] = Field(None, description="Latest known price passed to model")
    latest_known_price_timestamp_utc: Optional[datetime] = Field(None, description="Timestamp of latest known price")
    forecasted_return_percent_for_horizon: Optional[float] = Field(None, description="Calculated forecasted return %")
    price_currency: Optional[str] = Field(None, description="Currency for prices and price targets")
    
    # --- Metadata ---
    prediction_snapshot_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Prediction as-of time")
    pulse_status: Optional[ObjectOverallStatus] = Field(ObjectOverallStatus.ACTIVE, description="Overall status of this rating record")
    changelog_registry: Optional[Dict[str, str]] = Field(None, description="JSON changelog with timestamp keys and 'updater_id:: description' values")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    # --- Audit Fields ---
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(...)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)
    
    def add_changelog(self, description: str, updater_id: str) -> None:
        """
        Add a changelog entry and increment metadata version.
        
        Args:
            description: Description of the change
            updater_id: ID of the user making the change
        """
        now = datetime.now(timezone.utc)
        timestamp_key = now.strftime("%Y%m%d%H%M")
        
        if self.changelog_registry is None:
            self.changelog_registry = {}
        
        changelog_entry = f"{updater_id}:: {description}"
        self.changelog_registry[timestamp_key] = changelog_entry
        
        self.prediction_request_metadata_version += 1
        self.updated_at = now
        self.updated_by = updater_id
    
    def to_bigquery_row(self) -> Dict[str, Any]:
        """Convert to BigQuery row format."""
        return self.model_dump(mode='json', exclude_none=False)
    
    @classmethod
    def from_bigquery_row(cls, row: Dict[str, Any]) -> "TimeSeriesPredictionRatingBase":
        """Create instance from BigQuery row."""
        return cls(**row)
