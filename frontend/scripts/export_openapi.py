"""Export the authoritative CT6 OpenAPI document for frontend type generation."""

from pathlib import Path
import json
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from cat_treaty.api import create_app  # noqa: E402


def main() -> None:
    target = REPOSITORY_ROOT / "frontend" / "openapi" / "ct6.openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(create_app().openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Exported CT6 OpenAPI to {target.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    main()
