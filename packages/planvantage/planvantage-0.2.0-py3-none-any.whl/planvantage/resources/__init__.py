"""Resource classes for PlanVantage API."""

from planvantage.resources.base import BaseResource
from planvantage.resources.plansponsors import PlanSponsorsResource
from planvantage.resources.scenarios import ScenariosResource
from planvantage.resources.plandesigns import PlanDesignsResource
from planvantage.resources.rateplans import (
    CurrentRatePlansResource,
    ProposedRatePlansResource,
    CurrentRatePlanTiersResource,
    ProposedRatePlanTiersResource,
    CurrentRatePlanAdjustmentsResource,
    ProposedRatePlanAdjustmentsResource,
)
from planvantage.resources.contributions import (
    CurrentContributionGroupsResource,
    CurrentContributionTiersResource,
    ProposedContributionOptionsResource,
    ProposedContributionGroupsResource,
    ProposedContributionTiersResource,
)
from planvantage.resources.plandocuments import PlanDocumentsResource
from planvantage.resources.benchmarks import BenchmarksResource
from planvantage.resources.settings import (
    PlanModelSettingsResource,
    RateModelSettingsResource,
    RateModelAssumptionsResource,
    RatePlanTierNamesResource,
)
from planvantage.resources.census import CensusResource, ScenarioCensusResource
from planvantage.resources.export import ExportResource

# NOTE: The following resources are intentionally excluded:
# - AIModelsResource (aimodels.py) - internal use only
# - ApiKeysResource (apikeys.py) - managed via web UI only

__all__ = [
    "BaseResource",
    "PlanSponsorsResource",
    "ScenariosResource",
    "PlanDesignsResource",
    "CurrentRatePlansResource",
    "ProposedRatePlansResource",
    "CurrentRatePlanTiersResource",
    "ProposedRatePlanTiersResource",
    "CurrentRatePlanAdjustmentsResource",
    "ProposedRatePlanAdjustmentsResource",
    "CurrentContributionGroupsResource",
    "CurrentContributionTiersResource",
    "ProposedContributionOptionsResource",
    "ProposedContributionGroupsResource",
    "ProposedContributionTiersResource",
    "PlanDocumentsResource",
    "BenchmarksResource",
    "PlanModelSettingsResource",
    "RateModelSettingsResource",
    "RateModelAssumptionsResource",
    "RatePlanTierNamesResource",
    "CensusResource",
    "ScenarioCensusResource",
    "ExportResource",
]
