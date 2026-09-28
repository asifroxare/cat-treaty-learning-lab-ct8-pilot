"""Security boundary and exact CT7 outcomes for the separate no-card candidate."""
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import threading
import time

from fastapi.testclient import TestClient
import pytest

from cat_treaty.ct8_measure_api import FIXTURES
from cat_treaty.pilot_nocard_api import create_nocard_app
from deployment.probe import fixture_digest

HOST = "cat-treaty-learning-lab-ct8-pilot.onrender.com"
PUBLIC = "ct8-cat.asif-rox.workers.dev"
KEY = __import__("base64").urlsafe_b64encode(hashlib.sha256(b"review-only-assertion-key").digest()).decode().rstrip("=")
CONFIG = {
    "CT8_NOCARD_ENABLED": "true", "CT8_PILOT_ENABLED": "false", "CT8_MEASURE_ENABLED": "false",
    "CT8_NOCARD_API_HOST": HOST, "CT8_NOCARD_PUBLIC_HOST": PUBLIC,
    "CT8_NOCARD_ASSERTION_KEY": KEY, "CT8_NOCARD_ID_ALLOWLIST": "12345",
    "CT8_NOCARD_ASSERTION_KEY_ID": "k1",
    "CT8_NOCARD_LIMITS_JSON": json.dumps({"max_body_bytes": 4096, "max_trials": 1,
        "max_occurrences": 1, "max_layers": 1, "max_hours_components": 2,
        "max_requests_per_minute": 6, "allow_full_detail": True}),
    "CT8_NOCARD_DEADLINE_SECONDS": "30", "CT8_NOCARD_RESULT_BYTES": str(16 * 1024 * 1024),
}


def signed(path, raw=b"", *, method="POST", uid="12345", timestamp=None, nonce=None,
           key=KEY, digest=None, kid="k1", boot=None):
    digest = digest or hashlib.sha256(raw).hexdigest()
    stamp = str(timestamp or int(time.time()))
    nonce = nonce or secrets.token_urlsafe(24)
    boot = boot if boot is not None else signed.boot
    message = "\n".join(("ct8.1", kid, method, path, HOST, PUBLIC, uid,
                         digest, stamp, nonce, boot)).encode("ascii")
    signature = hmac.new(key.encode("ascii"), message, hashlib.sha256).hexdigest()
    return {"X-CT8-Assertion-Key": kid, "X-CT8-Assertion-ID": uid,
        "X-CT8-Assertion-Nonce": nonce, "X-CT8-Assertion-Time": stamp,
        "X-CT8-Assertion-Boot": boot,
        "X-CT8-Assertion-Digest": digest, "X-CT8-Assertion-Signature": signature,
        "Content-Type": "application/json"}


def boot(client):
    signed.boot = client.get("/health/ready").json()["boot"]


def test_fail_closed_and_no_other_api_or_docs():
    for change in ({"CT8_NOCARD_ENABLED": "false"}, {"CT8_PILOT_ENABLED": "true"},
                   {"CT8_MEASURE_ENABLED": "true"}, {"CT8_NOCARD_ASSERTION_KEY": "short"},
                   {"CT8_NOCARD_ASSERTION_KEY": "a" * 64},
                   {"WEB_CONCURRENCY": "2"},
                   {"CT8_NOCARD_ID_ALLOWLIST": "someone@example.com"},
                   {"CT8_NOCARD_RESULT_BYTES": str(128 * 1024 * 1024)}):
        with pytest.raises(ValueError):
            create_nocard_app(config={**CONFIG, **change})
    with TestClient(create_nocard_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        for route in ("/api/v1/runs/catalogue", "/openapi.json", "/docs", "/auth/start"):
            assert client.get(route).status_code == 404
        assert client.get("/health/ready").json()["mode"] == "private-review"


def test_no_unsigned_spoofed_or_replayed_work_reaches_child(monkeypatch):
    invoked = []
    monkeypatch.setattr("cat_treaty.pilot_nocard_api.run_isolated", lambda *a, **k: invoked.append(1))
    path = "/api/pilot/v1/runs/catalogue"
    raw = (FIXTURES / "approved-catalogue.json").read_bytes()
    with TestClient(create_nocard_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        boot(client)
        assert client.post(path, content=raw, headers={"Cookie": "__Host-CT8PilotSession=fake"}).status_code == 401
        assert client.post(path, content=raw, headers=signed(path, raw, key="not-the-worker-key")).status_code == 401
        assert client.post(path, content=raw, headers=signed(path, raw, uid="98765")).status_code == 401
        assert client.post(path, content=raw, headers=signed(path, raw, timestamp=int(time.time())-60)).status_code == 401
        same = signed(path, raw)
        assert client.post(path, content=raw+b" ", headers=same).status_code == 401
        assert client.post(path, content=raw, headers=same).status_code == 401
        assert client.post(path, content=raw, headers=signed(path, raw),
                           follow_redirects=False).status_code == 500  # mocked child has no result
        assert len(invoked) == 1


@pytest.mark.parametrize("mode", ["catalogue", "hours-clause"])
def test_signed_real_fixture_preserves_full_ct7_golden(mode):
    raw = (FIXTURES / f"approved-{mode}.json").read_bytes()
    path = f"/api/pilot/v1/runs/{mode}"
    with TestClient(create_nocard_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        boot(client)
        response = client.post(path, content=raw, headers=signed(path, raw))
        assert response.status_code == 200, response.text[:250]
        manifest = json.loads((FIXTURES / "baseline-candidates.json").read_text())
        expected = next(row["response_sha256"] for row in manifest["fixtures"] if row["route"] == mode)
        assert fixture_digest(response.json(), [("api", "request_id")]) == expected


def test_one_slot_rejects_second_signed_run_without_spawning(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    def isolated(*args, **kwargs):
        entered.set()
        release.wait(timeout=5)
        raise RuntimeError("test stop")
    monkeypatch.setattr("cat_treaty.pilot_nocard_api.run_isolated", isolated)
    path = "/api/pilot/v1/runs/catalogue"
    raw = (FIXTURES / "approved-catalogue.json").read_bytes()
    app = create_nocard_app(config=CONFIG)
    with TestClient(app, base_url=f"https://{HOST}") as first, TestClient(app, base_url=f"https://{HOST}") as second:
        boot(first)
        worker = threading.Thread(target=lambda: first.post(path, content=raw, headers=signed(path, raw)))
        worker.start()
        assert entered.wait(3)
        try:
            result = second.post(path, content=raw, headers=signed(path, raw))
            assert result.status_code == 503 and result.json()["code"] == "CT8_PILOT_BUSY"
        finally:
            release.set()
            worker.join(timeout=5)


@pytest.mark.parametrize("mode", ["catalogue", "hours-clause"])
def test_real_worker_signed_fixture_passes_python_boundary(mode):
    bridge = FIXTURES.parent.parent / "nocard_bridge_fixture.mjs"
    manifest = json.loads((FIXTURES / "baseline-candidates.json").read_text())
    expected = next(row["response_sha256"] for row in manifest["fixtures"] if row["route"] == mode)
    with TestClient(create_nocard_app(config=CONFIG), base_url=f"https://{HOST}") as client:
        boot(client)
        result = subprocess.run(["node", str(bridge), mode], check=True, capture_output=True,
                                text=True, env={**os.environ, "CT8_TEST_BOOT": signed.boot})
        forwarded = json.loads(result.stdout)
        response = client.request(forwarded["method"], forwarded["url"],
                                  content=forwarded["body"].encode(), headers=forwarded["headers"])
        assert response.status_code == 200, response.text[:200]
        assert fixture_digest(response.json(), [("api", "request_id")]) == expected


def test_replay_across_restart_and_previous_key_rotation():
    path = "/api/pilot/v1/capabilities"
    older = __import__("base64").urlsafe_b64encode(hashlib.sha256(b"old-rotation-test").digest()).decode().rstrip("=")
    config = {**CONFIG, "CT8_NOCARD_ASSERTION_PREVIOUS": older,
              "CT8_NOCARD_ASSERTION_PREVIOUS_ID": "k0"}
    with TestClient(create_nocard_app(config=config), base_url=f"https://{HOST}") as first:
        boot(first)
        original = signed(path, method="GET", key=older, kid="k0")
        assert first.get(path, headers=original).status_code == 200
        assert first.get(path, headers=original).status_code == 401
    with TestClient(create_nocard_app(config=config), base_url=f"https://{HOST}") as second:
        boot(second)
        assert second.get(path, headers=original).status_code == 401
        assert second.get(path, headers=signed(path, method="GET")).status_code == 200
