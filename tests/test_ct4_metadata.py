"""CT4 canonical input/result serialization and identity tests."""

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from cat_treaty.ct4_metadata import (
    CT4_ENGINE_VERSION,
    CT4_SCHEMA_VERSION,
    build_ct4_input_hash,
    build_ct4_run_identity,
    canonicalize_ct4_inputs,
    canonicalize_ct4_result,
    serialize_ct4_inputs,
    serialize_ct4_result,
)
from cat_treaty.ct4_models import CT4AnnualTrialInput, HoursElectionMethod, OccurrenceDefinitionMode
from cat_treaty.occurrence_definition import evaluate_hours_clause_scenario
from cat_treaty.metadata import PRODUCT_ID, PRODUCT_ROUTE
from cat_treaty.simulation import apply_catalogue_simulation
from cat_treaty.tail import calculate_tail_analytics, calculate_tail_analytics_from_rows
from tests.test_ct4_models import hours_scenario, hours_terms, simulation
from tests.test_ct4_occurrence_definition import component
from tests.test_ct4_simulation import catalogue, event


def completed_catalogue(*, seed: int = 42):
    request = replace(
        catalogue(
            CT4AnnualTrialInput(
                1,
                "T1",
                (
                    event("E2", 45_000_000.0, event_time=2.0),
                    event("E1", 5_000_000.0, event_time=1.0),
                ),
            ),
            CT4AnnualTrialInput(2, "T2", ()),
        ),
        simulation_seed=seed,
    )
    result = apply_catalogue_simulation(request)
    return request, result, calculate_tail_analytics(result)


def completed_hours(*, method=HoursElectionMethod.MAXIMUM_SUBJECT_LOSS, manual_id=None):
    components = (
        component("C2", 25_000_000.0, 200.0),
        component("C1", 25_000_000.0, 100.0),
    )
    terms = hours_terms(
        authorized_election_methods=(
            HoursElectionMethod.EARLIEST_VALID_WINDOW,
            HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
            HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
            HoursElectionMethod.MANUAL,
        ),
        selected_election_method=method,
        manual_candidate_set_id=manual_id,
    )
    scenario = hours_scenario(components=components, terms=terms)
    request = simulation(
        trial_count=1,
        trials=(CT4AnnualTrialInput(1, "hours", ()),),
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        hours_clause_scenario=scenario,
    )
    result = evaluate_hours_clause_scenario(scenario, source_version=request.source_version)
    assert result.annual_row is not None
    analytics = calculate_tail_analytics_from_rows(
        (result.annual_row,),
        config=request.tail_configuration,
        relative_tolerance=request.tolerance_profile.relative_tolerance,
        absolute_tolerance=request.tolerance_profile.absolute_currency_tolerance,
    )
    return request, result, analytics


def test_ct4_version_literals_are_frozen() -> None:
    assert CT4_ENGINE_VERSION == "ct4.0.0"
    assert CT4_SCHEMA_VERSION == "ct4.0"


def test_input_serialization_is_canonical_json_and_sha256() -> None:
    request, _, _ = completed_catalogue()
    serialized = serialize_ct4_inputs(request)
    decoded = json.loads(serialized)
    assert serialized.decode() == json.dumps(
        decoded, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    digest = build_ct4_input_hash(request)
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


def test_hash_payload_is_bound_to_treaty_and_upstream_engine_versions() -> None:
    request, _, _ = completed_catalogue()
    payload = canonicalize_ct4_inputs(request)
    occurrence = payload["trials"][0]["occurrences"][0]  # type: ignore[index]
    assert occurrence["ct2_engine_version"] == "ct2.0.0"
    assert occurrence["ct3_engine_version"] == "ct3.0.0"
    assert PRODUCT_ID == "cat_treaty_learning_lab"
    assert PRODUCT_ROUTE == "/cat-treaty"


def test_g40_non_contractual_event_order_canonicalizes_identically() -> None:
    first, _, _ = completed_catalogue()
    first_trial = first.trials[0]
    second = replace(
        first,
        trials=(replace(first_trial, occurrences=tuple(reversed(first_trial.occurrences))), first.trials[1]),
    )
    assert serialize_ct4_inputs(first) == serialize_ct4_inputs(second)
    assert build_ct4_input_hash(first) == build_ct4_input_hash(second)


def test_hours_component_order_canonicalizes_identically() -> None:
    first, _, _ = completed_hours()
    scenario = first.hours_clause_scenario
    assert scenario is not None
    second = replace(first, hours_clause_scenario=replace(scenario, components=tuple(reversed(scenario.components))))
    assert serialize_ct4_inputs(first) == serialize_ct4_inputs(second)


def test_descriptions_references_and_display_text_do_not_change_input_hash() -> None:
    request, _, _ = completed_catalogue()
    changed_event = replace(
        request.trials[0].occurrences[0],
        source_reference="display:other",
        trace_reference="trace:other",
        program_input=replace(
            request.trials[0].occurrences[0].program_input,
            description="Other display title",
            source_reference="other",
            rule_reference="other",
        ),
    )
    changed_trial = replace(request.trials[0], occurrences=(changed_event, request.trials[0].occurrences[1]))
    changed = replace(
        request,
        trials=(changed_trial, request.trials[1]),
        description="Other simulation title",
        source_reference="other source",
        rule_reference="other rule",
    )
    assert build_ct4_input_hash(request) == build_ct4_input_hash(changed)


@pytest.mark.parametrize(
    "change",
    [
        {"simulation_seed": 43},
        {"catalogue_version": "catalogue-v2"},
        {"source_version": "source-v2"},
        {"simulation_id": "SIM-OTHER"},
    ],
)
def test_identity_and_provenance_changes_change_input_hash(change) -> None:
    request, _, _ = completed_catalogue()
    assert build_ct4_input_hash(request) != build_ct4_input_hash(replace(request, **change))


def test_empty_trials_are_present_in_normalized_input() -> None:
    request, _, _ = completed_catalogue()
    payload = canonicalize_ct4_inputs(request)
    assert len(payload["trials"]) == 2
    assert payload["trials"][1]["occurrences"] == []  # type: ignore[index]


def test_contractual_election_and_authorization_are_hash_inputs() -> None:
    automatic, _, _ = completed_hours()
    scenario = automatic.hours_clause_scenario
    assert scenario is not None
    manual_terms = replace(
        scenario.terms,
        selected_election_method=HoursElectionMethod.MANUAL,
        manual_candidate_set_id="SET-003",
    )
    manual = replace(automatic, hours_clause_scenario=replace(scenario, terms=manual_terms))
    assert build_ct4_input_hash(automatic) != build_ct4_input_hash(manual)
    reduced_terms = replace(
        scenario.terms,
        authorized_election_methods=scenario.terms.authorized_election_methods[:-1],
    )
    reduced = replace(automatic, hours_clause_scenario=replace(scenario, terms=reduced_terms))
    assert build_ct4_input_hash(automatic) != build_ct4_input_hash(reduced)


def test_completed_catalogue_identity_is_exactly_reproducible() -> None:
    request, result, analytics = completed_catalogue()
    first = build_ct4_run_identity(simulation_input=request, result=result, analytics=analytics)
    second = build_ct4_run_identity(simulation_input=request, result=result, analytics=analytics)
    assert first == second
    assert first.simulation_id == request.simulation_id
    assert len(first.input_hash) == len(first.result_hash) == 64
    with pytest.raises(FrozenInstanceError):
        first.result_hash = "x" * 64  # type: ignore[misc]
    payload = canonicalize_ct4_result(result, analytics)
    assert "gross_contractual_recovery_pre_annual_capacity" in payload["occurrence_rows"][0]  # type: ignore[index]


def test_result_hash_is_bound_to_input_hash_and_versions() -> None:
    request, result, analytics = completed_catalogue()
    baseline = build_ct4_run_identity(simulation_input=request, result=result, analytics=analytics)
    engine = build_ct4_run_identity(
        simulation_input=request, result=result, analytics=analytics, engine_version="ct4.0.1"
    )
    schema = build_ct4_run_identity(
        simulation_input=request, result=result, analytics=analytics, schema_version="ct4.1"
    )
    assert len({baseline.input_hash, engine.input_hash, schema.input_hash}) == 3
    assert len({baseline.result_hash, engine.result_hash, schema.result_hash}) == 3


def test_result_serialization_excludes_explanation_wording() -> None:
    _, result, analytics = completed_catalogue()
    row = result.occurrence_rows[0]
    altered_geometry = replace(
        row.assessment.geometry,
        notices=("Different explanation",),
    )
    altered_assessment = replace(
        row.assessment,
        geometry=altered_geometry,
        program_result=replace(
            row.assessment.program_result,
            geometry=altered_geometry,
        ),
    )
    altered_row = replace(row, assessment=altered_assessment, trace_references=("other",))
    altered_annual = replace(
        result.annual_rows[0], occurrence_rows=(altered_row, result.annual_rows[0].occurrence_rows[1])
    )
    altered = replace(
        result,
        occurrence_rows=(altered_row, result.occurrence_rows[1]),
        annual_rows=(altered_annual, result.annual_rows[1]),
    )
    assert serialize_ct4_result(result, analytics) == serialize_ct4_result(altered, analytics)


def test_analytics_must_match_result_annual_samples() -> None:
    _, result, analytics = completed_catalogue()
    subject = analytics.perspectives[0]
    altered_subject = replace(subject, oep_sample=tuple(reversed(subject.oep_sample)))
    altered = replace(analytics, perspectives=(altered_subject,) + analytics.perspectives[1:])
    with pytest.raises(ValueError, match="do not match"):
        canonicalize_ct4_result(result, altered)


def test_completed_hours_result_receives_deterministic_identity() -> None:
    request, result, analytics = completed_hours()
    identity = build_ct4_run_identity(simulation_input=request, result=result, analytics=analytics)
    assert identity.simulation_id == request.simulation_id
    payload = canonicalize_ct4_result(result, analytics)
    assert payload["result_type"] == "hours_clause"
    assert payload["selected_candidate_set_id"] == result.selected_candidate_set_id


def test_blocked_hours_result_cannot_receive_completed_identity() -> None:
    request, _, analytics = completed_hours()
    scenario = request.hours_clause_scenario
    assert scenario is not None
    bad_terms = replace(
        scenario.terms,
        selected_election_method=HoursElectionMethod.MANUAL,
        manual_candidate_set_id="UNKNOWN",
    )
    bad_scenario = replace(scenario, terms=bad_terms)
    bad_request = replace(request, hours_clause_scenario=bad_scenario)
    blocked = evaluate_hours_clause_scenario(bad_scenario, source_version=request.source_version)
    with pytest.raises(ValueError, match="blocked"):
        build_ct4_run_identity(
            simulation_input=bad_request, result=blocked, analytics=analytics
        )


def test_result_must_match_simulation_input() -> None:
    request, result, analytics = completed_catalogue()
    with pytest.raises(ValueError, match="match"):
        build_ct4_run_identity(
            simulation_input=replace(request, simulation_id="OTHER"),
            result=result,
            analytics=analytics,
        )


@pytest.mark.parametrize("name", ["engine_version", "schema_version"])
def test_blank_versions_are_rejected(name: str) -> None:
    request, result, analytics = completed_catalogue()
    with pytest.raises(ValueError, match=name):
        build_ct4_run_identity(
            simulation_input=request,
            result=result,
            analytics=analytics,
            **{name: " "},
        )


def test_metadata_rejects_wrong_input_result_and_analytics_types() -> None:
    request, result, analytics = completed_catalogue()
    with pytest.raises(TypeError):
        canonicalize_ct4_inputs({})  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        canonicalize_ct4_result({}, analytics)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        canonicalize_ct4_result(result, {})  # type: ignore[arg-type]
