"""CT6 HTTP routes, limits, errors, health and OpenAPI contract tests."""

from fastapi.testclient import TestClient

import cat_treaty.api as api_module
from cat_treaty.api import MAX_REQUEST_BYTES, create_app
from cat_treaty.ct6_models import CT6_API_VERSION, CT6_SCHEMA_VERSION
from tests.test_ct6_adapters import valid_hours_request
from tests.test_ct6_models import valid_request


def client() -> TestClient:
    return TestClient(create_app(), raise_server_exceptions=False)


def catalogue_payload() -> dict:
    return valid_request().model_dump(mode="json")


def hours_payload() -> dict:
    return valid_hours_request().model_dump(mode="json")


def test_root_liveness_readiness_and_capabilities_do_not_run_simulation(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "run_catalogue", lambda request: (_ for _ in ()).throw(AssertionError("must not run")))
    with client() as http:
        assert http.get("/").json()["product"] == "cat-treaty-learning-lab"
        assert http.get("/health/live").json() == {"status": "live", "api_version": CT6_API_VERSION}
        ready = http.get("/health/ready")
        assert ready.status_code == 200
        assert all(ready.json()["checks"].values())
        capabilities = http.get("/api/v1/capabilities").json()
    assert capabilities["versions"]["ct6_schema"] == CT6_SCHEMA_VERSION
    assert capabilities["limits"]["request_body_bytes"] == MAX_REQUEST_BYTES
    assert capabilities["limits"]["full_detail_occurrence_rows"] == 25_000
    assert set(capabilities["run_modes"]) == {"catalogue", "hours_clause"}


def test_catalogue_and_hours_routes_return_authoritative_success() -> None:
    with client() as http:
        catalogue = http.post(
            "/api/v1/runs/catalogue",
            json=catalogue_payload(),
            headers={"X-Request-ID": "audit-request-1"},
        )
        hours = http.post("/api/v1/runs/hours-clause", json=hours_payload())
    assert catalogue.status_code == 200, catalogue.text
    assert catalogue.headers["X-Request-ID"] == "audit-request-1"
    assert catalogue.json()["api"]["request_id"] == "audit-request-1"
    assert catalogue.json()["api"]["run_mode"] == "catalogue"
    assert hours.status_code == 200, hours.text
    assert hours.json()["api"]["run_mode"] == "hours_clause"
    assert hours.json()["pre_capacity"]["selected_candidate_set_id"]


def test_malformed_json_and_media_type_are_400_with_static_messages() -> None:
    with client() as http:
        malformed = http.post(
            "/api/v1/runs/catalogue",
            content=b'{"api_schema_version":',
            headers={"content-type": "application/json"},
        )
        media = http.post(
            "/api/v1/runs/catalogue",
            content=b"anything",
            headers={"content-type": "text/plain"},
        )
    for response in (malformed, media):
        assert response.status_code == 400
        assert response.json()["code"] == "CT6_MALFORMED_JSON"
        assert "anything" not in response.text
        assert "traceback" not in response.text.lower()


def test_unsupported_string_version_precedes_all_other_schema_errors() -> None:
    payload = catalogue_payload()
    payload["api_schema_version"] = "ct999.0"
    payload["unknown_field"] = "private-client-value"
    payload["input"]["simulation"]["trial_count"] = "wrong"
    with client() as http:
        response = http.post("/api/v1/runs/catalogue", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "CT6_VERSION_CONFLICT"
    assert response.json()["errors"] == []
    assert "private-client-value" not in response.text


def test_missing_or_wrong_typed_version_and_unknown_fields_are_422_schema_errors() -> None:
    cases = []
    missing = catalogue_payload()
    missing.pop("api_schema_version")
    cases.append(missing)
    wrong_type = catalogue_payload()
    wrong_type["api_schema_version"] = 6
    cases.append(wrong_type)
    unknown = catalogue_payload()
    unknown["not_in_contract"] = True
    cases.append(unknown)
    with client() as http:
        responses = [http.post("/api/v1/runs/catalogue", json=item) for item in cases]
    for response in responses:
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "CT6_SCHEMA_VALIDATION"
        assert body["errors"]
        assert body["errors"] == sorted(body["errors"], key=lambda item: (item["path"], item["code"]))
    assert responses[0].json()["errors"][0]["path"] == "api_schema_version"


def test_hours_invalid_manual_election_is_contract_blocked() -> None:
    payload = hours_payload()
    payload["input"]["terms"]["selected_election_method"] = "manual"
    payload["input"]["terms"]["manual_candidate_set_id"] = "UNKNOWN"
    with client() as http:
        response = http.post("/api/v1/runs/hours-clause", json=payload)
    assert response.status_code == 422
    assert response.json()["code"] == "CT6_CONTRACT_BLOCKED"
    assert "UNKNOWN" not in response.text


def test_full_detail_row_cap_is_413_and_never_silently_downgrades(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "MAX_FULL_DETAIL_ROWS", 0)
    with client() as http:
        response = http.post("/api/v1/runs/catalogue", json=catalogue_payload())
    assert response.status_code == 413
    assert response.json()["code"] == "CT6_REQUEST_TOO_LARGE"


def test_unexpected_failures_are_sanitized_500(monkeypatch) -> None:
    secret = "C:/secret/local/path credential=do-not-leak"

    def fail(request):
        raise RuntimeError(secret)

    monkeypatch.setattr(api_module, "run_catalogue", fail)
    with client() as http:
        response = http.post("/api/v1/runs/catalogue", json=catalogue_payload())
    assert response.status_code == 500
    assert response.json()["code"] == "CT6_INTERNAL_ERROR"
    assert secret not in response.text
    assert "traceback" not in response.text.lower()


def test_invalid_incoming_request_id_is_replaced() -> None:
    with client() as http:
        response = http.get("/health/live", headers={"X-Request-ID": "contains spaces"})
    generated = response.headers["X-Request-ID"]
    assert generated != "contains spaces"
    assert len(generated) == 36


def test_openapi_freezes_routes_models_and_problem_responses() -> None:
    schema = create_app().openapi()
    expected_paths = {
        "/", "/health/live", "/health/ready", "/api/v1/capabilities",
        "/api/v1/runs/catalogue", "/api/v1/runs/hours-clause",
    }
    assert expected_paths <= set(schema["paths"])
    catalogue = schema["paths"]["/api/v1/runs/catalogue"]["post"]
    hours = schema["paths"]["/api/v1/runs/hours-clause"]["post"]
    assert catalogue["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/CatalogueRunRequest")
    assert hours["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("/HoursRunRequest")
    assert catalogue["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/CT6SuccessResponse")
    assert set(("400", "409", "413", "422", "500")) <= set(catalogue["responses"])
    assert "CT6ProblemResponse" in schema["components"]["schemas"]
