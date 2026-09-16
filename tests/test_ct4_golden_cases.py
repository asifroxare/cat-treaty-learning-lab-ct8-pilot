"""Consolidated CT4 G11, G13 and G35-G46 acceptance evidence."""

from dataclasses import replace

import pytest

from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.ct4_metadata import build_ct4_input_hash, build_ct4_run_identity
from cat_treaty.ct4_models import (
    CandidateAdmissibility,
    CT4AnnualTrialInput,
    HoursElectionIssueCode,
    HoursElectionMethod,
    HoursElectionStatus,
    HoursExclusionCode,
)
from cat_treaty.occurrence_definition import evaluate_hours_clause_scenario
from cat_treaty.simulation import CT4PreflightError, apply_catalogue_simulation
from cat_treaty.stability import run_stability_gate
from cat_treaty.tail import calculate_tail_analytics, empirical_tvar, nearest_rank_quantile
from tests.test_ct3_models import layer, program
from tests.test_ct4_metadata import completed_catalogue
from tests.test_ct4_models import hours_scenario, hours_terms
from tests.test_ct4_occurrence_definition import component
from tests.test_ct4_simulation import catalogue, event


def hours_case(method, manual_id=None):
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
    return hours_scenario(
        components=(
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        terms=terms,
    )


def test_g11_seeded_catalogue_reproducibility() -> None:
    request, result, analytics = completed_catalogue(seed=20260915)
    first = build_ct4_run_identity(simulation_input=request, result=result, analytics=analytics)
    repeated_result = apply_catalogue_simulation(request)
    repeated_analytics = calculate_tail_analytics(repeated_result)
    second = build_ct4_run_identity(
        simulation_input=request,
        result=repeated_result,
        analytics=repeated_analytics,
    )
    assert first == second


def test_g13_combined_valid_occurrence_beats_invalid_split_only_after_admissibility() -> None:
    result = evaluate_hours_clause_scenario(
        hours_case(HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY),
        source_version="g13",
    )
    combined = next(item for item in result.candidate_sets if item.candidate_set_id == "SET-001")
    split = next(item for item in result.candidate_sets if item.candidate_set_id == "SET-003")
    assert combined.admissibility is CandidateAdmissibility.VALID
    assert split.total_contractual_recovery > combined.total_contractual_recovery  # type: ignore[operator]
    assert split.admissibility is CandidateAdmissibility.EXCLUDED
    assert HoursExclusionCode.OVERLAPPING_WINDOWS in split.exclusion_codes
    assert result.selected_candidate_set_id == combined.candidate_set_id


def test_g35_empty_trial_stays_in_all_six_samples() -> None:
    result = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(1, "T1", (event("E1", 45_000_000.0),)),
            CT4AnnualTrialInput(2, "T2", ()),
        )
    )
    analytics = calculate_tail_analytics(result)
    assert all(view.oep_sample[1] == 0 and view.aep_sample[1] == 0 for view in analytics.perspectives)


def test_g36_two_occurrences_oep_is_max_and_aep_is_sum() -> None:
    annual = apply_catalogue_simulation(
        catalogue(
            CT4AnnualTrialInput(
                1,
                "T1",
                (
                    event("E1", 5_000_000.0, event_time=1.0),
                    event("E2", 45_000_000.0, event_time=2.0),
                ),
            )
        )
    ).annual_rows[0]
    assert (annual.subject_oep, annual.subject_aep) == (45_000_000.0, 50_000_000.0)
    assert (annual.recovery_oep_pre_annual_capacity, annual.recovery_aep_pre_annual_capacity) == (35_000_000.0, 35_000_000.0)


def test_g37_annual_and_aal_reconciliation() -> None:
    _, result, analytics = completed_catalogue()
    assert all(row.reconciliation_passed for row in result.annual_rows)
    assert analytics.aal_reconciliation_passed is True


def test_g38_g39_nearest_rank_and_tvar_boundaries() -> None:
    sample = (0.0, 10.0, 20.0, 30.0)
    assert nearest_rank_quantile(sample, 0.5) == 10.0
    assert empirical_tvar(sample, 0.5) == 20.0


def test_g40_input_permutation_preserves_hash_ledgers_and_analytics() -> None:
    first, first_result, first_analytics = completed_catalogue()
    trial = first.trials[0]
    second = replace(
        first,
        trials=(replace(trial, occurrences=tuple(reversed(trial.occurrences))), first.trials[1]),
    )
    second_result = apply_catalogue_simulation(second)
    second_analytics = calculate_tail_analytics(second_result)
    assert build_ct4_input_hash(first) == build_ct4_input_hash(second)
    assert first_result.annual_rows == second_result.annual_rows
    assert first_analytics == second_analytics


def test_g41_seed_change_changes_input_identity_and_is_disclosed() -> None:
    first, _, _ = completed_catalogue(seed=11)
    second, _, _ = completed_catalogue(seed=29)
    assert first.simulation_seed == 11 and second.simulation_seed == 29
    assert build_ct4_input_hash(first) != build_ct4_input_hash(second)


def test_g42_frozen_stability_gate_passes() -> None:
    gate = run_stability_gate()
    assert len(gate.comparisons) == 70
    assert gate.passed and all(item.passed for item in gate.comparisons)


@pytest.mark.parametrize(
    "method",
    [
        HoursElectionMethod.EARLIEST_VALID_WINDOW,
        HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
        HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
    ],
)
def test_g43_authorized_elections_use_valid_candidates_only(method) -> None:
    result = evaluate_hours_clause_scenario(hours_case(method), source_version="g43")
    assert result.election_status is HoursElectionStatus.SELECTED
    assert result.selected_candidate_set_id in result.valid_candidate_set_ids


def test_g44_invalid_higher_recovery_is_visible_and_rejected() -> None:
    result = evaluate_hours_clause_scenario(
        hours_case(HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY),
        source_version="g44",
    )
    invalid = next(item for item in result.candidate_sets if item.candidate_set_id == "SET-003")
    assert invalid.total_contractual_recovery is not None
    assert invalid.candidate_set_id not in result.valid_candidate_set_ids
    assert invalid.exclusion_codes


def test_g45_invalid_manual_election_is_blocked() -> None:
    result = evaluate_hours_clause_scenario(
        hours_case(HoursElectionMethod.MANUAL, "UNKNOWN"),
        source_version="g45",
    )
    assert result.election_status is HoursElectionStatus.BLOCKED
    assert result.election_issues[0].code is HoursElectionIssueCode.MANUAL_SELECTION_INVALID


def test_g46_one_blocked_occurrence_blocks_complete_simulation() -> None:
    layers = (
        layer("L1", attachment=0.0, occurrence_limit=20.0),
        layer("L2", attachment=10.0, occurrence_limit=20.0),
    )
    blocked = event(
        "BLOCKED",
        25.0,
        layers=layers,
        overlap_coordination=OverlapCoordination.NONE,
    )
    request = catalogue(CT4AnnualTrialInput(1, "T1", (blocked,)))
    with pytest.raises(CT4PreflightError) as error:
        apply_catalogue_simulation(request)
    assert error.value.issues[0].event_id == "BLOCKED"
