"""Bounded local CT8 capacity measurements; never targets a public host."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "deployment" / "fixtures" / "ct7" / "approved-catalogue.json"
URL = "http://127.0.0.1:8767"


def windows_working_set(pid):
    if os.name != "nt":
        return None
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                   ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                   ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                   ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                   ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return None
        return max(counters.WorkingSetSize, counters.PeakWorkingSetSize)
    finally:
        kernel.CloseHandle(handle)


def payload(trials):
    if not 1 <= trials <= 100:
        raise ValueError("trial count must remain within the reviewed local sample cap")
    request = json.loads(FIXTURE.read_text(encoding="utf-8"))
    initial = request["input"]["trials"][0]
    request["input"]["trials"] = []
    for number in range(1, trials + 1):
        trial = deepcopy(initial)
        trial["annual_trial_id"] = number
        for occurrence in trial["occurrences"]:
            occurrence["annual_trial_id"] = number
        request["input"]["trials"].append(trial)
    request["input"]["simulation"]["trial_count"] = trials
    request["response_detail"] = "summary"
    return json.dumps(request, separators=(",", ":")).encode("utf-8")


def send(raw):
    request = urllib.request.Request(URL + "/api/v1/runs/catalogue", data=raw,
                                     headers={"Content-Type": "application/json"}, method="POST")
    began = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
            if response.status != 200 or body.get("api", {}).get("completion_status") != "complete":
                raise RuntimeError("API returned an incomplete result")
            return round(time.monotonic() - began, 4)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"CT6 rejected synthetic workload: HTTP {error.code}, {error.read()[:350]!r}") from error


def sample(process, count, parallel):
    raw = payload(count)
    peak = windows_working_set(process.pid) or 0
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [pool.submit(send, raw) for _ in range(parallel)]
        while any(not future.done() for future in futures):
            peak = max(peak, windows_working_set(process.pid) or 0)
            if process.poll() is not None:
                raise RuntimeError("CT8 API process exited during measurement")
            time.sleep(0.05)
        durations = [future.result() for future in futures]
    peak = max(peak, windows_working_set(process.pid) or 0)
    return {"trials_per_request": count, "parallel_requests": parallel,
            "request_body_bytes": len(raw), "wall_seconds": round(time.monotonic()-started, 4),
            "response_seconds": durations,
            "observed_api_process_peak_mib": round(peak / 1048576, 2) if peak else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path, help="existing CT7 .venv python.exe")
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    if not python.is_file():
        parser.error("Python executable missing")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    process = subprocess.Popen([str(python), "-m", "uvicorn", "cat_treaty.api:app",
                                "--host", "127.0.0.1", "--port", "8767", "--log-level", "warning"],
                               cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            if process.poll() is not None:
                raise RuntimeError("CT8 API did not start; verify port 8767 is free")
            try:
                with urllib.request.urlopen(URL + "/health/ready", timeout=1) as response:
                    if json.loads(response.read()).get("status") == "ready":
                        break
            except (OSError, ValueError):
                time.sleep(0.1)
        else:
            raise RuntimeError("CT8 API readiness timed out")
        results = [sample(process, n, parallel) for n, parallel in ((1,1),(10,1),(100,1),(10,2))]
        print(json.dumps({"measurement_scope": "local synthetic, maximum 100 trials per request",
                          "machine": "owner Windows; provide CPU/RAM separately if used for capacity decisions",
                          "results": results}, indent=2))
        print("CT8 local bounded measurement: PASS (measurements only; no public capacity threshold established)")
    finally:
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
        print(f"CT8 local bounded measurement: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
