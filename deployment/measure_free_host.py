"""Owner-only CT8 staging probe. Prompts locally; never prints or saves its secret."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import hmac
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

from probe import fixture_digest


ROOT = Path(__file__).resolve().parent / "fixtures" / "ct7"


def call(url: str, *, body: bytes | None = None, headers: dict[str, str] | None = None):
    request = urllib.request.Request(url, data=body, method="POST" if body is not None else "GET",
                                     headers=headers or {})
    began = time.monotonic()
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.status, response.read(), time.monotonic() - began


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", required=True, help="exact Render https://*.onrender.com origin")
    args = parser.parse_args()
    if not re.fullmatch(r"https://[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com", args.api):
        raise ValueError("require exact Render HTTPS origin, no path or query")
    secret = getpass.getpass("Paste Render CT8_MEASURE_SECRET (hidden): ")
    if len(secret) < 43:
        raise ValueError("probe secret unavailable")
    manifest = json.loads((ROOT / "baseline-candidates.json").read_text())
    if manifest["source_commit"] != "2a45727b9621a860ee074d6b14172b65fd836ad3":
        raise ValueError("CT7 baseline mismatch")
    for entry in manifest["fixtures"]:
        mode = entry["route"]
        body = (ROOT / entry["request_file"]).read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if digest != entry["request_sha256"]:
            raise ValueError("fixture request digest mismatch")
        status, challenge, _ = call(args.api + "/api/ct8-measure/v1/challenge")
        if status != 200:
            raise RuntimeError(f"{mode}: challenge HTTP {status}")
        nonce = json.loads(challenge)["nonce"]
        signature = hmac.new(secret.encode("ascii"), f"{nonce}\n{mode}\n{digest}".encode("ascii"), hashlib.sha256).hexdigest()
        status, raw, elapsed = call(args.api + "/api/ct8-measure/v1/runs/" + mode, body=body,
            headers={"Content-Type": "application/json", "X-CT8-Probe-Nonce": nonce,
                     "X-CT8-Probe-Body-SHA256": digest, "X-CT8-Probe-Signature": signature})
        if status != 200:
            raise RuntimeError(f"{mode}: HTTP {status}")
        response = json.loads(raw)
        if response.get("api", {}).get("completion_status") != "complete":
            raise RuntimeError(f"{mode}: incomplete response")
        golden = fixture_digest(response, [("api", "request_id")])
        if golden != entry["response_sha256"]:
            raise RuntimeError(f"{mode}: CT7 golden response digest mismatch ({golden})")
        print(f"{mode}: CT7 golden MATCH; warm request {elapsed:.3f}s; {len(raw)} response bytes")
    print("CT8 owner-only Render Free fixture probe: PASS (host memory evidence remains separate)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError, EOFError, UnicodeError, urllib.error.URLError) as exc:
        print(f"CT8 owner-only Render Free fixture probe: STOPPED ({exc})", file=sys.stderr)
        sys.exit(1)
