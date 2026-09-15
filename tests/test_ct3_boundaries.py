"""CT3 source-boundary, packaging, and public-contract tests."""

import ast
from pathlib import Path

import cat_treaty


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CT3_MODULES = (
    PROJECT_ROOT / "cat_treaty" / "ct3_models.py",
    PROJECT_ROOT / "cat_treaty" / "geometry.py",
    PROJECT_ROOT / "cat_treaty" / "program.py",
    PROJECT_ROOT / "cat_treaty" / "ct3_metadata.py",
)


def test_ct3_domain_modules_do_not_import_forbidden_product_engines() -> None:
    forbidden_roots = {"cat_xol", "api", "frontend"}

    for path in CT3_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert imports.isdisjoint(forbidden_roots), (path.name, imports)


def test_ct3_modules_contain_no_user_specific_absolute_paths() -> None:
    for path in CT3_MODULES:
        source = path.read_text(encoding="utf-8").lower()
        assert "c:\\aasif" not in source
        assert "/workspace/" not in source


def test_ct3_public_package_exports_are_complete() -> None:
    expected = {
        "CT3_ENGINE_VERSION",
        "CT3_SCHEMA_VERSION",
        "CT3RunMetadata",
        "CT3ProgramInput",
        "CT3ProgramResult",
        "CT3AssessmentResult",
        "CatLayerInput",
        "CatLayerResult",
        "ProgramGeometry",
        "GeometryClassification",
        "GeometrySegment",
        "GeometrySegmentType",
        "ProgramEligibilityStatus",
        "BlockingIssue",
        "BlockingIssueCode",
        "OverlapCoordination",
        "analyze_program_geometry",
        "geometry_order",
        "calculate_program_recovery",
        "evaluate_cat_xl_program",
        "build_ct3_run_metadata",
        "canonicalize_ct3_inputs",
        "serialize_ct3_inputs",
    }

    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, name) for name in expected)
