"""Common base model for all time series predictions (LLM and Quant)."""
from typing import ClassVar, Dict, Any, Literal, Optional, Union, List
from datetime import datetime, timezone
from pydantic import Field, BaseModel, field_validator
from ipulse_shared_base_ftredge.enums import (ModelOutputPurpose, ProgressStatus, TimeFrame, ReviewStatus)

class TimeSeriesPredictionValueBase(BaseModel):
    """Separate class for actual prediction values that reference a prediction log."""

    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "dp_oracle_prediction"
    OBJ_REF: ClassVar[str] = "tspredvalues"
    
    # --- Core Identity ---
    prediction_request_id: str = Field(..., description="Reference to the TimeSeriesPredictionLog that generated these values")
    prediction_response_id: Optional[str] = Field(None, description="Same or different from prediction_request_id, used to link to the response entity if applicable")
    predicted_on_timestamp_utc: datetime = Field(..., description="When these prediction values were generated")
    subject_id: Optional[str] = Field(..., description="ID of the subject being predicted (for easier querying without joins)")
    subject_name: Optional[str] = Field(..., description="Name of the subject being predicted (for easier querying without joins)")
    record_type: Optional[str] = Field(..., description="Type of records being predicted, e.g., 'eod_adjc', 'intraday_adjc', 'eod_sentiment_score' etc")
    unit: Optional[str] = Field(None, description="Unit of measurement for the predicted values, e.g., 'USD', 'points', 'percentage'")
    model_version_id: Optional[str] = Field(..., description="ID of the model version or Analyst used for this prediction (for easier querying without joins)")
    model_version_name: Optional[str] = Field(..., description="Name of the model version or Analyst used for this prediction (for easier querying without joins)")
    # --- Value Point Structure ---
    forecast_timestamp_utc: Union[datetime, str] = Field(..., description="Timestamp of the prediction in datetime utc format or YYYY-MM-DD format")
    value: float = Field(..., gt=0, description="Predicted value (must be > 0, rounded to 2 decimal places)")
    upper_bound: Optional[float] = Field(None, gt=0, description="Upper bound of the prediction confidence interval (must be > 0, rounded to 2 decimal places)")
    lower_bound: Optional[float] = Field(None, gt=0, description="Lower bound of the prediction confidence interval (must be > 0, rounded to 2 decimal places)")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the prediction (0-1, rounded to 4 decimal places)")

    # --- Time Series Components (for quant models) ---
    trend_component: Optional[float] = Field(None, description="Trend component for this prediction point (rounded to 4 decimal places)")
    seasonal_component: Optional[float] = Field(None, description="Seasonal component for this prediction point (rounded to 4 decimal places)")
    residual_component: Optional[float] = Field(None, description="Residual component for this prediction point (rounded to 4 decimal places)")
    
     # --- Quality Indicators ---
    is_anomaly: Optional[bool] = Field(None, description="Whether this prediction point is flagged as anomalous. This field will be populated by reviewer systems.")
    uncertainty_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Uncertainty score for this prediction point (0-1, rounded to 4 decimal places)")

    # --- Metadata ---
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata for this prediction value")
    
    # --- Field Validators for Decimal Precision ---
    @field_validator(
        'value',
        'upper_bound', 
        'lower_bound',
        mode='after'
    )
    @classmethod
    def round_price_values_to_2_decimals(cls, v: Optional[float]) -> Optional[float]:
        """Round price/value fields to 2 decimal places to prevent floating point artifacts."""
        if v is None:
            return None
        return round(v, 2)
    
    @field_validator(
        'confidence_score',
        'trend_component',
        'seasonal_component', 
        'residual_component',
        'uncertainty_score',
        mode='after'
    )
    @classmethod
    def round_scores_to_4_decimals(cls, v: Optional[float]) -> Optional[float]:
        """Round confidence scores and components to 4 decimal places for precision without bloat."""
        if v is None:
            return None
        return round(v, 4)
