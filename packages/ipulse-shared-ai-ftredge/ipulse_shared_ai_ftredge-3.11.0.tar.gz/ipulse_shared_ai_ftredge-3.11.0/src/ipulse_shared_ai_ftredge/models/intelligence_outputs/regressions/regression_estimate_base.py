"""Pydantic model for regression estimation results."""
from typing import ClassVar, Dict, Any, Optional, List
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from ipulse_shared_base_ftredge import AIModelStatus, ProgressStatus


class RegressionEstimate(BaseModel):
    """
    Regression estimation results model optimized for BigQuery storage.
    Focused specifically on regression predictions with intervals and residuals.
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "regressionestimate"

    # --- Estimate Identity ---
    estimate_id: str = Field(..., description="The unique identifier for this regression estimate.")
    target_object_id: str = Field(..., description="The unique identifier of the estimated object.")
    target_object_name: str = Field(..., description="The short name of the estimated object for easy reference.")
    target_object_domain: str = Field(..., description="The domain of the estimated object.")
    
    # --- Model References ---
    model_spec_id: str = Field(..., description="Reference to the AIModelSpecification used.")
    training_run_id: Optional[str] = Field(None, description="Reference to the AITrainingRun if applicable.")
    model_version_id: str = Field(..., description="Reference to the AIModelVersion used.")
    model_status: AIModelStatus = Field(..., description="Current lifecycle status of the model version used.")
    
    # --- Model Deployment Context (Optional - for MLOps tracking) ---
    model_serving_instance_id: Optional[str] = Field(None, description="ID of the specific serving instance used for this estimate")
    serving_instance_name: Optional[str] = Field(None, description="Name of the serving instance used for this estimate")
    
    # --- External API Context (For cloud-based regression models) ---
    api_path: Optional[str] = Field(None, description="API call ID for tracking external model calls.")
    api_call_cost: Optional[float] = Field(None, description="Cost of the API call in USD.")
    
    # --- Input Context (Multi-dimensional sources) ---
    input_data_sources_used: List[Dict[str, Any]] = Field(default_factory=list, description="Input data sources used for this regression estimate with their characteristics.")
    # Example structure:
    # {
    #   "schema_id": "real_estate_features",
    #   "schema_name": "Property Valuation Dataset", 
    #   "rows_count": 1,  # single property being estimated
    #   "index_or_date_column_name": "property_id",  # primary identifier column
    #   "feature_columns_used": ["sq_footage", "bedrooms", "neighborhood_score", "market_trends"],
    #   "temporal_range_start": "2024-01-01",
    #   "temporal_range_end": "2024-12-31",
    #   "data_freshness_minutes": 60,
    #   "preprocessing_applied": {"log_transform": ["sq_footage"], "scaling": "standard"},
    #   "dataset_filter_used": {"property_type": "residential", "min_sqft": 500},
    #   "dataset_scope": "regional_comparables"
    # }
    
    feature_store_version: Optional[str] = Field(None, description="Version of feature store used.")

    # --- Estimate Context ---
    estimate_datetime: datetime = Field(..., description="Timestamp when the estimate was made.")
    estimate_environment: str = Field(..., description="Environment where estimate was made, e.g., 'production', 'staging'.")
    estimate_status: ProgressStatus = Field(..., description="Status of the estimation process.")
    estimate_error: Optional[str] = Field(None, description="Error message if the estimation failed.")
    
    # --- REGRESSION CORE DATA ---
    estimated_values: List[float] = Field(..., description="The main estimated numerical values.")
    confidence_scores: Optional[List[float]] = Field(None, description="Confidence scores for each estimate.")
    
    # --- REGRESSION INTERVALS ---
    prediction_intervals_lower: Optional[List[float]] = Field(None, description="Lower prediction intervals.")
    prediction_intervals_upper: Optional[List[float]] = Field(None, description="Upper prediction intervals.")
    interval_confidence_level: Optional[float] = Field(None, description="Confidence level for intervals, e.g., 0.95.")
    
    # --- REGRESSION DIAGNOSTICS ---
    residual_estimates: Optional[List[float]] = Field(None, description="Estimated residuals from the model.")
    r_squared: Optional[float] = Field(None, description="R-squared value for model fit quality.")
    adjusted_r_squared: Optional[float] = Field(None, description="Adjusted R-squared value.")
    mean_squared_error: Optional[float] = Field(None, description="Mean squared error of the estimates.")
    root_mean_squared_error: Optional[float] = Field(None, description="Root mean squared error.")
    mean_absolute_error: Optional[float] = Field(None, description="Mean absolute error.")
    
    # --- FEATURE IMPORTANCE (Regression-specific) ---
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Importance scores for input features.")
    feature_coefficients: Optional[Dict[str, float]] = Field(None, description="Regression coefficients for features.")
    intercept: Optional[float] = Field(None, description="Regression intercept term.")
        
    # --- Quality and Performance ---
    estimate_quality_score: Optional[float] = Field(None, description="Overall quality/reliability score.")
    anomaly_flags: Optional[List[bool]] = Field(None, description="Boolean flags for anomalous estimates.")
    uncertainty_scores: Optional[List[float]] = Field(None, description="Uncertainty scores for each estimate.")
    
    # --- Performance Metrics ---
    estimate_latency_ms: Optional[float] = Field(None, description="Time taken to generate estimate in milliseconds.")
    estimate_cost: Optional[float] = Field(None, description="Cost of generating estimate in USD.")
    compute_resources_used: Optional[Dict[str, Any]] = Field(None, description="Compute resources used.")
    
    # --- Metadata ---
    estimate_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional technical metadata.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization and filtering.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)
