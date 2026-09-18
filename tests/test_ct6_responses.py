"""Authoritative CT6 full/summary response projection tests."""

import json

from cat_treaty.ct4_models import CandidateAdmissibility, HoursElectionMethod
from cat_treaty.ct6_hours import run_hours_clause
from cat_treaty.ct6_models import HoursComponentDTO, ResponseDetail
from cat_treaty.ct6_orchestration import run_catalogue
from cat_treaty.ct6_responses import project_catalogue_success, project_hours_success
from tests.test_ct6_adapters import valid_hours_request
from tests.test_ct6_models import valid_request


def test_full_catalogue_response_uses_exact_frozen_authoritative_names() -> None:
    response = project_catalogue_success(
        run_catalogue(valid_request()), request_id="request-1"
    )
    pre = response.pre_capacity.occurrence_rows[0]  # type: ignore[index]
    post = response.post_capacity.occurrence_rows[0]  # type: ignore[index]
    assert pre.gross_contractual_recovery_pre_annual_capacity == 20_000_000.0
    assert post.gross_contractual_recovery_pre_annual_capacity == 20_000_000.0
    assert post.gross_contractual_recovery == 20_000_000.0
    assert post.reinstatement_premium_payable > 0.0
    assert post.net_cash_settlement == 20_000_000.0
    assert "recovery" not in type(post).model_fields
    assert "net" not in type(post).model_fields


def test_summary_omits_rows_and_curve_samples_but_preserves_hashes_and_audit_evidence() -> None:
    full_run = run_catalogue(valid_request())
    summary_request = valid_request().model_copy(update={"response_detail": ResponseDetail.SUMMARY})
    summary_run = run_catalogue(summary_request)
    full = project_catalogue_success(full_run, request_id="full")
    summary = project_catalogue_success(summary_run, request_id="summary")

    assert summary.pre_capacity.occurrence_rows is None
    assert summary.post_capacity.occurrence_rows is None
    assert summary.pre_capacity.annual_rows
    assert summary.post_capacity.annual_rows
    assert summary.learning.reconciliations
    assert summary.learning.facts
    assert summary.identity == full.identity
    serialized = summary.model_dump(mode="json")
    tail_text = json.dumps(serialized["pre_capacity"]["tail_analytics"])
    assert "oep_sample" not in tail_text
    assert "aep_curve" not in tail_text
    full_tail_text = json.dumps(full.model_dump(mode="json")["pre_capacity"]["tail_analytics"])
    assert "oep_sample" in full_tail_text
    assert "aep_curve" in full_tail_text


def test_summary_retains_all_cumulative_credibility_warnings() -> None:
    summary_request = valid_request().model_copy(update={"response_detail": ResponseDetail.SUMMARY})
    response = project_catalogue_success(run_catalogue(summary_request), request_id="warnings")
    assert response.warnings
    codes = {item.code for item in response.warnings}
    assert "limited_tail_credibility" in codes
    assert "severe_tail_credibility_warning" in codes
    assert "return_period_exceeds_sample" in codes


def test_hours_summary_retains_election_and_invalid_split_evidence() -> None:
    components = (
        HoursComponentDTO(
            component_id="C1", subject_loss=25_000_000.0, timestamp=100.0,
            peril="wind", region="R1", causal_event_id="storm", source_reference="source",
        ),
        HoursComponentDTO(
            component_id="C2", subject_loss=25_000_000.0, timestamp=110.0,
            peril="wind", region="R1", causal_event_id="storm", source_reference="source",
        ),
    )
    request = valid_hours_request(
        components=components,
        selected_method=HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
    ).model_copy(update={"response_detail": ResponseDetail.SUMMARY})
    response = project_hours_success(run_hours_clause(request), request_id="hours")
    assert response.pre_capacity.occurrence_rows is None
    assert response.post_capacity.occurrence_rows is None
    assert response.pre_capacity.selected_candidate_set_id == "SET-001"
    invalid = next(
        item for item in response.pre_capacity.candidate_sets
        if item.candidate_set_id == "SET-003"
    )
    assert invalid.admissibility == CandidateAdmissibility.EXCLUDED.value
    assert "duplicate_component" in invalid.exclusion_codes
    assert "overlapping_windows" in invalid.exclusion_codes
    assert response.identity.ct4_input_hash
    assert response.identity.ct5_result_hash


def test_learning_facts_and_reconciliations_are_structured_and_complete() -> None:
    response = project_catalogue_success(
        run_catalogue(valid_request()), request_id="learning"
    )
    categories = {item.category for item in response.learning.facts}
    scopes = {item.scope for item in response.learning.reconciliations}
    assert {"loss_stage", "occurrence_program", "annual_capacity", "reinstatement", "settlement"} <= categories
    assert {"ct2", "ct3", "ct4_annual", "ct5_occurrence", "ct5_annual"} <= scopes
    assert all(item.passed for item in response.learning.reconciliations)


def test_success_response_is_finite_json_and_request_id_does_not_change_identity() -> None:
    run = run_catalogue(valid_request())
    first = project_catalogue_success(run, request_id="one")
    second = project_catalogue_success(run, request_id="two")
    assert first.identity == second.identity
    assert first.api.request_id != second.api.request_id
    payload = first.model_dump_json()
    assert "NaN" not in payload
    assert "Infinity" not in payload

