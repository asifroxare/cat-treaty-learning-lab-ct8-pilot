"""Canonical CT4 input/result serialization and version-bound SHA-256 identities."""

import hashlib
import json

from cat_treaty.ct3_metadata import (
    CT3_ENGINE_VERSION,
    CT3_SCHEMA_VERSION,
    canonicalize_ct3_inputs,
)
from cat_treaty.ct4_models import (
    CT4CatalogueResult,
    CT4RunIdentity,
    CT4SimulationInput,
    CT4TailAnalytics,
    HoursClauseResult,
    HoursElectionStatus,
    OccurrenceDefinitionMode,
)
from cat_treaty.geometry import geometry_order
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE


CT4_ENGINE_VERSION = "ct4.0.0"
CT4_SCHEMA_VERSION = "ct4.0"


def canonicalize_ct4_inputs(simulation_input: CT4SimulationInput) -> dict[str, object]:
    """Return calculation-relevant inputs with non-contractual order normalized."""

    if not isinstance(simulation_input, CT4SimulationInput):
        raise TypeError("simulation_input must be CT4SimulationInput")
    payload: dict[str, object] = {
        "catalogue_version": simulation_input.catalogue_version,
        "occurrence_definition_mode": simulation_input.occurrence_definition_mode.value,
        "simulation_id": simulation_input.simulation_id,
        "simulation_seed": simulation_input.simulation_seed,
        "source_version": simulation_input.source_version,
        "tail_configuration": {
            "probability_levels": sorted(float(item) for item in simulation_input.tail_configuration.probability_levels),
            "return_periods": sorted(float(item) for item in simulation_input.tail_configuration.return_periods),
            "tvar_levels": sorted(float(item) for item in simulation_input.tail_configuration.tvar_levels),
        },
        "tolerance_profile": {
            "absolute_currency_tolerance": float(simulation_input.tolerance_profile.absolute_currency_tolerance),
            "relative_tolerance": float(simulation_input.tolerance_profile.relative_tolerance),
        },
        "trial_count": simulation_input.trial_count,
        "trials": [
            {
                "annual_trial_id": trial.annual_trial_id,
                "catalogue_source_id": trial.catalogue_source_id,
                "occurrences": [
                    _catalogue_occurrence(item)
                    for item in sorted(
                        trial.occurrences,
                        key=lambda event: (event.event_time, event.event_sequence, event.event_id),
                    )
                ],
            }
            for trial in simulation_input.trials
        ],
    }
    if simulation_input.hours_clause_scenario is not None:
        payload["hours_clause_scenario"] = _hours_scenario(simulation_input.hours_clause_scenario)
    return payload


def serialize_ct4_inputs(simulation_input: CT4SimulationInput) -> bytes:
    return _serialize(canonicalize_ct4_inputs(simulation_input))


def build_ct4_input_hash(
    simulation_input: CT4SimulationInput,
    *,
    engine_version: str = CT4_ENGINE_VERSION,
    schema_version: str = CT4_SCHEMA_VERSION,
) -> str:
    engine = _nonblank("engine_version", engine_version)
    schema = _nonblank("schema_version", schema_version)
    return _hash(
        {
            "actuarial_inputs": canonicalize_ct4_inputs(simulation_input),
            "engine_version": engine,
            "product_id": PRODUCT_ID,
            "product_route": PRODUCT_ROUTE,
            "schema_version": schema,
        }
    )


def canonicalize_ct4_result(
    result: CT4CatalogueResult | HoursClauseResult,
    analytics: CT4TailAnalytics,
) -> dict[str, object]:
    """Return completed ledgers, election evidence and F19-F24 outputs."""

    if not isinstance(analytics, CT4TailAnalytics):
        raise TypeError("analytics must be CT4TailAnalytics")
    _validate_analytics_matches_result(result, analytics)
    if isinstance(result, CT4CatalogueResult):
        result_payload: dict[str, object] = {
            "result_type": "catalogue",
            "occurrence_rows": [_occurrence_row(item) for item in result.occurrence_rows],
            "annual_rows": [_annual_row(item) for item in result.annual_rows],
            "preflight_passed": result.preflight_passed,
        }
    elif isinstance(result, HoursClauseResult):
        if result.election_status is not HoursElectionStatus.SELECTED or result.annual_row is None:
            raise ValueError("blocked hours-clause result cannot receive a completed result hash")
        result_payload = {
            "result_type": "hours_clause",
            "candidate_windows": [
                {
                    "admissibility": item.admissibility.value,
                    "affected_ids": list(item.affected_ids),
                    "candidate_id": item.candidate_id,
                    "component_ids": list(item.component_ids),
                    "end": float(item.end),
                    "exclusion_codes": [code.value for code in item.exclusion_codes],
                    "start": float(item.start),
                    "subject_loss": float(item.subject_loss),
                }
                for item in result.candidate_windows
            ],
            "candidate_sets": [
                {
                    "admissibility": item.admissibility.value,
                    "affected_ids": list(item.affected_ids),
                    "candidate_set_id": item.candidate_set_id,
                    "exclusion_codes": [code.value for code in item.exclusion_codes],
                    "total_contractual_recovery": item.total_contractual_recovery,
                    "total_subject_loss": float(item.total_subject_loss),
                    "window_ids": list(item.window_ids),
                }
                for item in result.candidate_sets
            ],
            "selected_candidate_set_id": result.selected_candidate_set_id,
            "selected_election_method": result.selected_election_method.value,
            "selected_occurrence_rows": [_occurrence_row(item) for item in result.selected_occurrence_rows],
            "annual_rows": [_annual_row(result.annual_row)],
            "valid_candidate_set_ids": list(result.valid_candidate_set_ids),
        }
    else:
        raise TypeError("result must be CT4CatalogueResult or HoursClauseResult")
    result_payload["analytics"] = _analytics(analytics)
    return result_payload


def serialize_ct4_result(
    result: CT4CatalogueResult | HoursClauseResult,
    analytics: CT4TailAnalytics,
) -> bytes:
    return _serialize(canonicalize_ct4_result(result, analytics))


def build_ct4_run_identity(
    *,
    simulation_input: CT4SimulationInput,
    result: CT4CatalogueResult | HoursClauseResult,
    analytics: CT4TailAnalytics,
    engine_version: str = CT4_ENGINE_VERSION,
    schema_version: str = CT4_SCHEMA_VERSION,
) -> CT4RunIdentity:
    """Build one completed version-bound CT4 input and result identity."""

    engine = _nonblank("engine_version", engine_version)
    schema = _nonblank("schema_version", schema_version)
    _validate_result_matches_input(simulation_input, result)
    input_hash = build_ct4_input_hash(
        simulation_input,
        engine_version=engine,
        schema_version=schema,
    )
    result_hash = _hash(
        {
            "canonical_result": canonicalize_ct4_result(result, analytics),
            "engine_version": engine,
            "input_hash": input_hash,
            "schema_version": schema,
        }
    )
    return CT4RunIdentity(
        simulation_id=simulation_input.simulation_id,
        input_hash=input_hash,
        result_hash=result_hash,
        engine_version=engine,
        schema_version=schema,
    )


def _catalogue_occurrence(item) -> dict[str, object]:
    return {
        "annual_trial_id": item.annual_trial_id,
        "event_id": item.event_id,
        "event_sequence": item.event_sequence,
        "event_time": float(item.event_time),
        "peril": item.peril,
        "program_input": canonicalize_ct3_inputs(item.program_input),
        "ct2_engine_version": item.program_input.ct2_metadata.engine_version,
        "ct2_schema_version": item.program_input.ct2_metadata.schema_version,
        "ct3_engine_version": CT3_ENGINE_VERSION,
        "ct3_schema_version": CT3_SCHEMA_VERSION,
        "region": item.region,
    }


def _hours_scenario(scenario) -> dict[str, object]:
    terms = scenario.terms
    program = scenario.program_terms_source
    return {
        "components": [
            {
                "causal_event_id": item.causal_event_id,
                "component_id": item.component_id,
                "peril": item.peril,
                "region": item.region,
                "subject_loss": float(item.subject_loss),
                "timestamp": float(item.timestamp),
            }
            for item in sorted(scenario.components, key=lambda value: (value.timestamp, value.component_id))
        ],
        "program_terms": {
            "ct2_engine_version": program.ct2_metadata.engine_version,
            "ct2_schema_version": program.ct2_metadata.schema_version,
            "ct3_engine_version": CT3_ENGINE_VERSION,
            "ct3_schema_version": CT3_SCHEMA_VERSION,
            "intentional_gap_acknowledged": program.intentional_gap_acknowledged,
            "layers": [
                {
                    "attachment": float(layer.attachment),
                    "ceded_share": float(layer.ceded_share),
                    "currency": layer.currency,
                    "layer_id": layer.layer_id,
                    "occurrence_limit": float(layer.occurrence_limit),
                    "placement_share": float(layer.placement_share),
                }
                for layer in geometry_order(program.layers)
            ],
            "overlap_coordination": program.overlap_coordination.value,
            "priority_order": None if program.priority_order is None else list(program.priority_order),
            "program_id": program.program_id,
        },
        "scenario_id": scenario.scenario_id,
        "terms": {
            "authorized_election_methods": [item.value for item in terms.authorized_election_methods],
            "causal_link_required": terms.causal_link_required,
            "hours_duration": float(terms.hours_duration),
            "manual_candidate_set_id": terms.manual_candidate_set_id,
            "permitted_perils": sorted(terms.permitted_perils),
            "permitted_regions": sorted(terms.permitted_regions),
            "selected_election_method": terms.selected_election_method.value,
            "treaty_term_end": float(terms.treaty_term_end),
            "treaty_term_start": float(terms.treaty_term_start),
        },
    }


def _occurrence_row(item) -> dict[str, object]:
    result = item.assessment.program_result
    return {
        "annual_trial_id": item.annual_trial_id,
        "ct3_input_hash": item.assessment.metadata.input_hash,
        "elected_candidate_id": item.elected_candidate_id,
        "event_id": item.event_id,
        "insurer_net_loss_pre_annual_capacity": float(item.insurer_net_loss_pre_annual_capacity),
        "occurrence_definition_mode": item.occurrence_definition_mode.value,
        "occurrence_sequence": item.occurrence_sequence,
        "gross_contractual_recovery_pre_annual_capacity": float(
            item.gross_contractual_recovery_pre_annual_capacity
        ),
        "source_event_ids": list(item.source_event_ids),
        "subject_loss": float(item.subject_loss),
        "layer_recoveries": [
            {
                "allocated_covered_loss": float(layer.allocated_covered_loss),
                "gross_contractual_recovery": float(layer.gross_contractual_recovery),
                "layer_id": layer.layer_input.layer_id,
            }
            for layer in result.layer_results
        ],
    }


def _annual_row(item) -> dict[str, object]:
    return {
        "annual_trial_id": item.annual_trial_id,
        "common_oep_driver_event_id": item.common_oep_driver_event_id,
        "event_ids": [row.event_id for row in item.occurrence_rows],
        "net_aep_pre_annual_capacity": float(item.net_aep_pre_annual_capacity),
        "net_oep_pre_annual_capacity": float(item.net_oep_pre_annual_capacity),
        "reconciliation_passed": item.reconciliation_passed,
        "recovery_aep_pre_annual_capacity": float(item.recovery_aep_pre_annual_capacity),
        "recovery_oep_pre_annual_capacity": float(item.recovery_oep_pre_annual_capacity),
        "subject_aep": float(item.subject_aep),
        "subject_oep": float(item.subject_oep),
    }


def _estimate(item) -> dict[str, object]:
    return {
        "level": float(item.level),
        "value": float(item.value),
        "warnings": [
            {
                "code": warning.code.value,
                "observations_per_return_period": float(warning.observations_per_return_period),
                "return_period": float(warning.return_period),
            }
            for warning in item.warnings
        ],
    }


def _analytics(analytics: CT4TailAnalytics) -> dict[str, object]:
    return {
        "aal_reconciliation_passed": analytics.aal_reconciliation_passed,
        "perspectives": [
            {
                "aep_curve": [[item.rank, float(item.loss), float(item.exceedance_probability)] for item in view.aep_curve],
                "aep_return_period_estimates": [_estimate(item) for item in view.aep_return_period_estimates],
                "aep_sample": [float(item) for item in view.aep_sample],
                "aep_tvar_estimates": [_estimate(item) for item in view.aep_tvar_estimates],
                "aep_var_estimates": [_estimate(item) for item in view.aep_var_estimates],
                "annual_average_loss": float(view.annual_average_loss),
                "coefficient_of_variation": view.coefficient_of_variation,
                "coefficient_status": view.coefficient_status.value,
                "oep_curve": [[item.rank, float(item.loss), float(item.exceedance_probability)] for item in view.oep_curve],
                "oep_return_period_estimates": [_estimate(item) for item in view.oep_return_period_estimates],
                "oep_sample": [float(item) for item in view.oep_sample],
                "oep_tvar_estimates": [_estimate(item) for item in view.oep_tvar_estimates],
                "oep_var_estimates": [_estimate(item) for item in view.oep_var_estimates],
                "perspective": view.perspective.value,
                "population_standard_deviation": float(view.population_standard_deviation),
            }
            for view in analytics.perspectives
        ],
    }


def _validate_result_matches_input(simulation_input, result) -> None:
    if not isinstance(simulation_input, CT4SimulationInput):
        raise TypeError("simulation_input must be CT4SimulationInput")
    if isinstance(result, CT4CatalogueResult):
        if simulation_input.occurrence_definition_mode is not OccurrenceDefinitionMode.CATALOGUE_DEFINED or result.simulation_input != simulation_input:
            raise ValueError("catalogue result must match simulation_input")
    elif isinstance(result, HoursClauseResult):
        if simulation_input.occurrence_definition_mode is not OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING or result.scenario != simulation_input.hours_clause_scenario:
            raise ValueError("hours-clause result must match simulation_input")
    else:
        raise TypeError("result must be CT4CatalogueResult or HoursClauseResult")


def _validate_analytics_matches_result(result, analytics) -> None:
    if isinstance(result, CT4CatalogueResult):
        rows = result.annual_rows
    elif isinstance(result, HoursClauseResult):
        if result.election_status is not HoursElectionStatus.SELECTED or result.annual_row is None:
            raise ValueError("blocked hours-clause result cannot receive completed analytics")
        rows = (result.annual_row,)
    else:
        raise TypeError("result must be CT4CatalogueResult or HoursClauseResult")
    expected = (
        (tuple(float(row.subject_oep) for row in rows), tuple(float(row.subject_aep) for row in rows)),
        (
            tuple(float(row.recovery_oep_pre_annual_capacity) for row in rows),
            tuple(float(row.recovery_aep_pre_annual_capacity) for row in rows),
        ),
        (
            tuple(float(row.net_oep_pre_annual_capacity) for row in rows),
            tuple(float(row.net_aep_pre_annual_capacity) for row in rows),
        ),
    )
    actual = tuple((view.oep_sample, view.aep_sample) for view in analytics.perspectives)
    if actual != expected:
        raise ValueError("analytics samples do not match completed annual ledgers")


def _serialize(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(_serialize(payload)).hexdigest()


def _nonblank(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value
