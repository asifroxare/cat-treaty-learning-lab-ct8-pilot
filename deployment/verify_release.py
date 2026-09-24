"""Check source identity and production frontend configuration before staging."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "2a45727b9621a860ee074d6b14172b65fd836ad3"


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-origin", required=True, help="Expected HTTPS API origin embedded in the production build")
    args = parser.parse_args()
    origin = args.api_origin.rstrip("/")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::\d+)?", origin) or "localhost" in origin or "127.0.0.1" in origin:
        parser.error("require an explicit public HTTPS API origin")
    head = run("git", "rev-parse", "HEAD")
    if head != BASELINE:
        print(f"Source HEAD differs from CT7 baseline: {head}; require a reviewed CT8 commit")
    if run("git", "status", "--porcelain"):
        raise RuntimeError("working tree must be clean for a release build")
    dist = ROOT / "frontend" / "dist"
    html = dist / "index.html"
    if not html.is_file():
        raise RuntimeError("missing frontend/dist/index.html; build production assets first")
    files = sorted(p for p in dist.rglob("*") if p.is_file())
    scripts = [p for p in files if p.suffix == ".js"]
    if not scripts or not any(origin.encode() in p.read_bytes() for p in scripts):
        raise RuntimeError("expected production API origin was not found in built JavaScript")
    if any(b"http://localhost:8000" in p.read_bytes() for p in scripts):
        raise RuntimeError("development API origin was found in built JavaScript")
    report = {"source_commit": head, "api_origin": origin, "artifacts": {str(p.relative_to(ROOT)): sha(p) for p in files},
              "openapi_sha256": sha(ROOT / "frontend" / "openapi" / "ct6.openapi.json")}
    print(json.dumps(report, indent=2, sort_keys=True))
    print("Release configuration: PASS")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Release configuration: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
