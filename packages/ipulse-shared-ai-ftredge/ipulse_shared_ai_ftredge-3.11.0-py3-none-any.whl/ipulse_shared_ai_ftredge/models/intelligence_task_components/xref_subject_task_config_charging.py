from typing import Optional, List, Union
from pydantic import Field, field_validator
from ipulse_shared_ai_ftredge.models.common.base_versioned_model import BaseVersionedModel
from ipulse_shared_base_ftredge.enums.enums_analysts import AssignmentReason
from ipulse_shared_base_ftredge.enums.enums_units import TimeFrame

class XrefSubjectTaskConfigCharging(BaseVersionedModel):
    """
    Maps subjects to task configurations with optional subject-specific charge overrides and access control.
    Multiplies task configs by subjects.
    
    Enables:
    - Generalized analysts (1 config to many subjects)
    - Specialized analysts (1 config to 1 subject)
    - Per-subject pricing
    
    Matches BigQuery table: dp_oracle_fincore_prediction__controls.xref_subject_task_config_charging
    """
    xref_id: str = Field(..., description="Unique identifier for the xref. Primary Key.")
    
    # Subject Identification
    subject_id: str = Field(..., description="Foreign Key to dim_fincore_market_assets (e.g., AAPL asset_id)")
    subject_name: str = Field(..., description="Denormalized subject name (e.g., 'Apple Inc.')")
    subject_dim_schema_id: str = Field(..., description="Foreign Key to schema_registry for subject dimension schema")
    subject_sector_records_category: str = Field(..., description="market, sector_specific, sector_agnostic")
    subject_category: str = Field(..., description="equity, etf, index, crypto")
    subject_tier: str = Field(..., description="tier_1, tier_2, tier_3 for tier-based deployment")
    
    # Task Configuration Reference
    task_config_id: str = Field(..., description="Foreign Key to ai_task_configs")
    task_config_name: str = Field(..., description="Denormalized config name for readability")
    
    # Charging & Access Control (Subject-Specific)
    charge_specification_id: Optional[str] = Field(default=None, description="Foreign Key to specs_charges (override base if needed)")
    charge_specification_name: Optional[str] = Field(default=None, description="Human-readable charge spec name")
    charge_credit_cost: int = Field(..., description="FINAL credit cost (may override task_config base)")
    charge_notes: Optional[str] = Field(default=None, description="Cost breakdown, special pricing notes")
    
    allowed_reader_ids: Optional[Union[List[str], str]] = Field(
        default=None, 
        description="List of user/service account IDs. Stored as comma-separated in BigQuery."
    )
    allowed_reader_roles: Optional[Union[List[str], str]] = Field(
        default=None, 
        description="List of role names. Stored as comma-separated in BigQuery."
    )
    extra_filters_or_specifications: Optional[str] = Field(
        default=None, 
        description="Additional filters (JSON or comma-separated)"
    )
    
    # Execution Configuration
    execution_frequency: TimeFrame = Field(..., description="How often to execute for this subject (1d, 1w, 1M, on_demand)")
    
    # Assignment Management
    assignment_reason: AssignmentReason = Field(..., description="manual_curation, auto_recommend, pilot_test, performance_upgrade, tier_rollout. Matches AssignmentReason enum.")
    assignment_notes: Optional[str] = Field(default=None, description="Free-text assignment context")
    
    # Versioned Model Required Fields
    description: str = Field(..., description="XREF purpose (brief description of this subject-task config pairing)")
    
    @field_validator('allowed_reader_ids', 'allowed_reader_roles', mode='before')
    @classmethod
    def parse_comma_separated(cls, v):
        """Convert comma-separated strings from BigQuery to lists."""
        if v is None:
            return None
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('allowed_reader_ids', 'allowed_reader_roles', mode='after')
    @classmethod
    def serialize_to_string(cls, v):
        """Convert lists back to comma-separated strings for BigQuery storage."""
        if v is None:
            return None
        if isinstance(v, list):
            return ','.join(v)
        return v
