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



def windows_process_tree(root_pid):
    """Enumerate the venv launcher and all live descendants with Tool Help."""
    if os.name != "nt":
        return [root_pid]
    from ctypes import wintypes
    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                   ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                   ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                   ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                   ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        raise RuntimeError("could not enumerate API child processes")
    try:
        item = Entry()
        item.dwSize = ctypes.sizeof(Entry)
        parents = {}
        if kernel.Process32FirstW(snapshot, ctypes.byref(item)):
            while True:
                parents[item.th32ProcessID] = item.th32ParentProcessID
                if not kernel.Process32NextW(snapshot, ctypes.byref(item)):
                    break
        result = {root_pid}
        while True:
            descendants = {pid for pid, parent in parents.items() if parent in result}
            new = descendants - result
            if not new:
                break
            result.update(new)
        return sorted(result)
    finally:
        kernel.CloseHandle(snapshot)

def process_tree_peak(pid):
    children = windows_process_tree(pid)
    sizes = [windows_working_set(child) for child in children]
    return sum(value for value in sizes if value is not None), children

def payload(trials, *, sample_cap=100, detail="summary"):
    if not 1 <= sample_cap <= 1000 or not 1 <= trials <= sample_cap:
        raise ValueError("trial count must remain within the reviewed local sample cap")
    if detail not in {"summary", "full"}:
        raise ValueError("unsupported measurement detail")
    request = json.loads(FIXTURE.read_text(encoding="utf-8"))
    initial = request["input"]["trials"][0]
    request["input"]["trials"] = []
    for number in range(1, trials + 1):
        trial = deepcopy(initial)
        trial["annual_trial_id"] = number
        for occurrence in trial["occurrences"]:
            occurrence["annual_trial_id"] = number
            # CT6 requires event_id unique across the entire simulation and
            # identical to its CT2 loss-basis occurrence_id.
            identifier = f"T{number}-{occurrence['event_id']}"
            occurrence["event_id"] = identifier
            occurrence["loss_basis"]["occurrence_id"] = identifier
        request["input"]["trials"].append(trial)
    request["input"]["simulation"]["trial_count"] = trials
    request["response_detail"] = detail
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
    peak, seen_pids = process_tree_peak(process.pid)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [pool.submit(send, raw) for _ in range(parallel)]
        while any(not future.done() for future in futures):
            current, children = process_tree_peak(process.pid)
            peak = max(peak, current)
            seen_pids = sorted(set(seen_pids) | set(children))
            if process.poll() is not None:
                raise RuntimeError("CT8 API process exited during measurement")
            time.sleep(0.05)
        durations = [future.result() for future in futures]
    current, children = process_tree_peak(process.pid)
    peak = max(peak, current)
    seen_pids = sorted(set(seen_pids) | set(children))
    if os.name == "nt" and peak < 16 * 1048576:
        raise RuntimeError("API memory sample is implausibly low; process tree measurement invalid")
    return {"trials_per_request": count, "parallel_requests": parallel,
            "request_body_bytes": len(raw), "wall_seconds": round(time.monotonic()-started, 4),
            "response_seconds": durations,
            "observed_process_tree_peak_mib": round(peak / 1048576, 2) if peak else None,
            "sampled_process_pids": seen_pids}


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
        if os.name == "nt" and process.poll() is None:
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
        print(f"CT8 local bounded measurement: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
