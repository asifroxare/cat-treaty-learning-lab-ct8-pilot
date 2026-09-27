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
    scenario = sys.argv[2] if len(sys.argv) > 2 else "one"
    if scenario not in {"one", "rows25k"}:
        raise ValueError("unreviewed scenario")
    rows = 25000 if scenario == "rows25k" and count == 10000 else None
    if scenario == "rows25k" and rows is None:
        raise ValueError("row-limit scenario requires 10000 trials")
    raw = payload(count, sample_cap=10000, detail="full", total_occurrences=rows)
    if len(raw) > 25 * 1024 * 1024:
        raise ValueError("synthetic request exceeded the frozen 25 MiB input limit")
    request = CatalogueRunRequest.model_validate(
        _normalize_json_value(CatalogueRunRequest, json.loads(raw)))
    result = run_catalogue(request)
    encoded = pickle.dumps(("ok", result), protocol=5)
    print(json.dumps({"trials": count, "occurrences": rows or count,
                      "request_bytes": len(raw),
                      "serialized_result_bytes": len(encoded)}), flush=True)


if __name__ == "__main__":
    main()
