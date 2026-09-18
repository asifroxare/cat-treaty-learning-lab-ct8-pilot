"""Permanent consolidated CT6 G69--G83 HTTP acceptance."""

from fastapi.testclient import TestClient

import cat_treaty.api as api_module
from cat_treaty.api import create_app
from cat_treaty.ct2_models import LossComponentCategory
from cat_treaty.ct6_models import ResponseDetail
from cat_treaty.golden_cases import CT6_GOLDEN_CASE_EVIDENCE
from cat_treaty.models import SettlementMode
from tests.test_ct6_adapters import valid_hours_request
from tests.test_ct6_models import valid_request


def _client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


def _catalogue(request=None) -> dict:
    return (request or valid_request()).model_dump(mode="json")


def _hours(request=None) -> dict:
    return (request or valid_hours_request()).model_dump(mode="json")


def test_g69_liveness_and_readiness_do_not_execute_simulation(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "run_catalogue", lambda request: (_ for _ in ()).throw(AssertionError))
    with _client() as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200


def test_g70_catalogue_end_to_end_returns_both_capacity_views() -> None:
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue())
    body = response.json()
    assert response.status_code == 200
    assert body["pre_capacity"]["occurrence_rows"][0]["gross_contractual_recovery_pre_annual_capacity"] == 20_000_000.0
    assert body["post_capacity"]["occurrence_rows"][0]["gross_contractual_recovery"] == 20_000_000.0


def test_g71_hours_clause_end_to_end_preserves_election_evidence() -> None:
    with _client() as client:
        response = client.post("/api/v1/runs/hours-clause", json=_hours())
    body = response.json()
    assert response.status_code == 200
    assert body["pre_capacity"]["selected_candidate_set_id"] in body["pre_capacity"]["valid_candidate_set_ids"]
    assert body["post_capacity"]["occurrence_rows"]


def test_g72_malformed_json_is_sanitized_400() -> None:
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", content=b'{"bad":', headers={"content-type": "application/json"})
    assert response.status_code == 400
    assert response.json()["code"] == "CT6_MALFORMED_JSON"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert "traceback" not in response.text.lower()


def test_g73_numeric_string_and_unknown_field_are_rejected() -> None:
    payload = _catalogue()
    payload["input"]["simulation"]["trial_count"] = "1"
    payload["unknown"] = True
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "CT6_SCHEMA_VALIDATION"
    assert {item["path"] for item in response.json()["errors"]} == {"input.simulation.trial_count", "unknown"}


def test_g74_invalid_election_blocks_without_downstream_payload() -> None:
    payload = _hours()
    payload["input"]["terms"]["selected_election_method"] = "manual"
    payload["input"]["terms"]["manual_candidate_set_id"] = "UNKNOWN"
    with _client() as client:
        response = client.post("/api/v1/runs/hours-clause", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "CT6_CONTRACT_BLOCKED"
    assert "post_capacity" not in response.json()


def test_g75_deterministic_repeat_preserves_results_and_hashes() -> None:
    with _client() as client:
        first = client.post("/api/v1/runs/catalogue", json=_catalogue()).json()
        second = client.post("/api/v1/runs/catalogue", json=_catalogue()).json()
    assert first["identity"] == second["identity"]
    assert first["pre_capacity"] == second["pre_capacity"]
    assert first["post_capacity"] == second["post_capacity"]


def test_g76_permitted_component_permutation_preserves_hashes() -> None:
    request = valid_request()
    occurrence = request.input.trials[0].occurrences[0]
    extra = occurrence.loss_basis.components[0].model_copy(update={"component_id": "I2", "label": "other"})
    components = occurrence.loss_basis.components + (extra,)

    def with_components(values):
        changed_occurrence = occurrence.model_copy(update={"loss_basis": occurrence.loss_basis.model_copy(update={"components": values})})
        trial = request.input.trials[0].model_copy(update={"occurrences": (changed_occurrence,)})
        return request.model_copy(update={"input": request.input.model_copy(update={"trials": (trial,)})})

    with _client() as client:
        first = client.post("/api/v1/runs/catalogue", json=_catalogue(with_components(components))).json()
        second = client.post("/api/v1/runs/catalogue", json=_catalogue(with_components(tuple(reversed(components))))).json()
    assert first["identity"] == second["identity"]


def test_g77_full_and_summary_preserve_hashes_warnings_and_election() -> None:
    full = valid_hours_request()
    summary = full.model_copy(update={"response_detail": ResponseDetail.SUMMARY})
    with _client() as client:
        full_body = client.post("/api/v1/runs/hours-clause", json=_hours(full)).json()
        summary_body = client.post("/api/v1/runs/hours-clause", json=_hours(summary)).json()
    assert full_body["identity"] == summary_body["identity"]
    assert full_body["warnings"] == summary_body["warnings"]
    assert full_body["pre_capacity"]["candidate_sets"] == summary_body["pre_capacity"]["candidate_sets"]
    assert summary_body["pre_capacity"]["occurrence_rows"] is None


def test_g78_negative_cash_settlement_survives_json() -> None:
    request = valid_request()
    terms = request.input.treaty_terms.layer_terms[0].model_copy(
        update={"original_layer_premium": 100_000_000.0, "settlement_mode": SettlementMode.DEDUCTED_FROM_SETTLEMENT}
    )
    changed = request.model_copy(update={"input": request.input.model_copy(update={"treaty_terms": request.input.treaty_terms.model_copy(update={"layer_terms": (terms,)})})})
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue(changed))
    body = response.json()
    assert response.status_code == 200, response.text
    assert body["post_capacity"]["occurrence_rows"][0]["net_cash_settlement"] < 0
    assert body["post_capacity"]["annual_rows"][0]["net_cash_settlement"] < 0


def test_g79_zero_capacity_is_null_with_explicit_status() -> None:
    request = valid_request()
    layer = request.input.program.layers[0].model_copy(update={"ceded_share": 0.0})
    changed = request.model_copy(update={"input": request.input.model_copy(update={"program": request.input.program.model_copy(update={"layers": (layer,)})})})
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue(changed))
    summary = response.json()["post_capacity"]["annual_rows"][0]["layer_summaries"][0]
    assert response.status_code == 200
    assert summary["realized_capacity_utilization"] is None
    assert summary["realized_capacity_utilization_status"] == "not_applicable_zero_capacity"


def test_g80_cumulative_credibility_warnings_remain_http_200() -> None:
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue())
    codes = {item["code"] for item in response.json()["warnings"]}
    assert response.status_code == 200
    assert {"limited_tail_credibility", "severe_tail_credibility_warning", "return_period_exceeds_sample"} <= codes


def test_g81_oversized_full_response_is_rejected_without_downgrade(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "MAX_FULL_DETAIL_ROWS", 0)
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue())
    assert response.status_code == 413
    assert response.json()["code"] == "CT6_REQUEST_TOO_LARGE"
    assert "post_capacity" not in response.json()


def test_g82_internal_failure_is_sanitized_without_partial_payload(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "run_catalogue", lambda request: (_ for _ in ()).throw(RuntimeError("secret path")))
    with _client() as client:
        response = client.post("/api/v1/runs/catalogue", json=_catalogue())
    assert response.status_code == 500
    assert response.json()["code"] == "CT6_INTERNAL_ERROR"
    assert "secret path" not in response.text
    assert "post_capacity" not in response.json()


def test_g83_version_conflict_precedence_is_frozen() -> None:
    unsupported = _catalogue()
    unsupported["api_schema_version"] = "ct99.0"
    unsupported["unknown"] = True
    missing = _catalogue()
    missing.pop("api_schema_version")
    wrong_type = _catalogue()
    wrong_type["api_schema_version"] = 6
    with _client() as client:
        responses = [client.post("/api/v1/runs/catalogue", json=item) for item in (unsupported, missing, wrong_type)]
    assert [item.status_code for item in responses] == [409, 422, 422]
    assert [item.json()["code"] for item in responses] == ["CT6_VERSION_CONFLICT", "CT6_SCHEMA_VALIDATION", "CT6_SCHEMA_VALIDATION"]


def test_g69_g83_trace_register_is_complete_and_unique() -> None:
    ids = tuple(item.case_id for item in CT6_GOLDEN_CASE_EVIDENCE)
    assert ids == tuple(f"G{number}" for number in range(69, 84))
    assert len({item.test_node_id for item in CT6_GOLDEN_CASE_EVIDENCE}) == 15
