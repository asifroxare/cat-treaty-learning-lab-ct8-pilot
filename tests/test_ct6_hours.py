"""CT6 hours-clause orchestration and identity acceptance."""

import pytest

from cat_treaty.ct4_models import CandidateAdmissibility, HoursElectionMethod, HoursElectionStatus, HoursExclusionCode
from cat_treaty.ct6_hours import CT6HoursContractBlockedError, CT6HoursRunResult, run_hours_clause
from cat_treaty.ct6_models import HoursComponentDTO
from tests.test_ct6_adapters import valid_hours_request


def component(component_id: str, loss: float, timestamp: float, **changes) -> HoursComponentDTO:
    values = dict(
        component_id=component_id, subject_loss=loss, timestamp=timestamp,
        peril="wind", region="R1", causal_event_id="storm",
        source_reference="source",
    )
    values.update(changes)
    return HoursComponentDTO(**values)


def test_hours_runs_valid_election_through_ct5_and_identities() -> None:
    result = run_hours_clause(valid_hours_request())
    assert isinstance(result, CT6HoursRunResult)
    assert result.ct4_result.election_status is HoursElectionStatus.SELECTED
    assert len(result.ct4_result.selected_occurrence_rows) == 2
    assert tuple(row.event_id for row in result.ct5_result.occurrence_rows) == tuple(
        row.event_id for row in result.ct4_result.selected_occurrence_rows
    )
    assert result.ct5_identity.ct4_input_hash == result.ct4_identity.input_hash
    assert result.ct5_identity.ct4_result_hash == result.ct4_identity.result_hash


def test_disclosed_ct2_source_is_calculated_and_preserved_before_hours_election() -> None:
    result = run_hours_clause(valid_hours_request())
    source = result.ct4_result.scenario.program_terms_source
    assert source.ct2_result.loss_basis.basis_input.initial_insured_loss == 45_000_000.0
    assert source.ct2_result.total_inuring_recovery == 4_500_000.0
    assert source.ct2_result.cat_xl_subject_loss == 40_500_000.0
    assert source.ct2_metadata.occurrence_id == "E1"


def test_invalid_higher_recovery_split_retains_rejection_evidence_and_cannot_enter_ct5() -> None:
    request = valid_hours_request(components=(
        component("C1", 25_000_000.0, 100.0),
        component("C2", 25_000_000.0, 110.0),
    ), selected_method=HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY)
    result = run_hours_clause(request)
    invalid = next(item for item in result.ct4_result.candidate_sets if item.candidate_set_id == "SET-003")
    assert invalid.admissibility is CandidateAdmissibility.EXCLUDED
    assert HoursExclusionCode.DUPLICATE_COMPONENT in invalid.exclusion_codes
    assert HoursExclusionCode.OVERLAPPING_WINDOWS in invalid.exclusion_codes
    elected_window_ids = {
        row.event_id.rsplit(":", 1)[-1]
        for row in result.ct5_result.occurrence_rows
    }
    assert elected_window_ids == {"W001"}
    assert "W002" not in elected_window_ids


def test_invalid_manual_election_blocks_without_ct5_or_identity() -> None:
    request = valid_hours_request(
        selected_method=HoursElectionMethod.MANUAL,
        manual_candidate_set_id="UNKNOWN",
    )
    with pytest.raises(CT6HoursContractBlockedError) as captured:
        run_hours_clause(request)
    blocked = captured.value.result
    assert blocked.election_status is HoursElectionStatus.BLOCKED
    assert blocked.selected_occurrence_rows == ()
    assert blocked.annual_row is None
    assert blocked.election_issues


def test_out_of_term_components_preserve_window_exclusion_evidence() -> None:
    request = valid_hours_request(components=(
        component("BAD", 10_000_000.0, 400.0),
    ))
    with pytest.raises(CT6HoursContractBlockedError) as captured:
        run_hours_clause(request)
    window = captured.value.result.candidate_windows[0]
    assert window.admissibility is CandidateAdmissibility.EXCLUDED
    assert HoursExclusionCode.OUTSIDE_TREATY_TERM in window.exclusion_codes
    assert window.affected_ids == ("BAD",)


def test_identical_hours_request_is_deterministic() -> None:
    first = run_hours_clause(valid_hours_request())
    second = run_hours_clause(valid_hours_request())
    assert first.ct4_result == second.ct4_result
    assert first.ct5_result == second.ct5_result
    assert first.ct4_identity == second.ct4_identity
    assert first.ct5_identity == second.ct5_identity


def test_hours_orchestrator_rejects_wrong_type() -> None:
    with pytest.raises(TypeError, match="HoursRunRequest"):
        run_hours_clause(object())  # type: ignore[arg-type]

