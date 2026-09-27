"""OS-bounded local Linux CT6 capacity probe; not a host-sizing approval."""
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

MAX_ADDRESS_SPACE = 2 * 1024 * 1024 * 1024
MAX_SECONDS = 100
CHILD = Path(__file__).with_name("linux_capacity_child.py")


def bounded_address_space():
    resource.setrlimit(resource.RLIMIT_AS, (MAX_ADDRESS_SPACE, MAX_ADDRESS_SPACE))


def sample(name):
    if name not in ("small", "rows25k", "small_four", "rows25k_four"):
        raise ValueError("unreviewed workload")
    start = time.monotonic()
    print(f"Linux bounded CT6 {name}: started (2 GiB address-space / 100s deadline)", flush=True)
    process = subprocess.Popen([sys.executable, str(CHILD), name],
        cwd=CHILD.parents[1], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=bounded_address_space)
    try:
        stdout, stderr = process.communicate(timeout=MAX_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise RuntimeError(f"{name} exceeded {MAX_SECONDS}s")
    if process.returncode:
        raise RuntimeError(f"{name} exited {process.returncode}: {stderr[-1800:]!r}")
    result = json.loads(stdout)
    result["wall_seconds"] = round(time.monotonic() - start, 3)
    print(json.dumps(result), flush=True)
    return result


def main():
    if sys.platform != "linux":
        raise RuntimeError("Linux-only probe")
    for name in sys.argv[1:] or ("small",):
        sample(name)
    print("Linux bounded CT6 selected scenarios: COMPLETE (not staging approval)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Linux bounded CT6 capacity: STOPPED ({error})", file=sys.stderr)
        sys.exit(1)
