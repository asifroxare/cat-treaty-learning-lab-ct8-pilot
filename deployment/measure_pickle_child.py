"""Disposable worker for CT8 serialization measurement; prints sizes only."""
import json
import pickle
import sys

from measure_local import payload
from cat_treaty.api import _normalize_json_value
from cat_treaty.ct6_models import CatalogueRunRequest
from cat_treaty.ct6_orchestration import run_catalogue


def main():
    count = int(sys.argv[1])
    raw = payload(count, sample_cap=10000, detail="full")
    if len(raw) > 12 * 1024 * 1024:
        raise ValueError("local synthetic body exceeded 12 MiB")
    request = CatalogueRunRequest.model_validate(
        _normalize_json_value(CatalogueRunRequest, json.loads(raw)))
    result = run_catalogue(request)
    encoded = pickle.dumps(("ok", result), protocol=5)
    print(json.dumps({"trials": count, "request_bytes": len(raw),
                      "serialized_result_bytes": len(encoded)}), flush=True)


if __name__ == "__main__":
    main()
