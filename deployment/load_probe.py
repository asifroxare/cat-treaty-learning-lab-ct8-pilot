"""Controlled staging load probe; never point at public production without authorization."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import statistics
import time
from probe import post


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--route", required=True, choices=["catalogue", "hours-clause"])
    parser.add_argument("--concurrency", required=True, type=int)
    parser.add_argument("--total", required=True, type=int)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if not args.api.startswith("http://127.0.0.1:") and not args.api.startswith("http://localhost:"):
        parser.error("load probe is restricted to loopback; staging requires separately reviewed authorization")
    if not 1 <= args.concurrency <= 8 or not 1 <= args.total <= 32:
        parser.error("concurrency must be 1..8 and total 1..32")
    payload = json.loads(args.fixture.read_text(encoding="utf-8"))
    url = args.api.rstrip("/") + "/api/v1/runs/" + args.route
    def invoke(_):
        status, _, body, seconds, size = post(url, payload, args.timeout)
        if status != 200 or body.get("api", {}).get("completion_status") != "complete":
            raise RuntimeError("incomplete or non-success response")
        return seconds, size
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = [future.result() for future in as_completed([pool.submit(invoke, i) for i in range(args.total)])]
    durations = sorted(result[0] for result in results)
    print(json.dumps({"count": len(results), "concurrency": args.concurrency,
        "wall_seconds": round(time.monotonic()-start, 3), "max_seconds": round(max(durations), 3),
        "median_seconds": round(statistics.median(durations), 3),
        "max_response_bytes": max(result[1] for result in results)}, indent=2))
    print("Measurement only: no production threshold can be inferred from this local run")


if __name__ == "__main__":
    main()
