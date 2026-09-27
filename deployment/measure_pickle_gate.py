"""Local guarded CT8 pickle-size probe; never contacts a public API."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from measure_local import ROOT, process_tree_peak

MAX_SECONDS = 30
MAX_PEAK_BYTES = 800 * 1024 * 1024


def stop_tree(process):
    if process.poll() is None and os.name == "nt":
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    elif process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def sample(python: Path, count: int):
    if count not in (1000, 2500, 5000, 10000):
        raise ValueError("count outside the fixed reviewed samples")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT)
    process = subprocess.Popen([str(python), str(Path(__file__).with_name("measure_pickle_child.py")),
                                str(count)], cwd=ROOT, env=environment,
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    start = time.monotonic()
    peak = 0
    pids = set()
    print(f"CT8 local probe: {count} full-detail trials started (30s / 800 MiB safety stops)", flush=True)
    next_progress = start + 5
    try:
        while process.poll() is None:
            now = time.monotonic()
            if now >= MAX_SECONDS + start:
                raise RuntimeError(f"stopped {count} trials at the 30-second local deadline")
            if now >= next_progress:
                print(f"CT8 local probe: {count} trials, {int(now - start)}s elapsed", flush=True)
                next_progress = now + 5
            current, children = process_tree_peak(process.pid)
            peak = max(peak, current)
            pids.update(children)
            if peak >= MAX_PEAK_BYTES:
                raise RuntimeError(f"stopped {count} trials at the 800 MiB local process-tree limit")
            time.sleep(0.4)
        stdout, stderr = process.communicate(timeout=5)
        if process.returncode:
            raise RuntimeError(f"{count}-trial computation exited {process.returncode}: {stderr[-2400:]!r}")
        result = json.loads(stdout)
        if result.get("trials") != count:
            raise RuntimeError("child returned the wrong trial count")
        result.update({"wall_seconds": round(time.monotonic() - start, 4),
                       "observed_process_tree_peak_mib": round(peak / 1048576, 2),
                       "sampled_process_pids": sorted(pids)})
        return result
    finally:
        stop_tree(process)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    results = []
    for count in (1000, 2500, 5000):
        try:
            result = sample(python, count)
            results.append(result)
            print(json.dumps(result), flush=True)
        except (OSError, ValueError, RuntimeError, KeyboardInterrupt) as error:
            print(f"CT8 guarded pickle probe: STOPPED ({error})", file=sys.stderr)
            print(json.dumps({"completed_samples": results}, indent=2))
            return 1
    print("CT8 guarded pickle probe: PASS (max-legal capacity still open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
