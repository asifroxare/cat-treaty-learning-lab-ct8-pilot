"""CT6 transport-level identity invariants."""

from fastapi.testclient import TestClient

from cat_treaty.api import create_app
from tests.test_ct6_models import valid_request


def test_request_id_and_json_object_order_do_not_change_authoritative_identity() -> None:
    payload = valid_request().model_dump(mode="json")
    reordered = dict(reversed(tuple(payload.items())))
    with TestClient(create_app()) as client:
        first = client.post("/api/v1/runs/catalogue", json=payload, headers={"X-Request-ID": "first"}).json()
        second = client.post("/api/v1/runs/catalogue", json=reordered, headers={"X-Request-ID": "second"}).json()
    assert first["identity"] == second["identity"]
    assert first["api"]["request_id"] != second["api"]["request_id"]

