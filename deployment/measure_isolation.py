"""Bounded opt-in isolation measurement; local only, at most 1000 trials."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

from measure_local import ROOT, URL, payload, process_tree_peak


def measure(process, trials, detail):
    raw = payload(trials, sample_cap=1000, detail=detail)
    if len(raw) > 2 * 1024 * 1024:
        raise RuntimeError("synthetic request exceeds the 2 MiB local probe cap")
    request = urllib.request.Request(URL + "/api/v1/runs/catalogue", data=raw,
        headers={"Content-Type": "application/json"}, method="POST")
    began = time.monotonic()
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(urllib.request.urlopen, request, timeout=45)
        peak, pids = process_tree_peak(process.pid)
        while not future.done():
            current, children = process_tree_peak(process.pid)
            peak = max(peak, current)
            pids = sorted(set(pids) | set(children))
            if process.poll() is not None:
                raise RuntimeError("local API process exited unexpectedly")
            time.sleep(0.025)
        try:
            with future.result() as response:
                raw_response = response.read()
                status = response.status
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"local API returned HTTP {error.code}: {error.read()[:240]!r}") from error
    body = json.loads(raw_response)
    if status != 200 or body.get("api", {}).get("completion_status") != "complete":
        raise RuntimeError("local API returned an incomplete result")
    current, children = process_tree_peak(process.pid)
    peak = max(peak, current)
    pids = sorted(set(pids) | set(children))
    if os.name == "nt" and peak < 16 * 1048576:
        raise RuntimeError("process-tree memory sample is implausibly low")
    return {"trials": trials, "detail": detail, "request_bytes": len(raw),
            "response_bytes": len(raw_response),
            "wall_seconds": round(time.monotonic() - began, 4),
            "observed_process_tree_peak_mib": round(peak / 1048576, 2) if peak else None,
            "sampled_process_pids": pids}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path)
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    environment["CT8_ISOLATED_RUNS"] = "true"
    environment["CT8_ISOLATION_DEADLINE_SECONDS"] = "30"
    environment["CT8_ISOLATION_MAX_CONCURRENCY"] = "1"
    process = subprocess.Popen([str(python), "-m", "uvicorn", "cat_treaty.api:app",
        "--host", "127.0.0.1", "--port", "8767", "--workers", "1", "--log-level", "warning"],
        cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError("local API did not start; check port 8767")
            try:
                with urllib.request.urlopen(URL + "/health/ready", timeout=1) as response:
                    if json.loads(response.read()).get("status") == "ready":
                        break
            except (OSError, ValueError):
                time.sleep(0.1)
        else:
            raise RuntimeError("local API readiness timed out")
        results = [measure(process, count, detail) for count, detail in
                   ((100, "summary"), (500, "summary"), (1000, "summary"), (1000, "full"))]
        print(json.dumps({"scope": "local opt-in isolation, one worker, one request at a time",
                          "limits": "at most 1000 trials and 2 MiB request; 30s isolated deadline",
                          "results": results}, indent=2))
        print("CT8 bounded isolation measurement: PASS (capacity decision still open)")
    finally:
        if process.poll() is None and os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        elif process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"CT8 bounded isolation measurement: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
