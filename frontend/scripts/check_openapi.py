"""Fail when the committed frontend contract differs from the CT6 application."""

from pathlib import Path
import json
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from cat_treaty.api import create_app  # noqa: E402


def main() -> None:
    snapshot_path = REPOSITORY_ROOT / "frontend" / "openapi" / "ct6.openapi.json"
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    current = create_app().openapi()
    if snapshot != current:
        raise SystemExit(
            "CT6 OpenAPI drift detected. Review the backend change before "
            "running frontend/scripts/export_openapi.py and npm run api:generate."
        )
    print("CT6 OpenAPI contract: PASS")


if __name__ == "__main__":
    main()
