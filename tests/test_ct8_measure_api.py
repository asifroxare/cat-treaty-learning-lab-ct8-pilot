"""A capacity probe cannot broaden the frozen CT6 or invited pilot routes."""
import hashlib
import hmac
import json
import threading

from fastapi.testclient import TestClient
import pytest

from cat_treaty.ct8_measure_api import FIXTURES, create_measure_app
from deployment.probe import fixture_digest


SECRET = "test-only-secret-" + "x" * 48
HOST = "measure.example.org"
CONFIG = {"CT8_MEASURE_ENABLED": "true", "CT8_PILOT_ENABLED": "false",
          "CT8_MEASURE_HOST": HOST, "CT8_MEASURE_SECRET": SECRET}


def _signed(client, mode="catalogue", raw=None):
    raw = raw if raw is not None else (FIXTURES / f"approved-{mode}.json").read_bytes()
    nonce = client.get("/api/ct8-measure/v1/challenge").json()["nonce"]
    digest = hashlib.sha256((FIXTURES / f"approved-{mode}.json").read_bytes()).hexdigest()
    signature = hmac.new(SECRET.encode(), f"{nonce}\n{mode}\n{digest}".encode(), hashlib.sha256).hexdigest()
    return raw, {"Content-Type": "application/json", "X-CT8-Probe-Nonce": nonce,
                 "X-CT8-Probe-Body-SHA256": digest, "X-CT8-Probe-Signature": signature}


def test_probe_fails_closed_with_no_access_to_frozen_routes():
    for change in ({"CT8_MEASURE_ENABLED": "false"}, {"CT8_PILOT_ENABLED": "true"}, {"CT8_MEASURE_SECRET": "short"},
                   {"CT8_MEASURE_HOST": "localhost"}):
        with pytest.raises(ValueError):
            create_measure_app(config={**CONFIG, **change})
    with TestClient(create_measure_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        assert client.get("/health/ready").status_code == 200
        for path in ("/api/v1/runs/catalogue", "/api/pilot/v1/runs/catalogue", "/openapi.json", "/docs"):
            assert client.post(path, json={}).status_code == 404
        assert client.get("/api/ct8-measure/v1/challenge", headers={"host": "wrong.example.org"}).status_code == 404


def test_authentication_replay_and_fixture_bytes_are_enforced_before_compute(monkeypatch):
    invoked = []
    monkeypatch.setattr("cat_treaty.ct8_measure_api.run_isolated", lambda *a, **k: invoked.append(1))
    with TestClient(create_measure_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        route = "/api/ct8-measure/v1/runs/catalogue"
        raw, headers = _signed(client)
        assert client.post(route, content=raw, headers={**headers, "X-CT8-Probe-Signature": "0" * 64}).status_code == 401
        assert client.post(route, content=raw + b" ", headers=headers).status_code == 422
        assert client.post(route, content=raw, headers=headers).status_code == 401
        raw, headers = _signed(client)
        assert client.post(route, content=raw * 2, headers=headers).status_code == 413
        raw, headers = _signed(client)
        assert client.post(route, content=raw, headers={**headers, "X-CT8-Probe-Nonce": "invalid"}).status_code == 401
        assert invoked == []


def test_challenge_from_another_worker_lifecycle_cannot_authorize_a_run(monkeypatch):
    invoked = []
    monkeypatch.setattr("cat_treaty.ct8_measure_api.run_isolated", lambda *a, **k: invoked.append(1))
    with TestClient(create_measure_app(config=CONFIG), base_url=f"https://{HOST}") as before:
        raw, headers = _signed(before)
    with TestClient(create_measure_app(config=CONFIG), base_url=f"https://{HOST}") as after:
        response = after.post("/api/ct8-measure/v1/runs/catalogue", content=raw, headers=headers)
        assert response.status_code == 401
        assert invoked == []


@pytest.mark.parametrize("mode", ["catalogue", "hours-clause"])
def test_exact_fixture_runs_return_projected_complete_result(mode):
    with TestClient(create_measure_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        raw, headers = _signed(client, mode)
        result = client.post(f"/api/ct8-measure/v1/runs/{mode}", content=raw, headers=headers)
        assert result.status_code == 200, result.text[:150]
        assert result.json()["api"]["completion_status"] == "complete"
        manifest = json.loads((FIXTURES / "baseline-candidates.json").read_text())
        expected = next(item["response_sha256"] for item in manifest["fixtures"] if item["route"] == mode)
        assert fixture_digest(result.json(), [("api", "request_id")]) == expected


def test_single_slot_refuses_second_real_fixture(monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    def isolated(*args, **kwargs):
        entered.set()
        release.wait(timeout=4)
        raise RuntimeError("expected test stop")
    monkeypatch.setattr("cat_treaty.ct8_measure_api.run_isolated", isolated)
    app = create_measure_app(config=CONFIG)
    with TestClient(app, base_url=f"https://{HOST}") as first, TestClient(app, base_url=f"https://{HOST}") as second:
        raw, headers = _signed(first)
        t = threading.Thread(target=lambda: first.post("/api/ct8-measure/v1/runs/catalogue", content=raw, headers=headers))
        t.start()
        assert entered.wait(timeout=2)
        try:
            raw2, headers2 = _signed(second)
            denied = second.post("/api/ct8-measure/v1/runs/catalogue", content=raw2, headers=headers2)
            assert denied.status_code == 503 and denied.json()["code"] == "CT8_PROBE_BUSY"
        finally:
            release.set()
            t.join(timeout=3)
