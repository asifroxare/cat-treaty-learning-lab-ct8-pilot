"""Compare approved CT7 synthetic responses with the unchanged CT8 API in process."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from probe import fixture_digest

BASELINE = "2a45727b9621a860ee074d6b14172b65fd836ad3"
ROUTES = {"catalogue", "hours-clause"}


def verify_manifest(folder: Path):
    folder = folder.resolve(strict=True)
    manifest = json.loads((folder / "baseline-candidates.json").read_text(encoding="utf-8"))
    if manifest.get("source_commit") != BASELINE or manifest.get("normalization") != ["api.request_id"]:
        raise ValueError("baseline identity or normalization differs from frozen CT7")
    entries = manifest.get("fixtures")
    if not isinstance(entries, list) or {item.get("route") for item in entries} != ROUTES or len(entries) != 2:
        raise ValueError("require exactly one catalogue and one hours-clause fixture")
    verified = []
    for item in entries:
        route, name = item["route"], item["request_file"]
        if name != f"approved-{route}.json":
            raise ValueError("unexpected fixture filename")
        for field in ("request_sha256", "response_sha256"):
            if not re.fullmatch("[0-9a-f]{64}", item[field]):
                raise ValueError(f"invalid {field}")
        raw = (folder / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["request_sha256"]:
            raise ValueError(f"{route} fixture bytes do not match reviewed manifest")
        verified.append((route, raw, item["response_sha256"]))
    return verified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True, help="CT7 golden candidates folder")
    args = parser.parse_args()
    cases = verify_manifest(args.folder)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from fastapi.testclient import TestClient
    import cat_treaty.api as ct8_api
    if root not in Path(ct8_api.__file__).resolve().parents:
        raise RuntimeError("API import did not resolve to the CT8 candidate")
    create_app = ct8_api.create_app
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        for route, raw, expected in cases:
            response = client.post("/api/v1/runs/" + route, content=raw,
                                   headers={"Content-Type": "application/json"})
            if response.status_code != 200:
                raise RuntimeError(f"{route}: HTTP {response.status_code}")
            body = response.json()
            if body.get("api", {}).get("completion_status") != "complete":
                raise RuntimeError(f"{route}: incomplete response")
            digest = fixture_digest(body, [("api", "request_id")])
            if digest != expected:
                raise RuntimeError(f"{route}: CT7 versus CT8 response mismatch ({digest})")
            print(f"{route}: CT7 full-response golden digest MATCH")
    print("CT8 frozen CT7 synthetic golden comparison: PASS")
    print("Coverage is limited to the two supplied fixture scenarios; this is not independent actuarial validation.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, ImportError) as error:
        print(f"CT8 golden comparison: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
