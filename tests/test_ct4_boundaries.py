"""CT4 source, naming and public-contract boundary gates."""

import ast
from pathlib import Path

import cat_treaty


CT4_MODULES = (
    "ct4_models.py",
    "simulation.py",
    "tail.py",
    "frequency.py",
    "occurrence_definition.py",
    "ct4_metadata.py",
    "stability.py",
)


def test_ct4_has_no_pricing_api_or_frontend_dependency() -> None:
    package = Path(cat_treaty.__file__).parent
    forbidden = ("cat_xol", "api", "frontend", "cat_treaty.pricing")
    for filename in CT4_MODULES:
        tree = ast.parse((package / filename).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        assert not any(name.startswith(forbidden) for name in imports), (filename, imports)


def test_ct4_public_contract_exports_final_engines() -> None:
    expected = {
        "apply_catalogue_simulation",
        "calculate_tail_analytics",
        "calculate_frequency_analytics",
        "evaluate_hours_clause_scenario",
        "build_ct4_run_identity",
        "generate_reference_metrics",
        "run_stability_gate",
    }
    assert expected.issubset(cat_treaty.__all__)
    assert all(hasattr(cat_treaty, name) for name in expected)


def test_ct4_source_uses_mandatory_pre_annual_capacity_recovery_name() -> None:
    package = Path(cat_treaty.__file__).parent
    metadata_source = (package / "ct4_metadata.py").read_text(encoding="utf-8")
    assert "gross_contractual_recovery_pre_annual_capacity" in metadata_source
    assert "annual treaty recovery" not in metadata_source.lower()
    assert "net settlement" not in metadata_source.lower()
