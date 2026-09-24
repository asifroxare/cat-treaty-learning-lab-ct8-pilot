"""Export CT7 fixtures from the frozen test constructors for independent review.

Run only against the exact CT7 release, not CT8. Does not approve fixture hashes.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from probe import fixture_digest

BASELINE = "2a45727b9621a860ee074d6b14172b65fd836ad3"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ct7-root", type=Path, required=True, help="Installed clean CT7 repository")
    args = parser.parse_args()
    root = args.ct7_root.resolve()
    if not (root / "cat_treaty" / "api.py").is_file():
        parser.error("--ct7-root is not a CT7 repository")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if head != BASELINE or subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip():
        parser.error("export must run from the clean exact CT7 commit; never fabricate baseline from changed code")
    sys.path.insert(0, str(root))
    from fastapi.testclient import TestClient
    from cat_treaty.api import create_app
    from tests.test_ct6_models import valid_request
    from tests.test_ct6_adapters import valid_hours_request

    output = args.output.resolve()
    if output == root or root in output.parents:
        parser.error("output must be outside the frozen CT7 tree")
    if output.exists() and any(output.iterdir()):
        parser.error("output folder must be empty")
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"source_commit": BASELINE, "normalization": ["api.request_id"], "fixtures": []}
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        for route, request in (("catalogue", valid_request()), ("hours-clause", valid_hours_request())):
            raw = (json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            response = client.post("/api/v1/runs/" + route, content=raw, headers={"Content-Type": "application/json"})
            if response.status_code != 200:
                raise RuntimeError(f"{route}: CT7 fixture failed with HTTP {response.status_code}")
            payload = response.json()
            if payload["api"]["completion_status"] != "complete":
                raise RuntimeError(f"{route}: incomplete result")
            name = f"approved-{route}.json"
            (output / name).write_bytes(raw)
            manifest["fixtures"].append({"route": route, "request_file": name,
                "request_sha256": hashlib.sha256(raw).hexdigest(),
                "response_sha256": fixture_digest(payload, [("api", "request_id")])})
    (output / "baseline-candidates.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("CT7 fixture candidates exported. Independent review is required before use as release evidence.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError, ImportError) as error:
        print(f"CT7 fixture export: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
