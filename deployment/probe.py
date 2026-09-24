"""Read-only deployment probe. Standard library; no actuarial calculations."""
import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def get(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return response.status, response.headers, response.read()


def post(url, payload, timeout=120):
    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return response.status, response.headers, json.loads(body), time.monotonic() - start, len(body)


def fixture_digest(result, excluded):
    """Hash the full response after removing only predeclared transport request IDs."""
    import copy
    obj = copy.deepcopy(result)
    for path in excluded:
        cursor = obj
        for key in path[:-1]:
            cursor = cursor[key]
        del cursor[path[-1]]
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True, help="API origin, without trailing slash")
    parser.add_argument("--fixture", type=Path, help="CT6 JSON request fixture")
    parser.add_argument("--route", choices=["catalogue", "hours-clause"])
    parser.add_argument("--expected-digest", help="Preapproved canonical response SHA-256")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--metrics-only", action="store_true", help="Report duration and response bytes; do not print treaty content")
    args = parser.parse_args()
    if args.fixture and not args.route or args.route and not args.fixture:
        parser.error("--fixture and --route must be given together")
    if args.expected_digest and not args.fixture:
        parser.error("--expected-digest requires --fixture")
    base = args.api.rstrip("/")
    for route in ("/health/live", "/health/ready", "/api/v1/capabilities"):
        status, _, raw = get(base + route, timeout=args.timeout)
        parsed = json.loads(raw)
        if status != 200 or (route.endswith("ready") and parsed.get("status") != "ready"):
            raise RuntimeError(f"{route}: unexpected response")
        print(f"{route}: PASS")
    if args.fixture:
        payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        status, headers, result, duration, size = post(base + "/api/v1/runs/" + args.route, payload, args.timeout)
        if status != 200 or result.get("api", {}).get("completion_status") != "complete":
            raise RuntimeError("run did not return a complete authoritative response")
        if not headers.get("X-Request-ID"):
            raise RuntimeError("missing request correlation header")
        # CT6 request IDs are transport fields. No business fields are excluded.
        excluded = [("api", "request_id")]
        digest = fixture_digest(result, excluded)
        if args.expected_digest and digest.lower() != args.expected_digest.lower():
            raise RuntimeError(f"golden response mismatch: {digest}")
        print(f"{args.route}: PASS, {duration:.3f}s, {size} bytes, normalized SHA-256 {digest}")
        if not args.expected_digest:
            print("UNAPPROVED BASELINE: obtain independent fixture approval before treating this digest as a release gate")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, urllib.error.URLError) as error:
        print(f"deployment probe: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
