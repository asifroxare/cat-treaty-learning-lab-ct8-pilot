"""Local-only no-card candidate reproduction; never configures providers or deploys."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
    print("CHECK:", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path,
                        help="existing installed CT7 .venv python.exe")
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    if python.name.lower() not in ("python.exe", "python"):
        parser.error("pass the existing CT7 virtual-environment Python executable")
    env = os.environ.copy()
    env["PATH"] = str(python.parent) + os.pathsep + env.get("PATH", "")
    node = shutil.which("node", path=env["PATH"])
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm", path=env["PATH"])
    if not node or not npm:
        parser.error("Node and npm must already be installed")
    run([str(python), "-m", "pytest", "-q"], ROOT, env)
    run([node, "--test", "deployment/test_pilot_edge.mjs",
         "deployment/test_pilot_nocard_worker.mjs"], ROOT, env)
    run([npm, "ci"], FRONTEND, env)
    run([npm, "run", "check"], FRONTEND, env)
    pilot = {**env, "VITE_CT8_PILOT_MODE": "true", "VITE_CT8_NOCARD_MODE": "true",
        "VITE_CT6_API_BASE_URL": "https://ct8-cat.asif-rox.workers.dev"}
    run([npm, "run", "build"], FRONTEND, pilot)
    run([npm, "run", "build:audit"], FRONTEND, pilot)
    print("CT8 no-card review candidate: LOCAL PASS (live provider/browser acceptance still open)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"CT8 no-card review candidate: STOPPED ({error})", file=sys.stderr)
        sys.exit(1)
