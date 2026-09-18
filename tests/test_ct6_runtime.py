"""CT6 deployment-neutral runtime configuration tests."""

import pytest
from fastapi.testclient import TestClient

from cat_treaty.api import create_app
from cat_treaty.runtime import RuntimeSettings


def test_environment_runtime_settings_are_explicit(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "9001")
    monkeypatch.setenv("CT6_CORS_ORIGINS", "https://lab.edinsured.com,http://localhost:5173")
    settings = RuntimeSettings.from_environment()
    assert settings.port == 9001
    assert settings.cors_origins == ("https://lab.edinsured.com", "http://localhost:5173")


def test_wildcard_cors_is_rejected() -> None:
    with pytest.raises(ValueError, match="wildcard"):
        RuntimeSettings(cors_origins=("*",))


def test_configured_cors_is_applied_without_changing_health_contract() -> None:
    app = create_app(settings=RuntimeSettings(cors_origins=("https://lab.edinsured.com",)))
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"Origin": "https://lab.edinsured.com"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://lab.edinsured.com"


def test_invalid_port_and_boolean_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "invalid")
    with pytest.raises(ValueError, match="integer"):
        RuntimeSettings.from_environment()
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.setenv("CT6_CORS_ALLOW_CREDENTIALS", "perhaps")
    with pytest.raises(ValueError, match="boolean"):
        RuntimeSettings.from_environment()
