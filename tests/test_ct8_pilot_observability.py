"""Operator evidence never contains request data or tester identity."""
import json
import logging

from cat_treaty.pilot_observability import record, resource_snapshot


def test_pilot_resource_evidence_has_only_bounded_safe_fields(caplog):
    snapshot = resource_snapshot()
    assert set(snapshot) == {
        "cgroup_peak_bytes", "cgroup_current_bytes", "cgroup_limit_bytes",
        "api_peak_rss_kib", "reaped_child_peak_rss_kib",
    }
    assert all(value is None or (isinstance(value, int) and value >= 0)
               for value in snapshot.values())
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        record(mode="catalogue", outcome="complete", elapsed_ms=100,
               request_bytes=1000, response_bytes=2000)
    observed = json.loads(caplog.records[-1].message)
    assert observed["event"] == "pilot_request"
    assert observed["mode"] == "catalogue"
    assert observed["outcome"] == "complete"
    assert observed["cgroup_peak_bytes"] == snapshot["cgroup_peak_bytes"]
    assert not ({"email", "ip", "request_id", "token", "input", "result"} & set(observed))
