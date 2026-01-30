# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import List, Optional, Dict, Any, ClassVar, Tuple
from datetime import datetime, timezone
from pydantic import Field, BaseModel
from ipulse_shared_base_ftredge import TimeFrame, AIModelTrainingType



class AITrainingConfiguration(BaseModel):
    """
    📋 AI TRAINING CONFIGURATION - The Training Recipe
    
    CORE CONCEPT:
    This defines HOW to train a specific model specification - the training strategy, approach, 
    and general data characteristics. It's a reusable "recipe" that creates a lineage of model versions.
    
    KEY RELATIONSHIPS:
    • ONE model specification → MULTIPLE training configurations  
    • ONE training configuration → MULTIPLE training runs
    • ONE training configuration → MULTIPLE model versions (over time)
    
    TRAINING STRATEGY EXAMPLES:
    • Daily retraining config: "Retrain completely every day with last 2 years of data"
    • Weekly fine-tuning config: "Fine-tune every week with last 30 days of data" 
    • Monthly full retraining config: "Complete retrain monthly with all historical data"
    
    DATA BLUEPRINT vs ACTUAL DATA:
    • Training Config: Defines GENERAL data characteristics (e.g., "market data + sentiment, 2-year window")
    • Training Run: Specifies EXACT data used (e.g., "market_data_v2.3, 2022-01-01 to 2024-01-01, 45,231 records")
    
    TRAINING RUN SHARING:
    A single training run CAN serve multiple training configurations:
    • Initial training run → shared by daily and weekly configs
    • Complete retraining run → shared by multiple strategies
    • But subsequent fine-tuning runs diverge as models evolve differently
    
    TARGET CRITERIA FLEXIBILITY:
    {
        "domain": ["fincore_market_assets"],
        "asset_class": ["equity"], 
        "market_cap_min": 1000000000,
        "exchange": ["NYSE", "NASDAQ"],
        "specific_object_ids": ["AAPL", "GOOGL"]  # if needed
    }
    """

    VERSION: ClassVar[int] = 2
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aiupdateconfig"

    training_config_id: str = Field(..., description="The unique identifier for this training configuration.")
    model_spec_id: str = Field(..., description="The UID of the AIModel this configuration belongs to.")
    training_config_short_name: str = Field(..., description="A short name for this training configuration, e.g., 'Daily_retrain_2yr_market_sentiment'.")
    
    # --- Target Selection Strategy ---
    target_subjects_selection_criteria: Dict[str, Any] = Field(..., description="Criteria for selecting targets for this training configuration lineage.")
    prediction_variables: List[str] = Field(..., description="List of variables being predicted, e.g., ['close_price', 'volatility'].")
    
    # --- Training Data Blueprint (General Characteristics) ---
    data_sources_blueprint: List[Dict[str, Any]] = Field(..., description="Blueprint of data sources - defines general characteristics, not specific versions/dates.")
    # Example structure:
    # {
    #   "schema_id": "market_eod_data_realtime",
    #   "schema_name": "Market EOD Real-time Feed",
    #   "rows_count": "4000",  # general window approach
    #   "index_or_date_column_name": "date_id",  # primary temporal/index column
    #   "feature_columns_used": ["open_normalized", "volume_log", "sentiment_score"],
    #   "temporal_range_strategy": "rolling_window",  # general approach
    #   "data_freshness_target": "15_minutes_max",  # target freshness
    #   "preprocessing_applied": {"outlier_removal": True, "normalization": "z_score"},
    #   "dataset_filter_used": {"asset_category_pulse":"equity", "trading_status": "traded_on_exchange"},
    #   "dataset_scope": "training_universe"
    # }
    
    feature_engineering_strategy: Optional[Dict[str, Any]] = Field(default=None, description="High-level feature engineering strategy, not specific pipeline details.")
    data_splitting_strategy: Optional[Dict[str, Any]] = Field(default=None, description="General data splitting approach, e.g., {'method': 'temporal', 'validation_approach': 'rolling_window'}.")
    
    # --- Training Strategy and Schedule ---
    training_strategy: Tuple[AIModelTrainingType, TimeFrame] = Field(..., description="The training strategy: (type, frequency) e.g., (COMPLETE_RETRAINING, DAILY)")
    training_stopping_criteria: Optional[str] = Field(default=None, description="General stopping criteria approach, e.g., 'Early stopping based on validation loss'.")
    hyperparameters_template: Optional[Dict[str, Any]] = Field(default=None, description="Template hyperparameters for this training configuration lineage.")
    
    # --- Expected Performance and Cost ---
    training_config_overall_performance_score: Optional[float] = Field(default=None, description="Expected performance score for this config ")
    avg_monthly_cost_usd: Optional[float] = Field(default=None, description="Estimated monthly cost for this training configuration.")
    avg_training_duration_hours: Optional[float] = Field(default=None, description="Estimated training duration per run in hours.")
    
    # --- Metadata ---
    notes: Optional[str] = Field(default=None, description="Strategic notes about this training configuration approach.")
    strengths: Optional[str] = Field(default=None, description="Expected strengths of this training approach.")
    weaknesses: Optional[str] = Field(default=None, description="Known limitations of this training approach.")
    recommended_use_cases: Optional[List[str]] = Field(default=None, description="Recommended scenarios for using this training configuration.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization, e.g., 'production', 'experimental'.")

    # --- Namespace and Identity ---
    pulse_namespace: Optional[str] = Field(default=None, description="Namespace for this AI training configuration.")
    namespace_id_seed_phrase: Optional[str] = Field(default=None, description="Seed phrase used for namespace-based UUID generation.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)