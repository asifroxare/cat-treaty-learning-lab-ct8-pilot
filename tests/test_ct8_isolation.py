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


def test_opt_in_busy_slot_returns_structured_500_without_changing_accepted_result(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    import cat_treaty.api as api_module

    entered = threading.Event()
    release = threading.Event()
    def held_run(mode, body, *, deadline_seconds):
        entered.set()
        assert release.wait(5)
        return api_module.run_catalogue(body)
    monkeypatch.setattr(api_module, "run_isolated", held_run)
    app = create_app(settings=RuntimeSettings(isolated_runs=True, isolation_max_concurrency=1))
    baseline_status, baseline = _post(create_app(settings=RuntimeSettings()), "catalogue", valid_request())
    with ThreadPoolExecutor(max_workers=1) as executor:
        accepted = executor.submit(_post, app, "catalogue", valid_request())
        assert entered.wait(5), "first request must acquire the only slot"
        try:
            busy_status, busy = _post(app, "catalogue", valid_request())
        finally:
            release.set()
        completed_status, completed = accepted.result(timeout=5)
    assert busy_status == 500 and busy["code"] == "CT6_INTERNAL_ERROR"
    assert "post_capacity" not in busy
    assert baseline_status == completed_status == 200
    assert baseline["api"].pop("request_id")
    assert completed["api"].pop("request_id")
    assert completed == baseline


def test_opt_in_deadline_failure_returns_structured_500_without_partial_result(monkeypatch):
    import cat_treaty.api as api_module
    from cat_treaty.ct8_executor import CT8ExecutionTimeout

    def expired(_mode, _body, *, deadline_seconds):
        raise CT8ExecutionTimeout("synthetic deadline")
    monkeypatch.setattr(api_module, "run_isolated", expired)
    app = create_app(settings=RuntimeSettings(isolated_runs=True))
    status, body = _post(app, "catalogue", valid_request())
    assert status == 500 and body["code"] == "CT6_INTERNAL_ERROR"
    assert "post_capacity" not in body
    assert "synthetic deadline" not in str(body)


def test_hard_killed_parent_does_not_leave_calculation_child_running(tmp_path):
    from pathlib import Path
    import subprocess
    import sys
    import time

    started = tmp_path / "orphan-started.txt"
    completed = tmp_path / "orphan-completed.txt"
    parent = subprocess.Popen([sys.executable, "-m", "tests.ct8_orphan_parent",
        str(started), str(completed)], cwd=str(Path(__file__).resolve().parents[1]))
    assert parent.wait(timeout=15) == 7
    assert started.is_file(), "the calculation child must start before the parent dies"
    time.sleep(2.3)
    assert not completed.exists(), "orphan child survived an abrupt worker exit"
    assert not _pid_is_running(int(started.read_text())), "calculation child remains alive"


def _pid_is_running(pid: int) -> bool:
    import os
    if os.name == "nt":
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.WaitForSingleObject.restype = ctypes.c_ulong
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, 0, pid)  # SYNCHRONIZE
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: PID does not exist
                return False
            raise OSError(error, f"cannot inspect calculation PID {pid}")
        try:
            return kernel.WaitForSingleObject(handle, 0) == 0x102  # WAIT_TIMEOUT
        finally:
            kernel.CloseHandle(handle)
    from pathlib import Path
    status = Path(f"/proc/{pid}/stat")
    if status.exists():
        return status.read_text().split(") ", 1)[1][0] != "Z"
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def test_missing_parent_sentinel_fails_closed(monkeypatch):
    import pytest
    import cat_treaty.ct8_executor as executor
    monkeypatch.setattr(executor.mp, "parent_process", lambda: None)
    with pytest.raises(executor.CT8ExecutionFailure, match="parent sentinel"):
        executor._watch_parent_or_exit()


def test_hard_killed_windows_worker_stops_calculation_descendant(tmp_path):
    import os
    import subprocess
    import sys
    import time
    from pathlib import Path
    import pytest
    if os.name != "nt":
        pytest.skip("Windows process-tree termination")
    started = tmp_path / "orphan-started.txt"
    completed = tmp_path / "descendant-completed.txt"
    descendant = tmp_path / "descendant-pid.txt"
    parent = subprocess.Popen([sys.executable, "-m", "tests.ct8_orphan_parent",
        str(started), str(completed), str(descendant)], cwd=str(Path(__file__).resolve().parents[1]))
    assert parent.wait(timeout=15) == 7
    assert started.is_file() and descendant.is_file()
    time.sleep(3.4)
    assert not completed.exists(), "orphan descendant continued work"
    assert not _pid_is_running(int(started.read_text())), "calculation child remains alive"
    assert not _pid_is_running(int(descendant.read_text())), "calculation descendant remains alive"
