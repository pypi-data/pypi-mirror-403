# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import List, Optional, Dict, Any, ClassVar, Literal
from pydantic import Field, BaseModel
from datetime import datetime, timezone
from ipulse_shared_base_ftredge import AIModelStatus, TimeFrame


class AIModelPerformanceEvaluation(BaseModel):
    """
    Tracks actual performance of deployed models based on real outcomes.
    Created when ground truth becomes available for previously made predictions.
    Enables continuous model monitoring and performance degradation detection.
    """

    SCHEMA_ID: ClassVar[str] = ""
    SCHEMA_NAME: ClassVar[str] = ""
    VERSION: ClassVar[int] = 2
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aimodelperformanceevaluation"

    # --- Identity and References ---
    evaluation_id: str = Field(..., description="Unique identifier for this performance evaluation.")
    model_spec_id: str = Field(..., description="Reference to the AIModelSpecification being evaluated.")
    model_version_id: str = Field(..., description="Reference to the specific AIModelVersion being evaluated.")
    target_object_id: str = Field(..., description="The unique identifier of the Predictable Object.")
    target_object_name: str = Field(..., description="The short name of the Predictable Object for easy reference.")
    target_object_domain: str = Field(..., description="The domain of the Predictable Object.")

    # --- Evaluation Period and Scope ---
    evaluation_period_start: datetime = Field(..., description="Start of the period being evaluated.")
    evaluation_period_end: datetime = Field(..., description="End of the period being evaluated.")
    evaluation_frequency: TimeFrame = Field(..., description="Evaluation frequency, e.g., DAILY, WEEKLY, MONTHLY.")
    predictions_evaluated_count: int = Field(..., description="Number of predictions included in this evaluation.")
    prediction_ids_sample: List[str] = Field(default_factory=list, description="Sample of prediction IDs evaluated (for debugging).")

    # --- Ground Truth Context ---
    ground_truth_source: str = Field(..., description="Source of ground truth data, e.g., 'market_data', 'user_feedback', 'manual_verification'.")
    ground_truth_availability_delay_hours: Optional[float] = Field(None, description="Average delay between prediction and ground truth availability.")
    ground_truth_confidence: Optional[float] = Field(None, description="Confidence level in ground truth data quality (0-1).")

    # --- Performance Metrics (All Prediction Types) ---
    prediction_type: Literal["regression", "classification", "time_series"] = Field(..., description="Type of predictions evaluated.")
    overall_performance_score: float = Field(..., description="Primary performance metric for this evaluation period.")
    performance_vs_baseline_pct: Optional[float] = Field(None, description="Performance improvement/degradation vs baseline model (%).")
    
    # --- Regression Performance Metrics ---
    mae: Optional[float] = Field(None, description="Mean Absolute Error (regression only).")
    mse: Optional[float] = Field(None, description="Mean Squared Error (regression only).")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error (regression only).")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (regression only).")
    r_squared: Optional[float] = Field(None, description="R-squared coefficient of determination (regression only).")

    # --- Classification Performance Metrics ---
    accuracy: Optional[float] = Field(None, description="Classification accuracy (classification only).")
    precision: Optional[float] = Field(None, description="Precision score (classification only).")
    recall: Optional[float] = Field(None, description="Recall score (classification only).")
    f1_score: Optional[float] = Field(None, description="F1 score (classification only).")
    auc_roc: Optional[float] = Field(None, description="Area Under ROC Curve (classification only).")
    confusion_matrix: Optional[Dict[str, Any]] = Field(None, description="Confusion matrix (classification only).")

    # --- Time Series Performance Metrics ---
    forecast_accuracy: Optional[float] = Field(None, description="Overall forecast accuracy (time series only).")
    directional_accuracy: Optional[float] = Field(None, description="Percentage of correctly predicted directions (time series only).")
    seasonal_decomposition_accuracy: Optional[Dict[str, float]] = Field(None, description="Accuracy of trend/seasonal components (time series only).")

    # --- Performance Distribution and Outliers ---
    performance_percentiles: Optional[Dict[str, float]] = Field(None, description="Performance distribution (P10, P25, P50, P75, P90).")
    worst_performing_predictions: Optional[List[str]] = Field(None, description="Prediction IDs with worst performance (for analysis).")
    best_performing_predictions: Optional[List[str]] = Field(None, description="Prediction IDs with best performance (for analysis).")
    outlier_predictions_count: Optional[int] = Field(None, description="Number of predictions identified as outliers.")

    # --- Model Drift Detection ---
    drift_detected: bool = Field(False, description="Whether model drift was detected in this period.")
    drift_score: Optional[float] = Field(None, description="Quantitative drift score (higher = more drift).")
    drift_type: Optional[str] = Field(None, description="Type of drift detected, e.g., 'concept_drift', 'data_drift', 'performance_drift'.")
    feature_drift_scores: Optional[Dict[str, float]] = Field(None, description="Per-feature drift scores.")

    # --- Comparison with Previous Evaluations ---
    previous_evaluation_id: Optional[str] = Field(None, description="Reference to previous evaluation for comparison.")
    performance_trend: Optional[str] = Field(None, description="Performance trend: 'improving', 'stable', 'degrading'.")
    performance_change_pct: Optional[float] = Field(None, description="Performance change vs previous evaluation (%).")

    # --- Business Impact Metrics ---
    business_value_generated: Optional[float] = Field(None, description="Estimated business value generated by accurate predictions (USD).")
    business_cost_of_errors: Optional[float] = Field(None, description="Estimated business cost of prediction errors (USD).")
    prediction_usage_rate: Optional[float] = Field(None, description="Percentage of predictions actually used by downstream systems.")

    # --- Model Performance Context ---
    prediction_environment: str = Field(..., description="Environment where evaluated predictions were made, e.g., 'production', 'staging'.")
    model_load_during_period: Optional[float] = Field(None, description="Average prediction requests per hour during evaluation period.")
    average_prediction_latency_ms: Optional[float] = Field(None, description="Average prediction latency during this period.")
    
    # --- Recommendations and Actions ---
    performance_status: str = Field(..., description="Overall status: 'excellent', 'good', 'acceptable', 'concerning', 'failing'.")
    recommended_actions: Optional[List[str]] = Field(None, description="Recommended actions based on performance, e.g., 'retrain_model', 'investigate_drift'.")
    alert_level: Optional[str] = Field(None, description="Alert level for monitoring systems: 'none', 'warning', 'critical'.")

    # --- Evaluation Metadata ---
    evaluation_method: str = Field(..., description="Method used for evaluation, e.g., 'automated_pipeline', 'manual_analysis'.")
    evaluator: str = Field(..., description="Who/what performed the evaluation, e.g., 'model_monitoring_service', 'data_scientist_name'.")
    evaluation_computed_datetime: datetime = Field(..., description="When this evaluation was computed.")
    evaluation_notes: Optional[str] = Field(None, description="Additional notes about this evaluation.")
    
    # --- Quality Assurance ---
    data_quality_score: Optional[float] = Field(None, description="Quality score of data used in evaluation (0-1).")
    evaluation_confidence: Optional[float] = Field(None, description="Confidence in the evaluation results (0-1).")
    known_evaluation_limitations: Optional[List[str]] = Field(None, description="Known limitations of this evaluation.")

    # --- Metadata ---
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization and filtering.")

    # --- Namespace and Identity ---
    pulse_namespace: Optional[str] = Field(None, description="Namespace for this AI model performance evaluation.")
    namespace_id_seed_phrase: Optional[str] = Field(None, description="Seed phrase used for namespace-based UUID generation.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)
