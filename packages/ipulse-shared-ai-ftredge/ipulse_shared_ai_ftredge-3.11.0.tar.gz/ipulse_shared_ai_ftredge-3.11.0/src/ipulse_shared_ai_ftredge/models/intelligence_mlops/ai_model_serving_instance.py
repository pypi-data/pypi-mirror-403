# pylint: disable=missing-module-docstring, missing-class-docstring, line-too-long, invalid-name
from typing import Optional, Dict, Any, ClassVar
from pydantic import Field
from datetime import datetime, timezone
from ipulse_shared_base_ftredge import ObjectOverallStatus, ComputeResourceStatus
from ..common import BaseVersionedModel


class AIModelServingInstance(BaseVersionedModel):
    """
    🚀 AI MODEL SERVING INSTANCE - The Active Prediction Service

    CORE CONCEPT:
    Represents a specific, actively running serving instance of an AI model version that 
    provides prediction services. This is the actual callable endpoint or execution environment,
    not just the model artifact. ONE model version can spawn MULTIPLE serving instances with
    different hosting patterns, geographic distributions, and operational configurations.

    KEY RELATIONSHIPS:
    • ONE model version (AIModelVersion) → MULTIPLE serving instances
    • ONE serving instance → MANY predictions (served from this specific instance)
    • ONE model specification → MULTIPLE serving instances (via versions)
    • Each instance tracks its serving lineage through denormalized IDs for query efficiency

    SERVING PATTERNS & LIFECYCLE:
    • Persistent: Always-on services (24/7 web APIs, real-time endpoints)
      - Lifecycle: PROVISIONING → HEALTHY → SERVING → RETIRING → TERMINATED
    • Ephemeral: On-demand execution (batch jobs, scheduled tasks, one-time analysis)
      - Lifecycle: PROVISIONING → SERVING → COMPLETED → TERMINATED
    • Hybrid: Auto-scaling services (scale-to-zero when idle, burst for demand)
      - Lifecycle: PROVISIONING → SCALING → SERVING → IDLE → TERMINATED

    DEPLOYMENT SCENARIOS:
    • Multi-Region: Same version deployed in us-east-1, europe-west1, asia-southeast1
    • Multi-Environment: Same version in staging, production, development, canary
    • A/B Testing: Same version with different endpoint configurations or traffic splits
    • Batch Processing: Ephemeral instances that spin up → process → shut down
    • Local Development: Developer workstation instances for testing and debugging

    HOSTING ARCHITECTURE:
    • Internal Hosting: Self-managed infrastructure
      - Providers: GCP (Cloud Run), AWS (Lambda), Azure (Container Instances), Local (Python/Docker)
      - Resource Control: CPU/GPU specs, memory, scaling policies, networking
      - Cost Management: Direct infrastructure costs, optimization opportunities
    
    • External Hosting: Third-party API services  
      - Providers: OpenAI (GPT), Google AI (Gemini), Anthropic (Claude)
      - Service Integration: API keys, rate limits, authentication flows
      - Cost Tracking: Per-request pricing, usage optimization, fallback strategies

    OPERATIONAL MONITORING:
    • Health Checks: Automated endpoint monitoring and alerting
    • Performance Metrics: Latency, throughput, error rates, resource utilization
    • Traffic Management: Load balancing, circuit breakers, traffic splitting for A/B tests
    • Scaling Policies: Auto-scaling triggers, resource limits, cost controls

    SCHEDULED & TRIGGERED EXECUTION:
    • Cron-based: schedule_expression for regular batch processing
    • Event-driven: execution_trigger for API requests, file uploads, data changes
    • Time-bounded: max_execution_duration_minutes for resource protection
    • Auto-cleanup: auto_shutdown_after_completion for cost optimization

    DENORMALIZED TRACKING:
    Instance includes denormalized references (model_spec_id, training_config_id, training_run_id)
    for query efficiency, enabling fast lookups without complex joins while maintaining
    referential integrity to the source model version.
    """

    VERSION: ClassVar[int] = 5
    SCHEMA_ID: ClassVar[str] = "schema_24a66dfd-3c1b-5434-92cc-9dd1ea6cbc23"
    SCHEMA_NAME: ClassVar[str] = "dp_oracle_fincore_prediction__controls.ai_model_serving_instances"
    DOMAIN: ClassVar[str] = "papp_oracle_fincore_prediction"
    OBJ_REF: ClassVar[str] = "aimodelinstance"

    # --- Core Identity ---
    model_serving_instance_id: str = Field(..., description="Unique identifier for this serving instance.")
    model_serving_instance_name: str = Field(..., max_length=200, description="Machine-readable identifier for programmatic use (e.g., 'gemini_2_5_pro_genai_client', 'gpt_4_production_us_east')")
    serving_instance_display_name: str = Field(..., max_length=200, description="Human-readable instance name for UI display, e.g., 'Prod US East Primary', 'Daily Batch Runner'")
    # Version fields inherited from BaseVersionedModel: major_version, minor_version, metadata_version
    model_version_id: str = Field(..., description="Reference to the AIModelVersion being served.")
    model_spec_id: Optional[str] = Field(default=None, description="Reference to the AIModelSpecification (denormalized from model version for query efficiency).")
    training_config_id: Optional[str] = Field(default=None, description="Reference to the training configuration (denormalized from model version for query efficiency).")
    training_run_id: Optional[str] = Field(default=None, description="Reference to the training run (denormalized from model version for query efficiency).")

    # --- Hosting Pattern ---
    hosting_environment: str = Field(..., description="Environment type, e.g., 'production', 'staging', 'development', 'local', 'batch'.")
    hosting_type: str = Field(..., description="Type of hosting: 'internal' (self-hosted infrastructure) or 'external' (third-party API service).")
    hosting_pattern: str = Field(..., description="Hosting pattern: 'persistent' (24/7), 'ephemeral' (on-demand), 'hybrid' (auto-scaling).")
    hosting_provider: str = Field(..., description="Hosting provider, e.g., 'gcp', 'aws', 'azure', 'local' (for internal) or 'openai', 'anthropic', 'google' (for external).")
    hosting_service: Optional[str] = Field(default=None, description="Specific service, e.g., 'cloud_run', 'lambda', 'local_python', 'batch_job' (internal) or 'api', 'vertex_ai' (external).")
    hosting_region: str = Field(..., description="Geographic region, e.g., 'us-east-1', 'europe-west1', 'local', or 'global' for external providers.")
    hosting_zone: Optional[str] = Field(default=None, description="Availability zone if applicable, e.g., 'us-east-1a' (internal hosting only).")

    # --- Compute Resources (Internal Hosting Only) ---
    compute_specification: Optional[Dict[str, Any]] = Field(default=None, description="Compute resources for internal hosting, e.g., {'cpu': '2 cores', 'memory': '8GB', 'gpu': 'T4', 'instances': 3}.")
    auto_scaling_config: Optional[Dict[str, Any]] = Field(default=None, description="Auto-scaling configuration for internal hosting, e.g., {'min_instances': 1, 'max_instances': 10, 'target_cpu': 70}.")

    # --- Network & Access (Universal) ---
    endpoint_url: str = Field(..., description="Primary endpoint URL - either internal deployment URL or external API endpoint.")
    endpoint_authentication: Optional[str] = Field(default=None, description="Auth method, e.g., 'api_key', 'oauth', 'service_account', 'iam', 'none'.")
    endpoint_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Endpoint settings, e.g., {'timeout_seconds': 30, 'max_concurrent_requests': 100, 'rate_limit': '1000/min'}.")
    api_key_reference: Optional[str] = Field(default=None, description="Reference to stored API key (not actual key) - for both internal auth and external APIs.")

    # --- Hosting Lifecycle ---
    hosting_compute_resource_status: ComputeResourceStatus = Field(..., description="Infrastructure status of the hosting compute resources (RUNNING, STOPPED, PROVISIONING, ERROR, etc.).")
    # Note: pulse_status, changelog_registry, and lessons_learned are inherited from BaseVersionedModel
    hosting_strategy: Optional[str] = Field(default=None, description="Hosting strategy, e.g., 'blue_green', 'canary', 'rolling', 'direct'.")
    
    # --- Ephemeral/Scheduled Configuration ---
    execution_trigger: Optional[str] = Field(default=None, description="How instance is triggered: 'always_on', 'manual', 'scheduled', 'api_request', 'batch_job'.")
    schedule_expression: Optional[str] = Field(default=None, description="Cron expression for scheduled instances, e.g., '0 9 * * 1' (every Monday at 9 AM).")
    max_execution_duration_minutes: Optional[int] = Field(default=None, description="Maximum allowed execution time in minutes before auto-termination.")
    auto_shutdown_after_completion: bool = Field(default=True, description="Whether to automatically shut down after completing execution (ephemeral pattern).")
    
    # --- Timestamps ---
    hosting_started_datetime: datetime = Field(..., description="When hosting process started.")
    hosting_completed_datetime: Optional[datetime] = Field(default=None, description="When hosting became ready for serving.")
    last_health_check_datetime: Optional[datetime] = Field(default=None, description="Last successful health check.")
    last_execution_datetime: Optional[datetime] = Field(default=None, description="Last time this instance executed/served predictions.")
    next_scheduled_execution_datetime: Optional[datetime] = Field(default=None, description="Next scheduled execution time (for scheduled instances).")
    hosting_terminated_datetime: Optional[datetime] = Field(default=None, description="When hosting was terminated.")

    # --- Performance & Monitoring ---
    health_check_endpoint: Optional[str] = Field(default=None, description="Health check URL for monitoring.")
    monitoring_configuration: Optional[Dict[str, Any]] = Field(default=None, description="Monitoring setup, e.g., {'metrics_enabled': True, 'logging_level': 'INFO', 'alerts': ['high_latency', 'error_rate']}.")
    traffic_percentage: Optional[float] = Field(default=None, description="Percentage of traffic routed to this hosting instance (for A/B testing).")

    # --- Operational Metadata ---
    hosting_notes: Optional[str] = Field(default=None, description="Hosting-specific notes and configuration details.")
    approved_by: Optional[str] = Field(default=None, description="Who approved this hosting instance for production.")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags for categorization and management.")

    # --- Namespace and Identity ---
    pulse_namespace: Optional[str] = Field(default=None, description="Namespace for this AI model serving instance.")
    namespace_id_seed_phrase: Optional[str] = Field(default=None, description="Seed phrase used for namespace-based UUID generation.")

    # Audit fields - created fields are frozen after creation, updated fields are mutable
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), frozen=True)
    created_by: Optional[str] = Field(..., frozen=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: str = Field(...)

    class Config:
        extra = "forbid"
