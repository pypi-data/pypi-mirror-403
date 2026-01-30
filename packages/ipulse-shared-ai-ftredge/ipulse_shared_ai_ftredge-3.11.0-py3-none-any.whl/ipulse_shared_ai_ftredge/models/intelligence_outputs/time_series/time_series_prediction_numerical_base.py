"""Common base model for all time series predictions (LLM and Quant)."""
from typing import ClassVar, Dict, Any, Literal, Optional, Union, List
from datetime import datetime, timezone
from pydantic import Field, BaseModel, field_validator
from ipulse_shared_base_ftredge.enums import (ModelOutputPurpose, ProgressStatus, TimeFrame, ReviewStatus)

class TimeSeriesPredictionNumericalBase(BaseModel):
    """Separate class for actual prediction values that reference a prediction log."""

    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "dp_oracle_prediction"
    OBJ_REF: ClassVar[str] = "tspredvalues"
    
    # --- Core Identity ---
    prediction_request_id: Optional[str] = Field(None, description="Reference to the TimeSeriesPredictionLog that generated these values")
    prediction_response_id: Optional[str] = Field(None, description="Same or different from prediction_request_id, used to link to the response entity if applicable")
    prediction_snapshot_timestamp_utc: Optional[datetime] = Field(None, description="Snapshot time of the prediction (was predicted_on_timestamp_utc)")
    
    # --- Prediction Type & Units ---
    predicted_values_type: Optional[str] = Field(None, description="Type of records being predicted (was record_type), e.g., 'eod_close_price'")
    predicted_value_unit: Optional[str] = Field(None, description="Unit of measurement (was unit), e.g., 'USD'")
    values_mode: Optional[str] = Field(None, description="e.g. 'original'")
    
    # --- Step Info ---
    forecast_step: Optional[int] = Field(None, description="Sequence number of the forecast step")
    forecast_timestamp_utc: Union[datetime, str] = Field(..., description="Timestamp of the prediction in datetime utc format or YYYY-MM-DD format")
    
    # --- Absolute Values ---
    predicted_value: Optional[float] = Field(None, gt=0, description="Predicted value (was value)")
    predicted_value_upper_bound: Optional[float] = Field(None, gt=0, description="Upper bound (was upper_bound)")
    predicted_value_lower_bound: Optional[float] = Field(None, gt=0, description="Lower bound (was lower_bound)")
    
    # --- Percentage Change Metrics (Step-over-Step & Compounded) ---
    predicted_step_over_step_change_percent: Optional[float] = Field(None, description="Step-over-step percentage change")
    predicted_step_over_step_change_upper_bound_percent: Optional[float] = Field(None, description="Upper bound for step-over-step change")
    predicted_step_over_step_change_lower_bound_percent: Optional[float] = Field(None, description="Lower bound for step-over-step change")
    predicted_step_compounded_change_percent: Optional[float] = Field(None, description="Compounded percentage change from anchor")

    # --- Anchors ---
    forecast_horizon_anchor_value: Optional[float] = Field(None, description="Anchor value used for calculating changes")
    forecast_horizon_anchor_value_timestamp_utc: Optional[datetime] = Field(None, description="Timestamp of the anchor value")

    # --- Confidence & Quality ---
    predicted_value_confidence_interval: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence/Probability (0-1) (was confidence_score)")
    is_anomaly: Optional[bool] = Field(None, description="Whether this prediction point is flagged as anomalous")
    
    # --- Components (Generic) ---
    prediction_components: Optional[Any] = Field(None, description="Detailed components (trend, seasonal, etc) if available")

    # --- Audit & System ---
    tags: Optional[List[str]] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    prediction_request_metadata_version: Optional[int] = Field(None)
    
    created_at: Optional[datetime] = Field(None)
    updated_at: Optional[datetime] = Field(None)
    created_by: Optional[str] = Field(None)
    updated_by: Optional[str] = Field(None)

    # --- Field Validators for Decimal Precision ---
    @field_validator(
        'predicted_value',
        'predicted_value_upper_bound', 
        'predicted_value_lower_bound',
        'forecast_horizon_anchor_value',
        mode='after'
    )
    @classmethod
    def round_price_values_to_2_decimals(cls, v: Optional[float]) -> Optional[float]:
        """Round price/value fields to 2 decimal places."""
        if v is None:
            return None
        return round(v, 2)
    
    @field_validator(
        'predicted_step_over_step_change_percent',
        'predicted_step_over_step_change_upper_bound_percent',
        'predicted_step_over_step_change_lower_bound_percent',
        'predicted_step_compounded_change_percent',
        mode='after'
    )
    @classmethod
    def round_percentages_to_2_decimals(cls, v: Optional[float]) -> Optional[float]:
        """Round percentage fields to 2 decimal places."""
        if v is None:
            return None
        return round(v, 2)
    
    @field_validator(
        'predicted_value_confidence_interval',
        mode='after'
    )
    @classmethod
    def round_scores_to_4_decimals(cls, v: Optional[float]) -> Optional[float]:
        """Round confidence scores to 4 decimal places."""
        if v is None:
            return None
        return round(v, 4)
