"""Reproduce the frozen CT7 release from a clean extracted package."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
FRONTEND = ROOT / "frontend"


def run(*command: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print(f"\n[CT7 reproduction] {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def main() -> int:
    if not VENV.exists():
        run(sys.executable, "-m", "venv", str(VENV))
    scripts = VENV / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    runtime_env = os.environ.copy()
    runtime_env["PATH"] = f"{scripts}{os.pathsep}{runtime_env.get('PATH', '')}"
    runtime_env["PYTHON"] = str(python)

    run(str(python), "-m", "pip", "install", "-r", "requirements-dev.txt", env=runtime_env)
    run(str(python), "-m", "pip", "install", "-e", ".", env=runtime_env)
    run(str(python), "-m", "pip", "check", env=runtime_env)
    run(str(python), "-m", "pytest", "-q", env=runtime_env)
    run("npm", "ci", cwd=FRONTEND, env=runtime_env)
    run("npm", "run", "check", cwd=FRONTEND, env=runtime_env)
    run("npm", "audit", "--audit-level=high", cwd=FRONTEND, env=runtime_env)
    run("npm", "run", "test:real-api", cwd=FRONTEND, env=runtime_env)
    print("\nCT7 independent reproduction: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
