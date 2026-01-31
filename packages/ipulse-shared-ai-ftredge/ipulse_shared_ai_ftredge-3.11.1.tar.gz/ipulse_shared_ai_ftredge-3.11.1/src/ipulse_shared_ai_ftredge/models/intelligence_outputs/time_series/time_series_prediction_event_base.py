"""Base model for prediction events (drivers, risks, milestones, opportunities)."""
from typing import ClassVar, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from ipulse_shared_base_ftredge.enums import ObjectOverallStatus


class TimeSeriesPredictionEventBase(BaseModel):
    """
    Base class for predicted events: drivers, risks, milestones, opportunities.
    
    Works for: LLM predictions (per-period or horizon-level), expert predictions.
    Maps to BigQuery table: prediction_events
    
    Event Types:
    - Period-level: pkdrv (period key driver), pkrisk (period key risk), etc.
    - Horizon-level: hkdrv (horizon key driver), hkrisk (horizon key risk), etc.
    
    Design Philosophy:
    - Single table for both period-level and horizon-level events
    - event_start/end_timestamp_utc capture the specific timeframe
    - prediction_horizon timestamps always present for filtering by overall horizon
    - event_name is encoded for uniqueness: {type}__{category}__{name_normalized}
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction_market__datasets.prediction_events"
    VERSION: ClassVar[int] = 1
    DOMAIN: ClassVar[str] = "oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "predevent"
    
    # --- Core Identity ---
    prediction_request_task_id: Optional[str] = Field(None, description="Reference to the prediction request task")
    prediction_request_metadata_version: int = Field(1, ge=1, description="Metadata version for tracking non-breaking changes (1, 2, 3...)")
    prediction_response_id: Optional[str] = Field(None, description="Response ID if different from task_id")
    prediction_response_generated_at_utc: Optional[datetime] = Field(None, description="When prediction was generated")
    event_normalized_name: str = Field(
        ...,
        description=(
            "Encoded name with format varying by event level:\n"
            "Period-level (h5y_s6m): {type}__{category}__{name}__{period_date} e.g. 'pkrisk__competitive_risks__amd_pressure__2026-05-14'\n"
            "Horizon-level (h3y_s3m): {type}__{category} e.g. 'hkrisk__competitive_risks'"
        )
    )
    
    # --- Subject Context ---
    subject_id: Optional[str] = Field(None, description="ID of the subject being predicted")
    subject_name: Optional[str] = Field(None, description="Name of the subject being predicted")
    
    # --- Model Context ---
    model_version_id: Optional[str] = Field(None, description="ID of the model version used")
    model_version_name: Optional[str] = Field(None, description="Name of the model version used")
    
    # --- Prediction Horizon Context (overall prediction timeframe - always present) ---
    prediction_horizon_start_timestamp_utc: Optional[datetime] = Field(
        None, description="Start of overall prediction horizon (e.g., today)"
    )
    prediction_horizon_end_timestamp_utc: Optional[datetime] = Field(
        None, description="End of overall prediction horizon (e.g., 3 or 5 years from now)"
    )
    
    # --- Period Timeframe Context (which timeseries period this event is associated with) ---
    period_start_timestamp_utc: Optional[datetime] = Field(
        None,
        description=(
            "Start of the timeseries period this event is associated with. "
            "For period-level events (h5y_s6m): start of the specific 6-month period. "
            "For horizon-level events (h3y_s3m): same as prediction_horizon_start_timestamp_utc"
        )
    )
    period_end_timestamp_utc: Optional[datetime] = Field(
        None,
        description=(
            "End of the timeseries period this event is associated with. "
            "For period-level events (h5y_s6m): end of the specific 6-month period. "
            "For horizon-level events (h3y_s3m): same as prediction_horizon_end_timestamp_utc"
        )
    )
    
    # --- Event Occurrence Timeframe (actual event start/end - can be very specific) ---
    event_start_timestamp_utc: Optional[datetime] = Field(
        None,
        description=(
            "Actual start date/time when this specific event is expected to begin occurring. "
            "Can be a specific date within the period (e.g., product launch on 2026-03-15). "
            "If unknown, can be same as period_start_timestamp_utc"
        )
    )
    event_end_timestamp_utc: Optional[datetime] = Field(
        None,
        description=(
            "Actual end date/time when this specific event is expected to stop occurring. "
            "Can be a specific date or range (e.g., 2-day event ending 2026-03-17). "
            "For ongoing events, can be same as period_end_timestamp_utc or None"
        )
    )
    
    # --- Event Details ---
    event_type: str = Field(
        ...,
        description="Event type: key_driver, key_risk, key_opportunity, key_milestone, key_event"
    )
    event_original_name: Optional[str] = Field(None, description="Human-readable name from LLM response")
    event_name: Optional[str] = Field(None, description="Alias or display name")
    event_category: str = Field(
        ...,
        description="Category enum (e.g., innovation_and_product_drivers, competitive_risks, macroeconomic_drivers)"
    )
    event_content: Optional[str] = Field(
        ...,
        description="Text content/description of the event"
    )
    event_description: Optional[str] = Field(
        None,
        description="JSON string details (compatible with Firestore dump)"
    )
    event_expected_impact_percent: Optional[float] = Field(None, description="Expected impact %")
    event_probability_percent: Optional[float] = Field(None, description="Probability %")
    
    # --- Additional Fields seen in Firestore ---
    prediction_snapshot_timestamp_utc: Optional[datetime] = Field(None, description="Snapshot timestamp")
    forecast_horizon_anchor_value_timestamp_utc: Optional[datetime] = Field(None, description="Anchor value timestamp")
    forecast_step: Optional[int] = Field(None, description="Forecast step number")
    period_label: Optional[str] = Field(None, description="Label for the period")
    event_exact_date_known: Optional[bool] = Field(None, description="Is exact date known?")
    
    # --- Metadata ---
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    # --- Audit Fields ---
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = Field(None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = Field(None)
    
    def to_bigquery_row(self) -> Dict[str, Any]:
        """Convert to BigQuery row format."""
        return self.model_dump(mode='json', exclude_none=False)
    
    @classmethod
    def from_bigquery_row(cls, row: Dict[str, Any]) -> "TimeSeriesPredictionEventBase":
        """Create instance from BigQuery row."""
        return cls(**row)
    
    def is_horizon_level_event(self) -> bool:
        """
        Check if this is a horizon-level event (vs period-level).
        Horizon-level events have period timeframe equal to the full prediction horizon.
        """
        return (
            self.period_start_timestamp_utc == self.prediction_horizon_start_timestamp_utc
            and self.period_end_timestamp_utc == self.prediction_horizon_end_timestamp_utc
        )
    
    def is_period_level_event(self) -> bool:
        """
        Check if this is a period-level event (vs horizon-level).
        Period-level events have period timeframe smaller than the full prediction horizon.
        """
        return not self.is_horizon_level_event()
