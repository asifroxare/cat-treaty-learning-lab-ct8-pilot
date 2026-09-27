"""Fail-closed local Linux full-API probe; never a public deployment command.

Run only inside a dedicated cgroup-v2 container with 1.5-2 GiB memory.max,
the project's Python dependencies installed, and no other workload in its
cgroup. --full explicitly enables the expensive four-layer legal fixture.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

from measure_local import payload

ROOT = Path(__file__).resolve().parents[1]
LIMIT_LOW = 1536 * 1024 * 1024
LIMIT_HIGH = 2 * 1024 * 1024 * 1024
MAX_RESPONSE = 150 * 1024 * 1024
PORT = 18764
URL = f"http://127.0.0.1:{PORT}"


def cgroup():
    if sys.platform != "linux":
        raise RuntimeError("requires Linux and a dedicated cgroup-v2 container")
    lines = Path("/proc/self/cgroup").read_text().splitlines()
    matches = [line.split("::", 1)[1] for line in lines if line.startswith("0::")]
    if len(matches) != 1:
        raise RuntimeError("cgroup v2 path unavailable")
    root = Path("/sys/fs/cgroup")
    group = (root / matches[0].lstrip("/")).resolve()
    if not group.is_relative_to(root) or not (group / "memory.max").exists():
        raise RuntimeError("cgroup memory.max unavailable")
    raw = (group / "memory.max").read_text().strip()
    if not raw.isdecimal() or not LIMIT_LOW <= int(raw) <= LIMIT_HIGH:
        raise RuntimeError("dedicated 1.5-2 GiB cgroup memory.max required")
    return group, int(raw)


def fixture(full):
    count = 10000 if full else 1000
    rows = 25000 if full else None
    wire = json.loads(payload(count, sample_cap=10000, detail="full", total_occurrences=rows))
    program = wire["input"]["program"]
    terms = wire["input"]["treaty_terms"]
    base = program["layers"][0]
    base_terms = terms["layer_terms"][0]
    for number in (2, 3, 4):
        layer = deepcopy(base)
        layer["layer_id"] = f"L{number}"
        layer["attachment"] = base["attachment"] + (number - 1) * base["occurrence_limit"]
        term = deepcopy(base_terms)
        term["layer_id"] = layer["layer_id"]
        program["layers"].append(layer)
        terms["layer_terms"].append(term)
    raw = json.dumps(wire, separators=(",", ":")).encode()
    if len(raw) > 25 * 1024 * 1024:
        raise RuntimeError("fixture exceeds frozen CT6 input limit")
    return raw


def request(path, raw=None, timeout=5):
    req = urllib.request.Request(URL + path, data=raw,
        headers={"Content-Type": "application/json"} if raw else {},
        method="POST" if raw else "GET")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_RESPONSE:
            raise RuntimeError("API response exceeds guarded probe limit")
        body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise RuntimeError("API response exceeds guarded probe limit")
        return response.status, body


def wait_ready():
    for _ in range(50):
        try:
            code, raw = request("/health/ready")
            if code == 200 and json.loads(raw).get("status") == "ready":
                return
        except (OSError, ValueError):
            pass
        time.sleep(0.1)
    raise RuntimeError("single-worker API failed readiness before request")


def run(full):
    group, memory_limit = cgroup()
    # This probe starts the only API worker and aborts if a same-cgroup server
    # already listens on its private loopback port.
    try:
        request("/health/live")
    except (OSError, ValueError):
        pass
    else:
        raise RuntimeError("probe port already serves an API")
    raw = fixture(full)
    environment = dict(os.environ, CT8_ISOLATED_RUNS="true",
        CT8_ISOLATION_DEADLINE_SECONDS="90", CT8_ISOLATION_MAX_CONCURRENCY="1",
        CT6_HOST="127.0.0.1", CT6_PORT=str(PORT))
    before = (group / "memory.events").read_text()
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "cat_treaty.api:app",
        "--host", "127.0.0.1", "--port", str(PORT), "--workers", "1",
        "--no-access-log"], cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        wait_ready()
        if server.poll() is not None:
            raise RuntimeError("API exited before request")
        start = time.monotonic()
        try:
            code, body = request("/api/v1/runs/catalogue", raw, timeout=105)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"API rejected fixture: HTTP {error.code}, {error.read(500)!r}") from error
        elapsed = round(time.monotonic() - start, 3)
        data = json.loads(body)
        if code != 200 or data.get("api", {}).get("completion_status") != "complete":
            raise RuntimeError("missing authoritative completed response")
        if not data["api"].pop("request_id", None):
            raise RuntimeError("missing request correlation ID")
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        after = (group / "memory.events").read_text()
        def events(raw):
            return {key: int(value) for key, value in (line.split() for line in raw.splitlines())}
        if any(events(after).get(key, 0) != events(before).get(key, 0)
               for key in ("oom", "oom_kill", "max")):
            raise RuntimeError("container memory ceiling was hit")
        print(json.dumps({"fixture": "four_layer_25k" if full else "four_layer_1k",
            "status": code, "request_bytes": len(raw), "response_bytes": len(body),
            "seconds": elapsed, "cgroup_limit_bytes": memory_limit,
            "cgroup_peak_bytes": int((group / "memory.peak").read_text()),
            "full_response_sha256_excluding_request_id": hashlib.sha256(normalized).hexdigest()}))
    finally:
        if server.poll() is None:
            os.killpg(server.pid, signal.SIGTERM)
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGKILL)
                server.wait(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="explicitly run the 25k-row case")
    options = parser.parse_args()
    try:
        run(options.full)
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(f"CT8 bounded Linux full API: STOPPED ({error})")
