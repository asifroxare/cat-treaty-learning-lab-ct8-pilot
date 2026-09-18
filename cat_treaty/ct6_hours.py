"""CT6 bounded hours-clause orchestration through CT4 and CT5."""

from dataclasses import dataclass

from cat_treaty.ct4_metadata import build_ct4_run_identity
from cat_treaty.ct4_models import (
    CT4AnnualTrialInput,
    CT4FrequencyAnalytics,
    CT4RunIdentity,
    CT4SimulationInput,
    CT4TailAnalytics,
    HoursClauseResult,
    HoursClauseScenario,
    HoursElectionStatus,
    OccurrenceDefinitionMode,
)
from cat_treaty.ct5_analytics import calculate_ct5_analytics
from cat_treaty.ct5_analytics_models import CT5Analytics
from cat_treaty.ct5_metadata import CT5RunIdentity, build_ct5_run_identity
from cat_treaty.ct5_models import CT5CatalogueResult
from cat_treaty.ct5_simulation import apply_ct5_catalogue
from cat_treaty.ct6_adapters import AdaptedHoursRequest, adapt_hours_request
from cat_treaty.ct6_models import HoursRunRequest
from cat_treaty.ct6_orchestration import _build_program_input
from cat_treaty.frequency import calculate_frequency_analytics_from_rows
from cat_treaty.occurrence_definition import evaluate_hours_clause_scenario
from cat_treaty.tail import calculate_tail_analytics_from_rows


class CT6HoursContractBlockedError(ValueError):
    """A valid request whose contractual election cannot complete."""

    def __init__(self, result: HoursClauseResult) -> None:
        if result.election_status is not HoursElectionStatus.BLOCKED:
            raise ValueError("blocked error requires a blocked HoursClauseResult")
        self.result = result
        codes = ", ".join(item.code.value for item in result.election_issues)
        super().__init__(f"hours-clause contract blocked: {codes}")


@dataclass(frozen=True, slots=True)
class CT6HoursRunResult:
    request: HoursRunRequest
    ct4_result: HoursClauseResult
    ct4_tail_analytics: CT4TailAnalytics
    ct4_frequency_analytics: CT4FrequencyAnalytics
    ct4_identity: CT4RunIdentity
    ct5_result: CT5CatalogueResult
    ct5_analytics: CT5Analytics
    ct5_identity: CT5RunIdentity


def run_hours_clause(request: HoursRunRequest) -> CT6HoursRunResult:
    """Validate source, elect valid occurrences, then apply CT5 statefully."""

    if not isinstance(request, HoursRunRequest):
        raise TypeError("request must be HoursRunRequest")
    adapted = adapt_hours_request(request)
    simulation_input, scenario = _build_hours_simulation(adapted)
    ct4_result = evaluate_hours_clause_scenario(
        scenario,
        source_version=request.input.source_version,
    )
    if ct4_result.election_status is HoursElectionStatus.BLOCKED:
        raise CT6HoursContractBlockedError(ct4_result)
    assert ct4_result.annual_row is not None
    annual_rows = (ct4_result.annual_row,)
    ct4_tail = calculate_tail_analytics_from_rows(
        annual_rows,
        config=adapted.tail_configuration,
        relative_tolerance=adapted.tolerance_profile.relative_tolerance,
        absolute_tolerance=adapted.tolerance_profile.absolute_currency_tolerance,
    )
    ct4_frequency = calculate_frequency_analytics_from_rows(annual_rows)
    ct4_identity = build_ct4_run_identity(
        simulation_input=simulation_input,
        result=ct4_result,
        analytics=ct4_tail,
    )
    ct5_result = apply_ct5_catalogue(
        ct4_result=ct4_result,
        treaty_terms=adapted.treaty_terms,
        program_layers=adapted.layers,
        ct4_simulation_input=simulation_input,
    )
    ct5_analytics = calculate_ct5_analytics(ct5_result)
    ct5_identity = build_ct5_run_identity(
        result=ct5_result,
        analytics=ct5_analytics,
        ct4_analytics=ct4_tail,
        ct4_identity=ct4_identity,
    )
    return CT6HoursRunResult(
        request=request,
        ct4_result=ct4_result,
        ct4_tail_analytics=ct4_tail,
        ct4_frequency_analytics=ct4_frequency,
        ct4_identity=ct4_identity,
        ct5_result=ct5_result,
        ct5_analytics=ct5_analytics,
        ct5_identity=ct5_identity,
    )


def _build_hours_simulation(
    adapted: AdaptedHoursRequest,
) -> tuple[CT4SimulationInput, HoursClauseScenario]:
    wire = adapted.request.input
    program_source = _build_program_input(
        adapted.program_source,
        adapted=adapted,
        source_version=wire.source_version,
    )
    scenario = HoursClauseScenario(
        scenario_id=wire.scenario_id,
        components=adapted.components,
        terms=adapted.terms,
        program_terms_source=program_source,
        source_reference=wire.source_reference,
    )
    simulation = CT4SimulationInput(
        simulation_id=wire.scenario_id,
        trial_count=1,
        trials=(CT4AnnualTrialInput(1, wire.source_reference, ()),),
        catalogue_version="hours-clause-teaching",
        source_version=wire.source_version,
        simulation_seed=None,
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        tail_configuration=adapted.tail_configuration,
        tolerance_profile=adapted.tolerance_profile,
        hours_clause_scenario=scenario,
        description="CT6 hours-clause teaching scenario",
        source_reference=wire.source_reference,
        rule_reference="CT6-v1.0-hours",
    )
    return simulation, scenario

