"""CT6 stable problem catalogue and containment tests."""

from fastapi.testclient import TestClient

import cat_treaty.api as api_module
from cat_treaty.api import create_app
from tests.test_ct6_models import valid_request


def test_every_public_problem_uses_static_reviewed_text() -> None:
    for code, value in api_module._MESSAGES.items():
        title, detail = value
        assert code.startswith("CT6_")
        assert title and detail
        assert "{" not in title + detail
        assert "traceback" not in (title + detail).lower()


def test_expected_4xx_never_contains_client_value() -> None:
    payload = valid_request().model_dump(mode="json")
    payload["api_schema_version"] = "private-client-version"
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.post("/api/v1/runs/catalogue", json=payload)
    assert response.status_code == 409
    assert "private-client-version" not in response.text

