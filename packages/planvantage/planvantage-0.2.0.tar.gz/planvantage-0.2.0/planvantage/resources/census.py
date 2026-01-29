"""Census resource."""

from __future__ import annotations

from typing import Any, BinaryIO, Optional

from planvantage.models.census import (
    ApplyCensusEnrollmentResult,
    CensusData,
    CensusInfo,
    CensusMappingConfig,
    CensusUploadResult,
    MigrationEstimation,
    ScenarioCensusInfo,
)
from planvantage.resources.base import BaseResource


class CensusResource(BaseResource):
    """Resource for managing census data."""

    def get_template(
        self,
        include_subscriber_key: bool = False,
        age_format: Optional[str] = None,
        include_zip_code: bool = False,
        service_format: Optional[str] = None,
        include_gender: bool = False,
        include_salary: bool = False,
        custom_fields: Optional[list[str]] = None,
    ) -> bytes:
        """Download a census template Excel file.

        Args:
            include_subscriber_key: Include subscriber key column.
            age_format: Age format ("age" or "dob").
            include_zip_code: Include zip code column.
            service_format: Service format ("hire_date" or "yos").
            include_gender: Include gender column.
            include_salary: Include salary column.
            custom_fields: List of custom field names to include.

        Returns:
            Excel file bytes.

        Example:
            >>> template = client.census.get_template(include_salary=True)
            >>> with open("template.xlsx", "wb") as f:
            ...     f.write(template)
        """
        params: dict[str, Any] = {}
        if include_subscriber_key:
            params["include_subscriber_key"] = "true"
        if age_format:
            params["age_format"] = age_format
        if include_zip_code:
            params["include_zip_code"] = "true"
        if service_format:
            params["service_format"] = service_format
        if include_gender:
            params["include_gender"] = "true"
        if include_salary:
            params["include_salary"] = "true"
        if custom_fields:
            params["custom_fields"] = ",".join(custom_fields)

        return self._http.get_raw("/census/template", params=params)

    def upload(
        self,
        plan_sponsor_guid: str,
        file: BinaryIO,
        name: Optional[str] = None,
    ) -> CensusUploadResult:
        """Upload census data from a file.

        Args:
            plan_sponsor_guid: The plan sponsor's GUID.
            file: File object containing census data (CSV or Excel).
            name: Optional name for the census.

        Returns:
            Upload result with census GUID and validation info.

        Example:
            >>> with open("census.csv", "rb") as f:
            ...     result = client.census.upload("ps_abc123", f, name="2024 Census")
        """
        files = {"file": file}
        data = {"plan_sponsor_guid": plan_sponsor_guid}
        if name:
            data["name"] = name

        response = self._http.post_multipart("/census", files=files, data=data)
        return CensusUploadResult.model_validate(response)

    def get(self, guid: str) -> CensusData:
        """Get census details.

        Args:
            guid: The census GUID.

        Returns:
            Full census data including mapping configuration.

        Example:
            >>> census = client.census.get("census_abc123")
        """
        data = self._http.get(f"/census/{guid}")
        return CensusData.model_validate(data)

    def update(self, guid: str, name: str) -> CensusData:
        """Update census name.

        Args:
            guid: The census GUID.
            name: New name for the census.

        Returns:
            Updated census data.

        Example:
            >>> census = client.census.update("census_abc123", name="Q1 Census")
        """
        data = self._http.patch(f"/census/{guid}", json={"name": name})
        return CensusData.model_validate(data)

    def delete(self, guid: str) -> None:
        """Delete a census.

        Args:
            guid: The census GUID.

        Example:
            >>> client.census.delete("census_abc123")
        """
        self._http.delete(f"/census/{guid}")

    def download(self, guid: str) -> bytes:
        """Download the original census file.

        Args:
            guid: The census GUID.

        Returns:
            Original uploaded file bytes.

        Example:
            >>> data = client.census.download("census_abc123")
            >>> with open("census_download.xlsx", "wb") as f:
            ...     f.write(data)
        """
        return self._http.get_raw(f"/census/{guid}/download")

    def replace(self, guid: str, file: BinaryIO) -> CensusUploadResult:
        """Replace census data with a new file.

        Args:
            guid: The census GUID.
            file: New file to replace existing data.

        Returns:
            Upload result with validation info.

        Example:
            >>> with open("new_census.csv", "rb") as f:
            ...     result = client.census.replace("census_abc123", f)
        """
        files = {"file": file}
        response = self._http.post_multipart(f"/census/{guid}/replace", files=files)
        return CensusUploadResult.model_validate(response)

    def get_mapping(self, guid: str) -> CensusMappingConfig:
        """Get census mapping configuration.

        Args:
            guid: The census GUID.

        Returns:
            Mapping configuration.

        Example:
            >>> mapping = client.census.get_mapping("census_abc123")
        """
        data = self._http.get(f"/census/{guid}/mapping")
        return CensusMappingConfig.model_validate(data)

    def update_mapping(
        self,
        guid: str,
        mapping: CensusMappingConfig,
    ) -> CensusMappingConfig:
        """Update census mapping configuration.

        Args:
            guid: The census GUID.
            mapping: New mapping configuration.

        Returns:
            Updated mapping configuration.

        Example:
            >>> mapping = client.census.get_mapping("census_abc123")
            >>> mapping.plan_mappings[0].rate_plan_guid = "rp_new"
            >>> client.census.update_mapping("census_abc123", mapping)
        """
        data = self._http.patch(
            f"/census/{guid}/mapping",
            json=self._serialize(mapping),
        )
        return CensusMappingConfig.model_validate(data)

    def reprocess(self, guid: str) -> None:
        """Reprocess census data.

        Args:
            guid: The census GUID.

        Example:
            >>> client.census.reprocess("census_abc123")
        """
        self._http.post(f"/census/{guid}/reprocess")

    def recalculate_mapping(self, guid: str) -> CensusMappingConfig:
        """Recalculate census mapping using AI.

        Args:
            guid: The census GUID.

        Returns:
            New AI-generated mapping configuration.

        Example:
            >>> mapping = client.census.recalculate_mapping("census_abc123")
        """
        data = self._http.post(f"/census/{guid}/mapping/recalculate")
        return CensusMappingConfig.model_validate(data)

    def list_for_plan_sponsor(self, plan_sponsor_guid: str) -> list[CensusInfo]:
        """List all censuses for a plan sponsor.

        Args:
            plan_sponsor_guid: The plan sponsor's GUID.

        Returns:
            List of census summaries.

        Example:
            >>> censuses = client.census.list_for_plan_sponsor("ps_abc123")
        """
        data = self._http.get(f"/plansponsor/{plan_sponsor_guid}/censuses")
        if isinstance(data, list):
            return [CensusInfo.model_validate(item) for item in data]
        return []


class ScenarioCensusResource(BaseResource):
    """Resource for managing census data linked to scenarios."""

    def get(self, scenario_guid: str) -> ScenarioCensusInfo:
        """Get census mapping for a scenario.

        Args:
            scenario_guid: The scenario's GUID.

        Returns:
            Scenario census information.

        Example:
            >>> info = client.scenario_census.get("sc_abc123")
        """
        data = self._http.get(f"/scenario/{scenario_guid}/census")
        return ScenarioCensusInfo.model_validate(data)

    def map(
        self,
        scenario_guid: str,
        census_guid: str,
    ) -> ScenarioCensusInfo:
        """Map a census to a scenario.

        Args:
            scenario_guid: The scenario's GUID.
            census_guid: The census GUID to map.

        Returns:
            Scenario census information with mapping.

        Example:
            >>> info = client.scenario_census.map("sc_abc123", "census_xyz")
        """
        data = self._http.post(
            f"/scenario/{scenario_guid}/census/map",
            json={"census_guid": census_guid},
        )
        return ScenarioCensusInfo.model_validate(data)

    def unmap(self, scenario_guid: str) -> None:
        """Unmap census from a scenario.

        Args:
            scenario_guid: The scenario's GUID.

        Example:
            >>> client.scenario_census.unmap("sc_abc123")
        """
        self._http.post(f"/scenario/{scenario_guid}/census/unmap")

    def apply(
        self,
        scenario_guid: str,
        apply_to: str = "current",
        migration_instructions: Optional[str] = None,
        allow_participation_change: bool = False,
        proposed_enrollment: Optional[dict[str, dict[str, int]]] = None,
    ) -> dict[str, Any]:
        """Apply census enrollment data to scenario.

        Args:
            scenario_guid: The scenario's GUID.
            apply_to: Where to apply ("current", "proposed", "both", "both_with_migration").
            migration_instructions: Instructions for AI migration estimation.
            allow_participation_change: Allow total enrollment to change during migration.
            proposed_enrollment: Pre-calculated proposed enrollment from preview.

        Returns:
            Result with enrollment changes.

        Example:
            >>> result = client.scenario_census.apply("sc_abc123", apply_to="both")
        """
        body: dict[str, Any] = {"apply_to": apply_to}
        if migration_instructions:
            body["migration_instructions"] = migration_instructions
        if allow_participation_change:
            body["allow_participation_change"] = True
        if proposed_enrollment:
            body["proposed_enrollment"] = proposed_enrollment

        return self._http.post(f"/scenario/{scenario_guid}/census/apply", json=body)

    def preview_migration(
        self,
        scenario_guid: str,
        migration_instructions: Optional[str] = None,
    ) -> MigrationEstimation:
        """Preview migration estimation from current to proposed plans.

        Uses AI to estimate how employees would migrate based on plan changes.

        Args:
            scenario_guid: The scenario's GUID.
            migration_instructions: Optional instructions to guide the AI estimation.

        Returns:
            Migration estimation with proposed enrollment counts.

        Example:
            >>> preview = client.scenario_census.preview_migration(
            ...     "sc_abc123",
            ...     migration_instructions="Assume 20% move to lower cost plans"
            ... )
        """
        body = {}
        if migration_instructions:
            body["migration_instructions"] = migration_instructions

        data = self._http.post(
            f"/scenario/{scenario_guid}/census/preview-migration",
            json=body if body else None,
        )
        return MigrationEstimation.model_validate(data)

    def update_mapping(
        self,
        scenario_guid: str,
        plan_mappings: Optional[list[dict[str, Any]]] = None,
        tier_mappings: Optional[list[dict[str, Any]]] = None,
        opt_out_mappings: Optional[list[dict[str, Any]]] = None,
    ) -> ScenarioCensusInfo:
        """Update scenario-specific census mapping.

        Args:
            scenario_guid: The scenario's GUID.
            plan_mappings: Updated plan mappings.
            tier_mappings: Updated tier mappings.
            opt_out_mappings: Updated opt-out mappings.

        Returns:
            Updated scenario census information.

        Example:
            >>> info = client.scenario_census.update_mapping(
            ...     "sc_abc123",
            ...     plan_mappings=[{"census_values": ["PPO"], "rate_plan_guid": "rp_new"}]
            ... )
        """
        body: dict[str, Any] = {}
        if plan_mappings:
            body["plan_mappings"] = plan_mappings
        if tier_mappings:
            body["tier_mappings"] = tier_mappings
        if opt_out_mappings:
            body["opt_out_mappings"] = opt_out_mappings

        data = self._http.patch(
            f"/scenario/{scenario_guid}/census/mapping",
            json=body,
        )
        return ScenarioCensusInfo.model_validate(data)
