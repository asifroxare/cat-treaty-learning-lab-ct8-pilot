"""Structural freeze gate for the CT6 review specification."""

from pathlib import Path


SPEC = Path(__file__).resolve().parents[1] / "docs" / "CT6_IMPLEMENTATION_SPEC.md"


def test_ct6_review_spec_contains_required_contract_boundaries() -> None:
    text = SPEC.read_text(encoding="utf-8")
    for required in (
        "Version:** 1.0",
        "Frozen after independent validation",
        "No actuarial formula may be implemented",
        "POST | `/api/v1/runs/catalogue`",
        "POST | `/api/v1/runs/hours-clause`",
        "CT6_DOMAIN_VALIDATION",
        "G69",
        "G82",
        "G83",
        "Frozen independent-review decisions",
        "catalogue_source_mode",
        "Validation/status precedence is frozen",
        "gross_contractual_recovery_pre_annual_capacity",
    ):
        assert required in text


def test_ct6_review_spec_preserves_ct5_three_way_settlement() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "gross contractual recovery" in text
    assert "reinstatement premium payable" in text
    assert "net cash settlement" in text
    assert "pre-capacity" in text
    assert "post-capacity" in text


def test_ct6_review_findings_are_disposed_without_open_questions() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "## 23. Questions for independent validation" not in text
    assert "1–10,000" in text
    assert "0–100,000" in text
    assert "selected from a reviewed static" in text
    assert "message catalogue keyed by stable error code" in text
    assert "For hours-clause mode the orchestrator performs exactly" in text
