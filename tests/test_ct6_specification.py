"""Structural freeze gate for the CT6 review specification."""

from pathlib import Path


SPEC = Path(__file__).resolve().parents[1] / "docs" / "CT6_IMPLEMENTATION_SPEC.md"


def test_ct6_review_spec_contains_required_contract_boundaries() -> None:
    text = SPEC.read_text(encoding="utf-8")
    for required in (
        "Version:** 0.9-review",
        "implementation is not authorized",
        "No actuarial formula may be implemented",
        "POST | `/api/v1/runs/catalogue`",
        "POST | `/api/v1/runs/hours-clause`",
        "CT6_DOMAIN_VALIDATION",
        "G69",
        "G82",
        "Questions for independent validation",
    ):
        assert required in text


def test_ct6_review_spec_preserves_ct5_three_way_settlement() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "gross contractual recovery" in text
    assert "reinstatement premium payable" in text
    assert "net cash settlement" in text
    assert "pre-capacity" in text
    assert "post-capacity" in text
