"""One-command Windows reproduction using the owner's existing CT7 Python environment.

Does not copy, replace or modify CT7's .venv or repository.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def run(command, cwd, environment):
    print("CHECK:", " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", required=True, type=Path, help="Existing installed CT7 .venv python.exe")
    args = parser.parse_args()
    python = args.python.resolve(strict=True)
    if not python.is_file() or python.name.lower() not in ("python.exe", "python"):
        parser.error("--python must be the existing CT7 virtual-environment Python executable")
    environment = os.environ.copy()
    environment["PYTHON"] = str(python)
    environment["PATH"] = str(python.parent) + os.pathsep + environment.get("PATH", "")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm", path=environment["PATH"])
    if npm is None:
        parser.error("npm is not available; install the supported Node version first")
    run([str(python), "-m", "pytest", "-q"], ROOT, environment)
    run([npm, "ci"], FRONTEND, environment)
    run([npm, "run", "check"], FRONTEND, environment)
    run([npm, "run", "test:real-api"], FRONTEND, environment)
    print("CT8 candidate Windows reproduction: PASS (backend, frontend and real CT6 API)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"CT8 candidate Windows reproduction: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
