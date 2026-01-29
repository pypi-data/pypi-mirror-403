"""Census models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CensusSchemaConfig(BaseModel):
    """Census field schema configuration."""

    has_subscriber_key: bool = False
    age_format: Optional[str] = None
    service_format: Optional[str] = None
    has_zip_code: bool = False
    has_gender: bool = False
    has_salary: bool = False
    custom_field_names: list[str] = Field(default_factory=list)


class CensusPlanMapping(BaseModel):
    """Mapping from census plan values to rate plans."""

    census_column: str
    census_values: list[str]
    rate_plan_guid: str
    rate_plan_name: str
    confidence: float = 0.0
    matched_count: int = 0


class CensusTierMapping(BaseModel):
    """Mapping from census tier values to standard tiers."""

    census_column: str
    census_values: list[str]
    rate_plan_tier_name_id: int
    tier_name: str
    confidence: float = 0.0
    matched_count: int = 0


class CensusOptOutMapping(BaseModel):
    """Mapping for opt-out/waived coverage values."""

    census_column: str
    census_values: list[str]
    reason: str
    matched_count: int = 0


class CensusMappingValidation(BaseModel):
    """Validation results for census mappings."""

    unmapped_plan_values: list[str] = Field(default_factory=list)
    unmapped_tier_values: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class CensusMappingConfig(BaseModel):
    """Full census mapping configuration."""

    version: str = ""
    generated_at: Optional[datetime] = None
    census_info: dict[str, Any] = Field(default_factory=dict)
    schema_config: Optional[CensusSchemaConfig] = Field(default=None, alias="schema")
    plan_mappings: list[CensusPlanMapping] = Field(default_factory=list)
    tier_mappings: list[CensusTierMapping] = Field(default_factory=list)
    opt_out_mappings: list[CensusOptOutMapping] = Field(default_factory=list)
    unique_plan_values: list[str] = Field(default_factory=list)
    unique_tier_values: list[str] = Field(default_factory=list)
    plan_value_counts: dict[str, int] = Field(default_factory=dict)
    tier_value_counts: dict[str, int] = Field(default_factory=dict)
    validation: Optional[CensusMappingValidation] = None

    class Config:
        populate_by_name = True


class CensusInfo(BaseModel):
    """Census summary information."""

    guid: str
    name: str
    file_name: str
    file_size: int
    row_count: int
    processing_status: str
    processing_error: Optional[str] = None
    schema_config: Optional[CensusSchemaConfig] = None
    created_at: datetime


class CensusData(BaseModel):
    """Full census data."""

    guid: str
    name: str
    file_name: str
    file_type: str
    file_size: int
    row_count: int
    processing_status: str
    processing_error: Optional[str] = None
    schema_config: Optional[CensusSchemaConfig] = None
    mapping_config: Optional[CensusMappingConfig] = None
    created_at: datetime
    updated_at: datetime


class CensusUploadResult(BaseModel):
    """Result of census upload operation."""

    success: bool
    census_guid: str
    row_count: int
    plans_found: list[str] = Field(default_factory=list)
    tiers_found: list[str] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScenarioCensusInfo(BaseModel):
    """Census mapping information for a scenario."""

    census_guid: str
    census_name: str
    row_count: int
    mapping_config: Optional[CensusMappingConfig] = None
    enrollment_status: str
    expected_enrollment: Optional[dict[str, dict[str, int]]] = None
    current_enrollment: Optional[dict[str, dict[str, int]]] = None


class MigrationChange(BaseModel):
    """A single migration between plans."""

    from_plan: str
    to_plan: str
    count: int
    percentage: float
    reason: str


class MigrationEstimation(BaseModel):
    """Estimated enrollment migration from current to proposed plans."""

    proposed_enrollment: dict[str, dict[str, int]]
    migration_summary: list[MigrationChange] = Field(default_factory=list)
    total_enrollment_delta: int = 0
    confidence: float = 0.0
    rationale: str = ""


class ApplyCensusEnrollmentResult(BaseModel):
    """Result of applying census enrollment."""

    success: bool
    total_records: int = 0
    previous_enrollment: int = 0
    new_enrollment: int = 0
    enrollment_by_plan: dict[str, int] = Field(default_factory=dict)
    enrollment_by_tier: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class CensusTemplateConfig(BaseModel):
    """Configuration for census template download."""

    include_subscriber_key: bool = False
    age_format: Optional[str] = None
    include_zip_code: bool = False
    service_format: Optional[str] = None
    include_gender: bool = False
    include_salary: bool = False
    custom_fields: list[str] = Field(default_factory=list)
