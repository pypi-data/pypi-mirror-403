"""Pydantic model for classification inference results."""
from typing import ClassVar, Dict, Any, Optional, List
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from ipulse_shared_base_ftredge import AIModelStatus, ProgressStatus


class ClassificationInference(BaseModel):
    """
    Classification inference results model optimized for BigQuery storage.
    Focused specifically on classification predictions with probabilities and classes.
    """
    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "classificationresult"
    
    # --- Result Identity ---
    result_id: str = Field(..., description="The unique identifier for this classification result.")
    target_object_id: str = Field(..., description="The unique identifier of the classified object.")
    target_object_name: str = Field(..., description="The short name of the classified object for easy reference.")
    target_object_domain: str = Field(..., description="The domain of the classified object.")
    
    # --- Model References ---
    model_spec_id: str = Field(..., description="Reference to the AIModelSpecification used.")
    training_run_id: Optional[str] = Field(None, description="Reference to the AITrainingRun if applicable.")
    model_version_id: str = Field(..., description="Reference to the AIModelVersion used.")
    model_status: AIModelStatus = Field(..., description="Current lifecycle status of the model version used.")
    
    # --- Model Deployment Context (Optional - for MLOps tracking) ---
    model_serving_instance_id: Optional[str] = Field(None, description="ID of the specific serving instance used for this classification")
    model_serving_instance_name: Optional[str] = Field(None, description="Name of the serving instance used for this classification")
    
    # --- External API Context (For cloud-based classification models) ---
    api_path: Optional[str] = Field(None, description="API call ID for tracking external model calls.")
    api_call_cost: Optional[float] = Field(None, description="Cost of the API call in USD.")
    
    # --- Input Context (Multi-dimensional sources) ---
    input_data_sources_used: List[Dict[str, Any]] = Field(default_factory=list, description="Input data sources used for this classification with their characteristics.")
    # Example structure:
    # {
    #   "schema_id": "customer_behavior_features",
    #   "schema_name": "Customer Behavior Analytics",
    #   "rows_count": 1,  # single record being classified
    #   "index_or_date_column_name": "customer_id",  # primary identifier column
    #   "feature_columns_used": ["purchase_frequency", "avg_order_value", "recency_score"],
    #   "temporal_range_start": "2024-01-01",
    #   "temporal_range_end": "2024-12-31",
    #   "data_freshness_minutes": 5,
    #   "preprocessing_applied": {"normalization": "min_max", "encoding": "one_hot"},
    #   "dataset_filter_used": {"active_customers_only": True},
    #   "dataset_scope": "production_features"
    # }
    
    feature_store_version: Optional[str] = Field(None, description="Version of feature store used.")

    # --- Classification Context ---
    inference_datetime: datetime = Field(..., description="Timestamp when the classification was made.")
    inference_environment: str = Field(..., description="Environment where inference was made, e.g., 'production', 'staging'.")
    inference_status: ProgressStatus = Field(..., description="Status of the classification process.")
    inference_error: Optional[str] = Field(None, description="Error message if the classification failed.")
    
    # --- CLASSIFICATION CORE DATA ---
    predicted_classes: List[str] = Field(..., description="Predicted class labels for each input.")
    class_probabilities: Dict[str, List[float]] = Field(..., description="Probabilities for each class.")
    confidence_scores: Optional[List[float]] = Field(None, description="Overall confidence scores for predictions.")
    
    # --- CLASSIFICATION DETAILS ---
    classification_threshold: Optional[float] = Field(None, description="Decision threshold used (binary classification).")
    num_classes: int = Field(..., description="Total number of possible classes.")
    class_names: List[str] = Field(..., description="Names of all possible classes.")
    
    # --- MULTI-CLASS SPECIFICS ---
    top_k_classes: Optional[List[List[str]]] = Field(None, description="Top-K predicted classes for each input.")
    top_k_probabilities: Optional[List[List[float]]] = Field(None, description="Probabilities for top-K classes.")
    entropy_scores: Optional[List[float]] = Field(None, description="Entropy scores indicating prediction uncertainty.")
    
    # --- CLASSIFICATION METRICS ---
    precision_scores: Optional[Dict[str, float]] = Field(None, description="Per-class precision scores if available.")
    recall_scores: Optional[Dict[str, float]] = Field(None, description="Per-class recall scores if available.")
    f1_scores: Optional[Dict[str, float]] = Field(None, description="Per-class F1 scores if available.")
    overall_accuracy: Optional[float] = Field(None, description="Overall accuracy if ground truth available.")
    
    # --- FEATURE IMPORTANCE (Classification-specific) ---
    feature_importance: Optional[Dict[str, float]] = Field(None, description="Importance scores for input features.")
    feature_contributions: Optional[Dict[str, List[float]]] = Field(None, description="Per-prediction feature contributions.")
    
    # --- Quality and Performance ---
    result_quality_score: Optional[float] = Field(None, description="Overall quality/reliability score.")
    anomaly_flags: Optional[List[bool]] = Field(None, description="Boolean flags for anomalous classifications.")
    uncertainty_scores: Optional[List[float]] = Field(None, description="Uncertainty scores for each classification.")
    
    # --- Performance Metrics ---
    inference_latency_ms: Optional[float] = Field(None, description="Time taken for classification in milliseconds.")
    inference_cost: Optional[float] = Field(None, description="Cost of generating classification in USD.")
    compute_resources_used: Optional[Dict[str, Any]] = Field(None, description="Compute resources used.")
    
    # --- Metadata ---
    inference_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional technical metadata.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization and filtering.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)
