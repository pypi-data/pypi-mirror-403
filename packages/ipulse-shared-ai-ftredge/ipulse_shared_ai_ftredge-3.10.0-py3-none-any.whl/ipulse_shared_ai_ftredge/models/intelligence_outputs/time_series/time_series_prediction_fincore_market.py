"""Market asset investment rating and analysis (LLM output)."""
from typing import ClassVar, Optional, Dict, Any
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from ipulse_shared_base_ftredge.enums import AssetRating, ObjectOverallStatus
from ..utils import (
    MarketKeyRisks, MarketKeyDrivers
)
# from .time_series_prediction_base import TimeSeriesPredictionValueBase

# class TimeSeriesPredictionValuesFincoreMarket(TimeSeriesPredictionValueBase):
#     """
#     Extended prediction values class to include market asset-specific fields.
#     Inherits from TimeSeriesPredictionValues and adds market-specific analysis fields.
#     """
#     SCHEMA_ID: ClassVar[str] = ""
#     SCHEMA_NAME: ClassVar[str] = ""
#     VERSION: ClassVar[int] = 1
#     DOMAIN: ClassVar[str] = "dp_oracle_fincore_market_prediction"
#     OBJ_REF: ClassVar[str] = "tspredvalsfincmarkt"

#     # --- Market-Specific Analysis (for Opinionated market predictions i.e. LLMs, Experts, Public etc.) ---
#     key_milestones_and_events: Optional[str] = Field(None, description="Key milestones and events affecting this prediction point")
#     most_influencing_technical_factors: Optional[str] = Field(None, description="Technical analysis factors")
#     most_influencing_fundamental_factors: Optional[str] = Field(None, description="Fundamental analysis factors")

class FincorePredictionAssetRating(BaseModel):
    """
    Investment rating and qualitative analysis for market assets (equity, crypto, fund).
    This is one of the outputs produced by LLM market predictions (alongside prediction values).
    
    Maps to BigQuery table: prediction_based_investment_rating
    Extends the base rating class with market-specific fields.
    
    NOTE: For LLM predictions, drivers and risks are stored in prediction_events table, NOT here.
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction_market__datasets.prediction_based_investment_rating"
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "assetrating"
    
    # --- Core Identity ---
    prediction_request_task_id: str = Field(..., description="Reference to the prediction request task")
    prediction_request_metadata_version: int = Field(1, ge=1, description="Metadata version for tracking non-breaking changes (1, 2, 3...)")
    prediction_response_id: Optional[str] = Field(None, description="Response ID if different from task_id")
    prediction_response_generated_at_utc: datetime = Field(..., description="When this analysis was generated")
    
    # --- Target Context ---
    subject_id: str = Field(..., description="ID of the asset being analyzed")
    subject_name: str = Field(..., description="Name of the asset being analyzed")
    subject_category: str = Field(..., description="Asset category: equity, crypto, fund")
    subject_category_detailed: str = Field(..., description="Detailed category: common_stock, etf, bitcoin, mutual_fund")
    contract_or_ownership_type: str = Field(..., description="Type: spot, adr, gdr, futures")
    predicted_records_type: str = Field(..., description="Type of records predicted (e.g., 'eod_adjc')")
    unit: str = Field(..., description="Unit: USD, EUR, BTC, etc.")
    
    # --- Model Context ---
    model_version_id: str = Field(..., description="ID of the model version used")
    model_version_name: str = Field(..., description="Name of the model version used")
    model_serving_instance_id: Optional[str] = Field(None, description="Serving instance ID")
    model_configs_used: Optional[Dict[str, Any]] = Field(None, description="Model configuration (JSON)")
    knowledge_used_by_model: Optional[Dict[str, Any]] = Field(None, description="Knowledge parameters (JSON)")
    
    # --- Horizon Context ---
    prediction_horizon_end_timestamp_utc: datetime = Field(..., description="End of prediction horizon")
    prediction_horizon_timeframe: str = Field(..., description="Horizon timeframe: 5Y, 3Y, etc.")
    
    # --- Investment Rating ---
    forecasted_return_percent_for_horizon: Optional[float] = Field(None, description="Calculated forecasted return %")
    investment_rating_by_model: Optional[str] = Field(None, description="Rating from model: sell_all, partially_sell, hold, buy, strong_buy")
    investment_rating_by_formula: Optional[str] = Field(None, description="Rating from internal formula")
    rating_subjective_confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence (0-1)")
    advised_to_reevaluate_rating_by: Optional[datetime] = Field(None, description="When to reevaluate")
    
    # --- Investment Thesis Scenarios (LLM predictions, ~80-120 words each) ---
    bull_case_scenario: Optional[str] = Field(None, description="Bull case scenario")
    bear_case_scenario: Optional[str] = Field(None, description="Bear case scenario")
    most_reasonable_investment_thesis_scenario: Optional[str] = Field(None, description="Most reasonable scenario")
    
    # --- Analysis Summaries (for Quant models only - LLM uses prediction_events) ---
    key_influencing_factors_summary_for_horizon: Optional[str] = Field(None, description="JSON with feature importance (Quant only)")

    # --- Metadata ---
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
    def from_bigquery_row(cls, row: Dict[str, Any]) -> "FincorePredictionAssetRating":
        """Create instance from BigQuery row."""
        return cls(**row)
