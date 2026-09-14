"""CT2 source and CT3 completion-boundary tests."""

import ast
from pathlib import Path

import pytest

from cat_treaty.completion import require_ct3_eligible_waterfall
from cat_treaty.ct2_models import (
    InuringWaterfallInput,
    LossBasisInput,
)
from cat_treaty.inuring import apply_inuring_waterfall
from cat_treaty.loss_basis import build_loss_basis


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CT2_MODULES = (
    PROJECT_ROOT / "cat_treaty" / "ct2_models.py",
    PROJECT_ROOT / "cat_treaty" / "loss_basis.py",
    PROJECT_ROOT / "cat_treaty" / "inuring.py",
    PROJECT_ROOT / "cat_treaty" / "ct2_metadata.py",
    PROJECT_ROOT / "cat_treaty" / "completion.py",
)


def completed_result():
    loss_basis = build_loss_basis(
        LossBasisInput(
            occurrence_id="OCC-GATE",
            reporting_currency="USD",
            source_stage_declaration="insured_loss_after_policy_terms",
            source_reference="scenario",
            initial_insured_loss=1_000.0,
        )
    )
    return apply_inuring_waterfall(
        InuringWaterfallInput(loss_basis=loss_basis)
    )


def test_ct3_gate_accepts_only_completed_waterfall_identity() -> None:
    result = completed_result()

    assert require_ct3_eligible_waterfall(result) is result


@pytest.mark.parametrize("invalid", [1_000.0, {"gross_event_loss": 1_000.0}, None, True])
def test_ct3_gate_rejects_raw_loss_substitutes(invalid: object) -> None:
    with pytest.raises(TypeError, match="completed InuringWaterfallResult"):
        require_ct3_eligible_waterfall(invalid)  # type: ignore[arg-type]


def test_ct2_domain_modules_do_not_import_forbidden_product_engines() -> None:
    forbidden_roots = {"cat_xol", "api", "frontend"}

    for path in CT2_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert imports.isdisjoint(forbidden_roots), (path.name, imports)


def test_ct2_modules_contain_no_user_specific_absolute_paths() -> None:
    for path in CT2_MODULES:
        source = path.read_text(encoding="utf-8").lower()
        assert "c:\\aasif" not in source
        assert "/workspace/" not in source
