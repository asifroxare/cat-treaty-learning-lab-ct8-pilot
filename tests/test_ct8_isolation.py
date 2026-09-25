"""Opt-in CT8 transport boundary; CT0-CT7 formulas are untouched."""
from fastapi.testclient import TestClient

from cat_treaty.api import create_app
from cat_treaty.runtime import RuntimeSettings
from tests.test_ct6_adapters import valid_hours_request
from tests.test_ct6_models import valid_request


def _post(app, route, request):
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/runs/" + route, json=request.model_dump(mode="json"))
    return response.status_code, response.json()


def test_opt_in_child_preserves_complete_catalogue_and_hours_response():
    normal = create_app(settings=RuntimeSettings())
    isolated = create_app(settings=RuntimeSettings(isolated_runs=True, isolation_deadline_seconds=30))
    for route, request in (("catalogue", valid_request()), ("hours-clause", valid_hours_request())):
        status, baseline = _post(normal, route, request)
        isolated_status, candidate = _post(isolated, route, request)
        assert status == isolated_status == 200
        assert baseline["api"].pop("request_id")
        assert candidate["api"].pop("request_id")
        assert candidate == baseline


def test_opt_in_child_preserves_blocked_hours_classification():
    request = valid_hours_request().model_dump(mode="json")
    request["input"]["terms"]["selected_election_method"] = "manual"
    request["input"]["terms"]["manual_candidate_set_id"] = "UNKNOWN"
    app = create_app(settings=RuntimeSettings(isolated_runs=True, isolation_deadline_seconds=30))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/runs/hours-clause", json=request)
    assert response.status_code == 422
    assert response.json()["code"] == "CT6_CONTRACT_BLOCKED"
    assert "post_capacity" not in response.json()


def test_isolation_settings_fail_closed():
    import pytest
    with pytest.raises(ValueError):
        RuntimeSettings(isolated_runs=True, isolation_deadline_seconds=0)
    with pytest.raises(ValueError):
        RuntimeSettings(isolated_runs=True, isolation_max_concurrency=0)


def test_expired_child_cannot_finish_or_emit_a_partial_result(tmp_path):
    import time
    import pytest
    from cat_treaty.ct8_executor import CT8ExecutionTimeout, _run_process
    from tests.ct8_child_fixtures import delayed_marker

    started = tmp_path / "started.txt"
    completed = tmp_path / "completed.txt"
    with pytest.raises(CT8ExecutionTimeout):
        _run_process(delayed_marker, (str(started), str(completed)), deadline_seconds=1.5)
    assert started.is_file(), "child must actually start before the deadline test"
    time.sleep(1.2)
    assert not completed.exists(), "a timed-out child must not keep calculating"
