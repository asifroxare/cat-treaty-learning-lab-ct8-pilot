"""Small, non-sensitive memory snapshot for an invited pilot on Linux."""
from __future__ import annotations

import json
import logging
from pathlib import Path
import sys

LOG = logging.getLogger("uvicorn.error")


def _read_number(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
        return int(raw) if raw.isdecimal() else None
    except (OSError, ValueError):
        return None


def resource_snapshot() -> dict[str, int | None]:
    """Cgroup total includes API and child; absent metrics remain explicit."""
    result: dict[str, int | None] = {
        "cgroup_peak_bytes": None, "cgroup_current_bytes": None,
        "cgroup_limit_bytes": None, "api_peak_rss_kib": None,
        "reaped_child_peak_rss_kib": None,
    }
    if sys.platform != "linux":
        return result
    try:
        import resource
        result["api_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["reaped_child_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        entries = Path("/proc/self/cgroup").read_text(encoding="ascii").splitlines()
        unified = [line.split("::", 1)[1] for line in entries if line.startswith("0::")]
        if len(unified) == 1:
            base = Path("/sys/fs/cgroup")
            group = (base / unified[0].lstrip("/")).resolve()
            if group.is_relative_to(base):
                result["cgroup_peak_bytes"] = _read_number(group / "memory.peak")
                result["cgroup_current_bytes"] = _read_number(group / "memory.current")
                result["cgroup_limit_bytes"] = _read_number(group / "memory.max")
        else:
            legacy = [line.split(":", 2)[2] for line in entries
                      if len(line.split(":", 2)) == 3 and "memory" in line.split(":", 2)[1].split(",")]
            if len(legacy) == 1:
                base = Path("/sys/fs/cgroup/memory")
                group = (base / legacy[0].lstrip("/")).resolve()
                if group.is_relative_to(base):
                    result["cgroup_peak_bytes"] = _read_number(group / "memory.max_usage_in_bytes")
                    result["cgroup_current_bytes"] = _read_number(group / "memory.usage_in_bytes")
                    result["cgroup_limit_bytes"] = _read_number(group / "memory.limit_in_bytes")
    except (OSError, ValueError):
        pass
    return result


def record(*, mode: str, outcome: str, elapsed_ms: int | None = None,
           request_bytes: int | None = None, response_bytes: int | None = None,
           include_resource: bool = True) -> None:
    """No input, result, IP, token, email, stack trace or request ID in logs."""
    LOG.info(json.dumps({"event": "pilot_request", "mode": mode, "outcome": outcome,
        "elapsed_ms": elapsed_ms, "request_bytes": request_bytes,
        "response_bytes": response_bytes,
        **(resource_snapshot() if include_resource else {})}, separators=(",", ":")))
