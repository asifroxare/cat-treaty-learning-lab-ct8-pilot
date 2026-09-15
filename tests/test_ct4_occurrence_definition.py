"""Bounded hours-window generation, admissibility, election and evidence tests."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.ct4_models import (
    CandidateAdmissibility,
    HoursClauseScenario,
    HoursElectionIssueCode,
    HoursElectionMethod,
    HoursElectionStatus,
    HoursExclusionCode,
    HoursLossComponent,
    OccurrenceDefinitionMode,
)
from cat_treaty.occurrence_definition import (
    evaluate_hours_clause_scenario,
    generate_candidate_windows,
)
from tests.test_ct3_models import layer, program
from tests.test_ct4_models import hours_scenario, hours_terms


def component(
    component_id: str,
    loss: float,
    timestamp: float,
    *,
    peril: str = "hurricane",
    region: str = "coastal",
    cause: str = "CAUSE-1",
) -> HoursLossComponent:
    return HoursLossComponent(
        component_id,
        loss,
        timestamp,
        peril,
        region,
        cause,
        f"loss:{component_id}",
    )


def scenario(
    components: tuple[HoursLossComponent, ...],
    *,
    method: HoursElectionMethod = HoursElectionMethod.EARLIEST_VALID_WINDOW,
    manual_id: str | None = None,
    program_terms=None,
    **term_changes: object,
) -> HoursClauseScenario:
    authorized = (
        HoursElectionMethod.EARLIEST_VALID_WINDOW,
        HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
        HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
        HoursElectionMethod.MANUAL,
    )
    terms = hours_terms(
        authorized_election_methods=authorized,
        selected_election_method=method,
        manual_candidate_set_id=manual_id,
        **term_changes,
    )
    return hours_scenario(
        components=components,
        terms=terms,
        program_terms_source=program() if program_terms is None else program_terms,
    )


def test_windows_are_component_anchored_ordered_and_bounded() -> None:
    request = scenario(
        (
            component("C2", 20.0, 150.0),
            component("C1", 10.0, 100.0),
        )
    )
    windows = generate_candidate_windows(request)
    assert tuple(item.candidate_id for item in windows) == ("W001", "W002")
    assert windows[0].component_ids == ("C1", "C2")
    assert windows[1].component_ids == ("C2",)
    assert all(item.end - item.start == 72.0 for item in windows)


def test_twelve_components_produce_the_frozen_4095_set_bound() -> None:
    components = tuple(
        component(f"C{index:02d}", 1_000_000.0, index * 100.0)
        for index in range(1, 13)
    )
    result = evaluate_hours_clause_scenario(
        scenario(components, method=HoursElectionMethod.MAXIMUM_SUBJECT_LOSS),
        source_version="ct4-hours-test",
    )
    assert len(result.candidate_windows) == 12
    assert len(result.candidate_sets) == 4095
    assert result.selected_candidate_set_id == "SET-FFF"


def test_inclusive_start_exclusive_end_boundary_is_frozen() -> None:
    request = scenario(
        (
            component("START", 1.0, 100.0),
            component("END", 1.0, 172.0),
        )
    )
    windows = generate_candidate_windows(request)
    assert windows[0].component_ids == ("START",)


def test_window_records_all_applicable_rule_specific_exclusions() -> None:
    bad = component(
        "BAD",
        1.0,
        9000.0,
        peril="earthquake",
        region="inland",
        cause="CAUSE-2",
    )
    request = scenario(
        (component("GOOD", 1.0, 8990.0), bad),
        treaty_term_end=8760.0,
    )
    window = generate_candidate_windows(request)[0]
    assert window.admissibility is CandidateAdmissibility.EXCLUDED
    assert window.exclusion_codes == (
        HoursExclusionCode.OUTSIDE_TREATY_TERM,
        HoursExclusionCode.PERIL_OR_CAUSE_MISMATCH,
        HoursExclusionCode.GEOGRAPHIC_MISMATCH,
        HoursExclusionCode.CAUSAL_LINK_FAILURE,
    )
    assert "BAD" in window.affected_ids


def test_g43_all_generated_sets_are_classified_before_election() -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        method=HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert len(result.candidate_windows) == 2
    assert len(result.candidate_sets) == 3
    assert all(
        item.admissibility in (CandidateAdmissibility.VALID, CandidateAdmissibility.EXCLUDED)
        for item in result.candidate_sets
    )
    assert result.election_status is HoursElectionStatus.SELECTED
    assert result.selected_candidate_set_id == "SET-001"


def test_g44_invalid_higher_recovery_split_is_visible_but_cannot_win() -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        method=HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    invalid_split = next(item for item in result.candidate_sets if item.candidate_set_id == "SET-003")
    elected = next(item for item in result.candidate_sets if item.candidate_set_id == result.selected_candidate_set_id)
    assert invalid_split.total_contractual_recovery > elected.total_contractual_recovery  # type: ignore[operator]
    assert invalid_split.admissibility is CandidateAdmissibility.EXCLUDED
    assert HoursExclusionCode.DUPLICATE_COMPONENT in invalid_split.exclusion_codes
    assert HoursExclusionCode.OVERLAPPING_WINDOWS in invalid_split.exclusion_codes
    assert {"C2", "W001", "W002"}.issubset(invalid_split.affected_ids)
    assert invalid_split.rule_reference == "CT4-section-8"
    assert "SET-003" not in result.valid_candidate_set_ids


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (HoursElectionMethod.EARLIEST_VALID_WINDOW, "SET-001"),
        (HoursElectionMethod.MAXIMUM_SUBJECT_LOSS, "SET-001"),
        (HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY, "SET-001"),
    ],
)
def test_each_automatic_election_uses_valid_sets_only(method, expected) -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        method=method,
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.selected_candidate_set_id == expected
    assert result.tie_break_facts


def test_manual_election_accepts_one_complete_valid_generated_set() -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        method=HoursElectionMethod.MANUAL,
        manual_id="SET-002",
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.election_status is HoursElectionStatus.SELECTED
    assert result.selected_candidate_set_id == "SET-002"
    assert result.selected_occurrence_rows[0].source_event_ids == ("C2",)


@pytest.mark.parametrize("manual_id", ["UNKNOWN", "SET-003"])
def test_g45_unknown_or_excluded_manual_selection_is_blocked(manual_id: str) -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 110.0),
        ),
        method=HoursElectionMethod.MANUAL,
        manual_id=manual_id,
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.election_status is HoursElectionStatus.BLOCKED
    assert result.selected_candidate_set_id is None
    assert result.annual_row is None
    assert result.election_issues[0].code is HoursElectionIssueCode.MANUAL_SELECTION_INVALID


def test_no_valid_window_blocks_without_partial_analytics() -> None:
    request = scenario((component("BAD", 10.0, 9000.0),))
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.election_status is HoursElectionStatus.BLOCKED
    assert result.election_issues[0].code is HoursElectionIssueCode.NO_VALID_CANDIDATE_SET
    assert result.selected_occurrence_rows == ()
    assert result.annual_row is None


def test_blocked_ct3_geometry_blocks_hours_election_before_recovery() -> None:
    overlapping = (
        layer("L1", attachment=0.0, occurrence_limit=20.0),
        layer("L2", attachment=10.0, occurrence_limit=20.0),
    )
    request = scenario(
        (component("C1", 25.0, 100.0),),
        program_terms=program(
            layers=overlapping,
            overlap_coordination=OverlapCoordination.NONE,
        ),
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.election_issues[0].code is HoursElectionIssueCode.PROGRAM_GEOMETRY_BLOCKED
    assert result.candidate_windows == ()


def test_selected_occurrences_reconcile_to_one_annual_hours_ledger() -> None:
    request = scenario(
        (
            component("C1", 25_000_000.0, 100.0),
            component("C2", 25_000_000.0, 200.0),
        ),
        method=HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
    )
    result = evaluate_hours_clause_scenario(request, source_version="ct4-hours-test")
    assert result.selected_candidate_set_id == "SET-003"
    assert len(result.selected_occurrence_rows) == 2
    assert all(
        item.occurrence_definition_mode is OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING
        for item in result.selected_occurrence_rows
    )
    assert result.annual_row.subject_aep == 50_000_000.0  # type: ignore[union-attr]
    assert result.annual_row.recovery_aep_pre_annual_capacity == 30_000_000.0  # type: ignore[union-attr]
    assert result.annual_row.net_aep_pre_annual_capacity == 20_000_000.0  # type: ignore[union-attr]


def test_hours_result_is_immutable() -> None:
    result = evaluate_hours_clause_scenario(
        scenario((component("C1", 25_000_000.0, 100.0),)),
        source_version="ct4-hours-test",
    )
    with pytest.raises(FrozenInstanceError):
        result.selected_candidate_set_id = "OTHER"  # type: ignore[misc]


def test_hours_entry_requires_canonical_scenario_and_source_version() -> None:
    with pytest.raises(TypeError):
        evaluate_hours_clause_scenario({}, source_version="x")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        evaluate_hours_clause_scenario(hours_scenario(), source_version=" ")
