"""CT6 byte and presentation-limit boundary tests."""

from fastapi.testclient import TestClient

import cat_treaty.api as api_module
from cat_treaty.api import create_app
from cat_treaty.ct6_models import ResponseDetail
from tests.test_ct6_models import valid_request


def test_summary_remains_eligible_when_full_detail_cap_blocks_full(monkeypatch) -> None:
    monkeypatch.setattr(api_module, "MAX_FULL_DETAIL_ROWS", 0)
    full = valid_request().model_dump(mode="json")
    summary = valid_request().model_copy(update={"response_detail": ResponseDetail.SUMMARY}).model_dump(mode="json")
    with TestClient(create_app()) as client:
        full_response = client.post("/api/v1/runs/catalogue", json=full)
        summary_response = client.post("/api/v1/runs/catalogue", json=summary)
    assert full_response.status_code == 413
    assert summary_response.status_code == 200
    assert summary_response.json()["pre_capacity"]["occurrence_rows"] is None


def test_declared_oversized_content_length_is_rejected_before_parsing() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/runs/catalogue",
            content=b"{}",
            headers={
                "content-type": "application/json",
                "content-length": str(api_module.MAX_REQUEST_BYTES + 1),
            },
        )
    assert response.status_code == 413
    assert response.json()["code"] == "CT6_REQUEST_TOO_LARGE"
