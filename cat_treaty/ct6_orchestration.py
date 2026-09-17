"""CT6 catalogue orchestration through the frozen CT2--CT5 engines."""

from dataclasses import dataclass

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import InuringWaterfallInput
from cat_treaty.ct3_models import CT3ProgramInput
from cat_treaty.ct4_metadata import build_ct4_run_identity
from cat_treaty.ct4_models import (
    CT4AnnualTrialInput,
    CT4CatalogueResult,
    CT4FrequencyAnalytics,
    CT4OccurrenceInput,
    CT4RunIdentity,
    CT4SimulationInput,
    CT4TailAnalytics,
    OccurrenceDefinitionMode,
)
from cat_treaty.ct5_analytics import calculate_ct5_analytics
from cat_treaty.ct5_analytics_models import CT5Analytics
from cat_treaty.ct5_metadata import CT5RunIdentity, build_ct5_run_identity
from cat_treaty.ct5_models import CT5CatalogueResult
from cat_treaty.ct5_simulation import apply_ct5_catalogue
from cat_treaty.ct6_adapters import AdaptedCatalogueRequest, AdaptedSourceOccurrence, adapt_catalogue_request
from cat_treaty.ct6_models import CatalogueRunRequest
from cat_treaty.frequency import calculate_frequency_analytics
from cat_treaty.inuring import apply_inuring_waterfall
from cat_treaty.loss_basis import build_loss_basis
from cat_treaty.simulation import apply_catalogue_simulation
from cat_treaty.tail import calculate_tail_analytics


@dataclass(frozen=True, slots=True)
class CT6CatalogueRunResult:
    request: CatalogueRunRequest
    ct4_result: CT4CatalogueResult
    ct4_tail_analytics: CT4TailAnalytics
    ct4_frequency_analytics: CT4FrequencyAnalytics
    ct4_identity: CT4RunIdentity
    ct5_result: CT5CatalogueResult
    ct5_analytics: CT5Analytics
    ct5_identity: CT5RunIdentity


def run_catalogue(request: CatalogueRunRequest) -> CT6CatalogueRunResult:
    """Execute one complete catalogue request in the frozen dependency order."""

    if not isinstance(request, CatalogueRunRequest):
        raise TypeError("request must be CatalogueRunRequest")
    adapted = adapt_catalogue_request(request)
    simulation_input = _build_simulation_input(adapted)
    ct4_result = apply_catalogue_simulation(simulation_input)
    ct4_tail = calculate_tail_analytics(ct4_result)
    ct4_frequency = calculate_frequency_analytics(ct4_result)
    ct4_identity = build_ct4_run_identity(
        simulation_input=simulation_input,
        result=ct4_result,
        analytics=ct4_tail,
    )
    ct5_result = apply_ct5_catalogue(
        ct4_result=ct4_result,
        treaty_terms=adapted.treaty_terms,
        program_layers=adapted.layers,
    )
    ct5_analytics = calculate_ct5_analytics(ct5_result)
    ct5_identity = build_ct5_run_identity(
        result=ct5_result,
        analytics=ct5_analytics,
        ct4_analytics=ct4_tail,
        ct4_identity=ct4_identity,
    )
    return CT6CatalogueRunResult(
        request=request,
        ct4_result=ct4_result,
        ct4_tail_analytics=ct4_tail,
        ct4_frequency_analytics=ct4_frequency,
        ct4_identity=ct4_identity,
        ct5_result=ct5_result,
        ct5_analytics=ct5_analytics,
        ct5_identity=ct5_identity,
    )


def _build_simulation_input(adapted: AdaptedCatalogueRequest) -> CT4SimulationInput:
    wire = adapted.request.input
    program = wire.program
    trials = tuple(
        CT4AnnualTrialInput(
            annual_trial_id=trial.annual_trial_id,
            catalogue_source_id=trial.catalogue_source_id,
            occurrences=tuple(
                _build_occurrence(
                    occurrence,
                    adapted=adapted,
                    source_version=wire.simulation.source_version,
                )
                for occurrence in trial.occurrences
            ),
        )
        for trial in adapted.trials
    )
    return CT4SimulationInput(
        simulation_id=wire.simulation.simulation_id,
        trial_count=wire.simulation.trial_count,
        trials=trials,
        catalogue_version=wire.simulation.catalogue_version,
        source_version=wire.simulation.source_version,
        simulation_seed=wire.simulation.simulation_seed,
        occurrence_definition_mode=OccurrenceDefinitionMode.CATALOGUE_DEFINED,
        tail_configuration=adapted.tail_configuration,
        tolerance_profile=adapted.tolerance_profile,
        hours_clause_scenario=None,
        description=program.description,
        source_reference=program.source_reference,
        rule_reference=program.rule_reference,
    )


def _build_occurrence(
    occurrence: AdaptedSourceOccurrence,
    *,
    adapted: AdaptedCatalogueRequest,
    source_version: str,
) -> CT4OccurrenceInput:
    loss_basis = build_loss_basis(occurrence.loss_basis)
    waterfall_input = InuringWaterfallInput(
        loss_basis=loss_basis,
        covers=occurrence.inuring_covers,
    )
    waterfall_result = apply_inuring_waterfall(waterfall_input)
    ct2_metadata = build_ct2_run_metadata(
        waterfall_input=waterfall_input,
        source_version=source_version,
    )
    program = adapted.request.input.program
    program_input = CT3ProgramInput(
        program_id=program.program_id,
        ct2_result=waterfall_result,
        ct2_metadata=ct2_metadata,
        layers=adapted.layers,
        intentional_gap_acknowledged=program.intentional_gap_acknowledged,
        overlap_coordination=program.overlap_coordination,
        priority_order=program.priority_order,
        description=program.description,
        source_reference=program.source_reference,
        rule_reference=program.rule_reference,
    )
    return CT4OccurrenceInput(
        annual_trial_id=occurrence.annual_trial_id,
        event_id=occurrence.event_id,
        event_time=occurrence.event_time,
        event_sequence=occurrence.event_sequence,
        peril=occurrence.peril,
        region=occurrence.region,
        program_input=program_input,
        source_reference=occurrence.source_reference,
        trace_reference=occurrence.trace_reference,
    )
