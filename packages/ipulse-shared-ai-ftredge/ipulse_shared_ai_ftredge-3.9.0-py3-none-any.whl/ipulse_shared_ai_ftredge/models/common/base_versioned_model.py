"""
Base Versioned Model - Shared governance base class for all Pulse specification tables.

This module provides the foundation for all specification tables (AI formats, analysts, 
models, schemas, etc.) with standardized governance, versioning, and audit fields.

See ARCHITECTURE_BaseVersionedModel.md for complete documentation.

AUTHOR: Russlan Ramdowar;russlan@ftredge.com
CREATED: 2025-01-15
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from ipulse_shared_base_ftredge import ObjectOverallStatus


class BaseVersionedModel(BaseModel):
    """
    Base class providing standard governance, versioning, and audit fields.
    
    All specs tables (specs_analyst_personas, specs_ai_input_formats, specs_ai_output_formats,
    ai_model_specifications, ai_model_versions, etc.) inherit these fields.
    
    GOVERNANCE GROUPS:
    1. Identity & Versioning: description, major_version, minor_version, metadata_version
    2. Governance: pulse_status, changelog_registry, lessons_learned, notes, tags
    3. Namespace & Reproducibility: pulse_namespace, namespace_id_seed_phrase
    4. Audit Trail: created_at, created_by, updated_at, updated_by
    
    CRITICAL RULES:
    - namespace_id_seed_phrase is IMMUTABLE once set (used for UUID generation)
    - changelog_registry and lessons_learned use YYYYMMDDHHMMSS timestamp format (UTC)
    - Timestamp keys are sortable strings for consistent ordering
    
    VERSIONING STRATEGY:
    - major_version: Breaking changes (schema structure, required fields, redefinitions)
    - minor_version: Non-breaking changes (new optional fields, expanded enums)
    - metadata_version: Documentation-only changes (descriptions, notes, examples)
    
    BIGQUERY SERIALIZATION:
    - Dict fields (changelog_registry, lessons_learned, tags) stored as JSON strings
    - All datetime fields stored as TIMESTAMP
    - Enums stored as STRING values
    """
    
    # ============================================================================
    # GROUP 1: Identity & Versioning
    # ============================================================================
    
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of object purpose, usage, constraints"
    )
    
    major_version: int = Field(
        default=1,
        ge=1,
        description="Breaking changes: schema structure, required fields, redefinitions"
    )
    
    minor_version: Optional[int] = Field(
        default=0,
        ge=0,
        description="Non-breaking: new optional fields, refinements. Optional field - some tables may only use major_version"
    )
    
    metadata_version: Optional[int] = Field(
        default=0,
        ge=0,
        description="Metadata-only changes (descriptions, notes, examples)"
    )
    
    # ============================================================================
    # GROUP 2: Governance
    # ============================================================================
    
    pulse_status: ObjectOverallStatus = Field(
        default=ObjectOverallStatus.ACTIVE,
        description="ACTIVE (in use), INACTIVE (not in use), DRAFT (being developed), RETIRED (permanently discontinued), DEPRECATED (use alternative)"
    )
    
    changelog_registry: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Change tracking with UTC timestamp keys (YYYYMMDDHHMMSS format). "
            "Values can be strings or structured objects. "
            "Example: {'20250115103000': 'Initial creation', '20250220140000': {'change_type': 'deprecation', 'reason': 'Replaced by v2.0'}}"
        )
    )
    
    lessons_learned: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Lessons learned with UTC timestamp keys (YYYYMMDDHHMMSS format). "
            "Values can be strings or structured objects. "
            "Example: {'20250225164500': 'Narrative templates too verbose - reduced by 30%', '20250305112000': {'issue': 'Missing sector comparison', 'solution': 'Added context_enrichment'}}"
        )
    )
    
    notes: Optional[str] = Field(
        default=None,
        description="Freeform notes for internal use"
    )
    
    tags: Optional[List[str]] = Field(
        default=None,
        description="Categorization tags (e.g., ['equity', 'llm_optimized', 'experimental'])"
    )
    
    # ============================================================================
    # GROUP 3: Namespace & Reproducibility
    # ============================================================================
    
    pulse_namespace: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Logical grouping (e.g., 'ai_namespace::oracle_fincore_prediction')"
    )
    
    namespace_id_seed_phrase: Optional[str] = Field(
        default=None,
        max_length=500,
        description=(
            "Seed for UUID generation (IMMUTABLE once set). "
            "Structure: {namespace}::{domain}::{object_type}::{stable_identity_key}::{creation_timestamp}. "
            "Example: 'ai_namespace::oracle_fincore_prediction::io_format::input_market_standard_assembly::202512261430'"
        )
    )
    
    # ============================================================================
    # GROUP 4: Audit Trail
    # ============================================================================
    
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        frozen=True,
        description="Timestamp when object was created (UTC, immutable)"
    )
    
    created_by: Optional[str] = Field(
        default=None,
        frozen=True,
        description="User ID or system that created the object (immutable)"
    )
    
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last update (UTC, automatically updated)"
    )
    
    updated_by: str = Field(
        default=None,
        description="User ID or system that last updated the object"
    )
