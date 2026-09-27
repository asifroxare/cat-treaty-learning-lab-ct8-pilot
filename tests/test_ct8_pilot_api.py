"""Separate pilot transport must not expose CT6 reference endpoints."""
import json

import pytest
from fastapi.testclient import TestClient

from cat_treaty.api import create_app
from cat_treaty.pilot_api import create_pilot_app
from tests.test_ct6_models import valid_request


HOST = "pilot-api.example.org"
PROOF = "a-secret-origin-proof-with-at-least-thirty-two-characters"
PATH = "/api/pilot/v1/runs/catalogue"


class ReviewerIdentity:
    def verify(self, token):
        if token != "signed-review-token":
            from cat_treaty.pilot_auth import PilotUnauthorized
            raise PilotUnauthorized("missing identity")
        return "tester@example.org"


def config():
    return {
        "CT8_PILOT_ENABLED": "true", "CT8_PILOT_API_HOST": HOST,
        "CT8_PILOT_UI_ORIGIN": "https://pilot-ui.example.org",
        "CT8_PILOT_ORIGIN_SECRET": PROOF, "CT8_PILOT_DEADLINE_SECONDS": "30",
        "CT8_PILOT_LIMITS_JSON": json.dumps({
            "max_body_bytes": 16384, "max_trials": 1, "max_occurrences": 1,
            "max_layers": 1, "max_hours_components": 2,
            "max_requests_per_minute": 5, "allow_full_detail": True,
        }),
    }


def headers(*, proof=PROOF, token="signed-review-token", host=HOST):
    return {"Host": host, "X-CT8-Pilot-Origin": proof,
            "Cf-Access-Jwt-Assertion": token, "Content-Type": "application/json"}


def test_pilot_fails_closed_when_unconfigured():
    with pytest.raises(ValueError, match="disabled"):
        create_pilot_app(config={})
    with pytest.raises(ValueError, match="limits"):
        create_pilot_app(config={key: value for key, value in config().items()
                                 if key != "CT8_PILOT_LIMITS_JSON"}, verifier=ReviewerIdentity())


def test_pilot_has_no_ct6_or_documentation_routes_and_denies_direct_origin():
    with TestClient(create_pilot_app(config=config(), verifier=ReviewerIdentity())) as client:
        raw = valid_request().model_dump(mode="json")
        assert client.post("/api/v1/runs/catalogue", json=raw, headers=headers()).status_code == 404
        assert client.get("/openapi.json", headers=headers()).status_code == 404
        assert client.post(PATH, json=raw, headers=headers(proof="")).status_code == 401
        assert client.post(PATH, json=raw, headers=headers(token="")).status_code == 401
        assert client.post(PATH, json=raw, headers=headers(host="onrender.com")).status_code == 404


def test_pilot_rejects_oversize_before_calculation(monkeypatch):
    import cat_treaty.pilot_api as pilot
    monkeypatch.setattr(pilot, "run_isolated", lambda *a, **k: pytest.fail("rejected input calculated"))
    with TestClient(create_pilot_app(config=config(), verifier=ReviewerIdentity())) as client:
        raw = valid_request().model_dump(mode="json")
        raw["input"]["trials"].append(raw["input"]["trials"][0])
        result = client.post(PATH, json=raw, headers=headers())
        assert result.status_code == 413 and result.json()["code"] == "CT8_PILOT_LIMIT"
        large = client.post(PATH, content=b"x" * 16385, headers=headers())
        assert large.status_code == 413 and large.json()["code"] == "CT8_PILOT_LIMIT"


def test_pilot_small_authoritative_result_matches_frozen_ct6():
    raw = valid_request().model_dump(mode="json")
    with TestClient(create_app()) as ct6, TestClient(create_pilot_app(
            config=config(), verifier=ReviewerIdentity())) as pilot:
        baseline = ct6.post("/api/v1/runs/catalogue", json=raw)
        candidate = pilot.post(PATH, json=raw, headers=headers())
    assert baseline.status_code == candidate.status_code == 200
    expected, actual = baseline.json(), candidate.json()
    expected["api"].pop("request_id")
    actual["api"].pop("request_id")
    assert actual == expected


def test_pilot_busy_refuses_before_queueing_another_child(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import cat_treaty.pilot_api as pilot_module

    started, release = threading.Event(), threading.Event()
    calls = []
    def held_run(mode, request, *, deadline_seconds):
        calls.append(mode)
        started.set()
        assert release.wait(5)
        from cat_treaty.ct6_orchestration import run_catalogue
        return run_catalogue(request)
    monkeypatch.setattr(pilot_module, "run_isolated", held_run)
    app = create_pilot_app(config=config(), verifier=ReviewerIdentity())
    raw = valid_request().model_dump(mode="json")
    with ThreadPoolExecutor(max_workers=1) as executor:
        first = executor.submit(lambda: TestClient(app).post(PATH, json=raw, headers=headers()))
        assert started.wait(5)
        try:
            with TestClient(app) as client:
                health = client.get("/health/ready", headers={"Host": HOST})
                second = client.post(PATH, json=raw, headers=headers())
            assert health.status_code == 200 and health.json()["status"] == "ready"
            assert second.status_code == 503 and second.json()["code"] == "CT8_PILOT_BUSY"
            assert calls == ["catalogue"]
        finally:
            release.set()
        assert first.result(timeout=5).status_code == 200


def test_pilot_timeout_releases_slot_without_returning_partial_evidence(monkeypatch):
    import cat_treaty.pilot_api as pilot_module
    from cat_treaty.ct8_executor import CT8ExecutionTimeout
    from cat_treaty.ct6_orchestration import run_catalogue

    calls = []
    def once_timeout(mode, body, *, deadline_seconds):
        calls.append(mode)
        if len(calls) == 1:
            raise CT8ExecutionTimeout("synthetic internal deadline")
        return run_catalogue(body)
    monkeypatch.setattr(pilot_module, "run_isolated", once_timeout)
    app = create_pilot_app(config=config(), verifier=ReviewerIdentity())
    raw = valid_request().model_dump(mode="json")
    with TestClient(app) as client:
        failed = client.post(PATH, json=raw, headers=headers())
        recovered = client.post(PATH, json=raw, headers=headers())
    assert failed.status_code == 500
    assert failed.json()["code"] == "CT8_PILOT_FAILURE"
    assert "synthetic internal deadline" not in failed.text
    assert "post_capacity" not in failed.text
    assert recovered.status_code == 200
    assert calls == ["catalogue", "catalogue"]
