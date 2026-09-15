"""Consolidated CT3 golden-case acceptance and milestone traceability."""

from dataclasses import replace

import pytest

from cat_treaty.ct3_metadata import serialize_ct3_inputs
from cat_treaty.ct3_models import (
    BlockingIssueCode,
    GeometryClassification,
    OverlapCoordination,
    ProgramEligibilityStatus,
)
from cat_treaty.program import evaluate_cat_xl_program
from tests.test_ct3_models import LAYERS, layer, program
from tests.test_ct3_program import program_at_loss


SOURCE_VERSION = "ct3-golden"


def evaluate(request):
    return evaluate_cat_xl_program(request, source_version=SOURCE_VERSION)


def test_ct0_to_ct3_golden_case_register_has_no_gaps_or_collisions() -> None:
    owners = {
        **{f"G{number:02d}": "CT1/CT3" for number in range(1, 6)},
        "G06": "CT2",
        **{f"G{number:02d}": "later" for number in range(7, 10)},
        "G10": "CT3",
        **{f"G{number:02d}": "later" for number in range(11, 14)},
        **{f"G{number:02d}": "CT1" for number in range(14, 17)},
        **{f"G{number:02d}": "CT2" for number in range(17, 26)},
        **{f"G{number:02d}": "CT3" for number in range(26, 35)},
    }

    assert set(owners) == {f"G{number:02d}" for number in range(1, 35)}
    assert {case_id for case_id, owner in owners.items() if "CT3" in owner} == {
        "G01", "G02", "G03", "G04", "G05", "G10",
        *{f"G{number:02d}" for number in range(26, 35)},
    }


def test_g01_loss_below_attachment() -> None:
    result = evaluate(program_at_loss(5.0, layers=(layer(attachment=10.0, occurrence_limit=20.0),))).program_result
    assert result is not None
    assert result.total_gross_contractual_recovery == 0.0
    assert result.insurer_net_loss == 5.0


def test_g02_loss_exactly_at_attachment() -> None:
    result = evaluate(program_at_loss(10.0, layers=(layer(attachment=10.0, occurrence_limit=20.0),))).program_result
    assert result is not None
    assert result.layer_results[0].covered_loss_before_coordination == 0.0
    assert result.total_gross_contractual_recovery == 0.0


def test_g03_partial_layer_loss_with_ninety_percent_share() -> None:
    treaty_layer = layer(
        attachment=10.0,
        occurrence_limit=20.0,
        ceded_share=0.9,
        placement_share=1.0,
    )
    result = evaluate(program_at_loss(20.0, layers=(treaty_layer,))).program_result
    assert result is not None
    assert result.layer_results[0].covered_loss_before_coordination == 10.0
    assert result.total_gross_contractual_recovery == 9.0
    assert result.in_layer_retained_participation == 1.0


def test_g04_loss_exactly_at_exhaustion() -> None:
    result = evaluate(program_at_loss(30.0, layers=(layer(attachment=10.0, occurrence_limit=20.0),))).program_result
    assert result is not None
    assert result.total_gross_contractual_recovery == 20.0
    assert result.layer_results[0].exhaustion_reached is True


def test_g05_loss_above_tower() -> None:
    result = evaluate(program_at_loss(40.0, layers=(layer(attachment=10.0, occurrence_limit=20.0),))).program_result
    assert result is not None
    assert result.total_gross_contractual_recovery == 20.0
    assert result.above_tower_loss == 10.0


def test_g10_ventilated_program_retains_and_discloses_gap_loss() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=20.0),
        layer("L2", attachment=50.0, occurrence_limit=20.0),
    )
    result = evaluate(
        program_at_loss(60.0, layers=layers, intentional_gap_acknowledged=True)
    )
    assert result.geometry.classification is GeometryClassification.VENTILATED
    assert result.program_result is not None
    assert result.program_result.gap_loss == 20.0


def test_g26_continuous_usd_45m_example() -> None:
    result = evaluate(program()).program_result
    assert result is not None
    assert tuple(item.gross_contractual_recovery for item in result.layer_results) == (20_000_000.0, 15_000_000.0)
    assert result.total_gross_contractual_recovery == 35_000_000.0
    assert result.insurer_net_loss == 10_000_000.0


def test_g27_intentional_ventilation() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=20.0),
        layer("L2", attachment=50.0, occurrence_limit=20.0),
    )
    assessment = evaluate(
        program_at_loss(55.0, layers=layers, intentional_gap_acknowledged=True)
    )
    assert assessment.geometry.eligibility_status is ProgramEligibilityStatus.ELIGIBLE
    assert assessment.geometry.segments[1].start == 30.0
    assert assessment.geometry.segments[1].end == 50.0
    assert assessment.program_result is not None
    assert assessment.program_result.gap_loss == 20.0


def test_g28_unacknowledged_gap_blocks_but_returns_geometry() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=20.0),
        layer("L2", attachment=50.0, occurrence_limit=20.0),
    )
    assessment = evaluate(program_at_loss(55.0, layers=layers))
    assert assessment.geometry.classification is GeometryClassification.VENTILATED
    assert assessment.geometry.blocking_issues[0].code is BlockingIssueCode.UNACKNOWLEDGED_GAP
    assert assessment.program_result is None


def test_g29_ambiguous_overlap_blocks_with_segment_and_layers() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    assessment = evaluate(program_at_loss(45.0, layers=layers))
    issue = assessment.geometry.blocking_issues[0]
    assert assessment.geometry.classification is GeometryClassification.OVERLAPPING
    assert issue.code is BlockingIssueCode.UNCOORDINATED_OVERLAP
    assert issue.affected_segment == (20.0, 40.0)
    assert issue.affected_layer_ids == ("L1", "L2")
    assert assessment.program_result is None


def test_g30_priority_overlap_allocates_band_once() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    result = evaluate(
        program_at_loss(
            45.0,
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L1", "L2"),
        )
    ).program_result
    assert result is not None
    assert tuple(item.allocated_covered_loss for item in result.layer_results) == (30.0, 5.0)
    assert tuple(item.recovery_before_coordination for item in result.layer_results) == (30.0, 25.0)
    assert tuple(item.gross_contractual_recovery for item in result.layer_results) == (30.0, 5.0)


def test_g31_different_layer_shares() -> None:
    layers = (
        replace(LAYERS[0], ceded_share=0.9, placement_share=0.75),
        replace(LAYERS[1], ceded_share=1.0, placement_share=0.5),
    )
    result = evaluate(program(layers=layers)).program_result
    assert result is not None
    assert tuple(item.gross_contractual_recovery for item in result.layer_results) == (13_500_000.0, 7_500_000.0)


def test_g32_request_order_permutation_is_identical() -> None:
    first_request = program(layers=LAYERS)
    second_request = program(layers=tuple(reversed(LAYERS)))
    first = evaluate(first_request)
    second = evaluate(second_request)

    assert serialize_ct3_inputs(first_request) == serialize_ct3_inputs(second_request)
    assert first.metadata.input_hash == second.metadata.input_hash
    assert first.geometry == second.geometry
    assert first.program_result is not None and second.program_result is not None
    assert first.program_result.layer_results == second.program_result.layer_results


def test_g33_zero_subject_loss_preserves_contract_geometry() -> None:
    assessment = evaluate(program_at_loss(0.0))
    result = assessment.program_result
    assert result is not None
    assert assessment.geometry.boundaries == (10_000_000.0, 30_000_000.0, 60_000_000.0)
    assert all(item.gross_contractual_recovery == 0.0 for item in result.layer_results)
    assert result.insurer_net_loss == 0.0
    assert result.base_retention == result.gap_loss == result.above_tower_loss == 0.0


def test_g34_ct2_entry_gate_rejects_raw_loss_substitutes() -> None:
    for raw in (45_000_000.0, {"gross_event_loss": 45_000_000.0}):
        with pytest.raises(ValueError, match="InuringWaterfallResult"):
            program(ct2_result=raw)
