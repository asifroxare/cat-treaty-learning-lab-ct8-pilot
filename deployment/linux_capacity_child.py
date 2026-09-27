"""Direct CT6 capacity worker for a separately resource-bounded Linux process."""
import ast
from copy import deepcopy
import json
import pickle
from pathlib import Path
import sys
import types
from enum import Enum
from typing import Annotated, Any, get_args, get_origin
import resource

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deployment"))
sys.path.insert(0, str(ROOT))
# cat_treaty/__init__.py imports FastAPI, unavailable in this Linux container.
# Load the actual backend modules without executing the app initializer.
package = types.ModuleType("cat_treaty")
package.__path__ = [str(ROOT / "cat_treaty")]
sys.modules["cat_treaty"] = package

from measure_local import payload
from cat_treaty.ct6_models import CatalogueRunRequest
from cat_treaty.ct6_orchestration import run_catalogue


def wire_normalizer():
    """Compile the exact CT6 API normalization function without app imports."""
    api = ast.parse((ROOT / "cat_treaty" / "api.py").read_text(encoding="utf-8"))
    functions = [node for node in api.body if isinstance(node, ast.FunctionDef)
                 and node.name == "_normalize_json_value"]
    if len(functions) != 1:
        raise RuntimeError("CT6 wire normalization function changed")
    namespace = {"Any": Any, "Annotated": Annotated, "get_args": get_args,
                 "get_origin": get_origin, "types": types, "Enum": Enum,
                 "BaseModel": BaseModel}
    code = compile(ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[])),
                   str(ROOT / "cat_treaty" / "api.py"), "exec")
    exec(code, namespace)
    return namespace["_normalize_json_value"]


def main():
    scenario = sys.argv[1] if len(sys.argv) == 2 else ""
    if scenario not in {"small", "rows25k", "small_four", "rows25k_four"}:
        raise ValueError("unreviewed fixture")
    trials = 1000 if scenario.startswith("small") else 10000
    rows = None if scenario.startswith("small") else 25000
    raw = payload(trials, sample_cap=10000, detail="full", total_occurrences=rows)
    if len(raw) > 25 * 1024 * 1024:
        raise ValueError("synthetic fixture exceeds CT6 25 MiB body cap")
    wire = json.loads(raw)
    if scenario.endswith("four"):
        program = wire["input"]["program"]
        treaty = wire["input"]["treaty_terms"]
        base_layer = program["layers"][0]
        base_terms = treaty["layer_terms"][0]
        for number in (2, 3, 4):
            layer = deepcopy(base_layer)
            layer["layer_id"] = f"L{number}"
            layer["attachment"] = base_layer["attachment"] + (number - 1) * base_layer["occurrence_limit"]
            terms = deepcopy(base_terms)
            terms["layer_id"] = layer["layer_id"]
            program["layers"].append(layer)
            treaty["layer_terms"].append(terms)
        raw = json.dumps(wire, separators=(",", ":")).encode("utf-8")
        if len(raw) > 25 * 1024 * 1024:
            raise ValueError("four-layer fixture exceeds CT6 25 MiB body cap")
    normalizer = wire_normalizer()
    request = CatalogueRunRequest.model_validate(
        normalizer(CatalogueRunRequest, wire))
    result = run_catalogue(request)
    encoded = pickle.dumps(("ok", result), protocol=5)
    print(json.dumps({"scenario": scenario, "layers": len(request.input.program.layers),
        "trials": trials,
        "occurrences": rows or trials, "request_bytes": len(raw),
        "pickled_result_bytes": len(encoded),
        "child_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)


if __name__ == "__main__":
    main()
