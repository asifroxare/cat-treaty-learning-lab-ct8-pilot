"""Deterministic CT3 geometry, gap, and overlap eligibility tests."""

from dataclasses import replace

import pytest

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import (
    InuringCompletionStatus,
    InuringWaterfallInput,
    InuringWaterfallResult,
    LossBasisResult,
    ReconciliationCheck,
)
from cat_treaty.ct3_models import (
    BlockingIssueCode,
    GeometryClassification,
    GeometrySegmentType,
    OverlapCoordination,
    ProgramEligibilityStatus,
)
from cat_treaty.geometry import analyze_program_geometry, geometry_order
from tests.test_ct3_models import BASIS_INPUT, LAYERS, layer, program


def issue_codes(result: object) -> tuple[BlockingIssueCode, ...]:
    return tuple(item.code for item in result.blocking_issues)  # type: ignore[attr-defined]


def test_g26_continuous_tower_has_deterministic_segments() -> None:
    result = analyze_program_geometry(program())

    assert result.sorted_layer_ids == ("L1", "L2")
    assert result.boundaries == (10_000_000.0, 30_000_000.0, 60_000_000.0)
    assert result.classification is GeometryClassification.CONTINUOUS
    assert result.eligibility_status is ProgramEligibilityStatus.ELIGIBLE
    assert tuple(item.segment_type for item in result.segments) == (
        GeometrySegmentType.COVERED,
        GeometrySegmentType.COVERED,
    )
    assert tuple(item.layer_ids for item in result.segments) == (("L1",), ("L2",))


def test_single_layer_is_not_treated_as_a_gap_or_overlap() -> None:
    result = analyze_program_geometry(program(layers=(LAYERS[0],)))

    assert result.classification is GeometryClassification.SINGLE_LAYER
    assert result.has_gaps is False
    assert result.has_overlaps is False
    assert len(result.segments) == 1


def test_g27_acknowledged_ventilation_is_eligible_and_warned() -> None:
    layers = (
        layer(occurrence_limit=20_000_000.0),
        layer("L2", attachment=50_000_000.0, occurrence_limit=20_000_000.0),
    )
    result = analyze_program_geometry(
        program(layers=layers, intentional_gap_acknowledged=True)
    )

    assert result.classification is GeometryClassification.VENTILATED
    assert result.eligibility_status is ProgramEligibilityStatus.ELIGIBLE
    gap = result.segments[1]
    assert (gap.start, gap.end) == (30_000_000.0, 50_000_000.0)
    assert gap.segment_type is GeometrySegmentType.GAP
    assert result.warnings == (
        "Intentional ventilation retained from 3e+07 to 5e+07.",
    )


def test_g28_unacknowledged_gap_returns_geometry_and_blocks() -> None:
    layers = (
        layer(occurrence_limit=20_000_000.0),
        layer("L2", attachment=50_000_000.0, occurrence_limit=20_000_000.0),
    )
    result = analyze_program_geometry(program(layers=layers))

    assert result.classification is GeometryClassification.VENTILATED
    assert result.eligibility_status is ProgramEligibilityStatus.BLOCKED
    assert issue_codes(result) == (BlockingIssueCode.UNACKNOWLEDGED_GAP,)
    assert result.blocking_issues[0].affected_segment == (
        30_000_000.0,
        50_000_000.0,
    )
    assert result.segments


def test_each_unacknowledged_gap_has_its_own_structured_issue() -> None:
    layers = (
        layer("L1", attachment=0.0, occurrence_limit=10.0),
        layer("L2", attachment=20.0, occurrence_limit=10.0),
        layer("L3", attachment=40.0, occurrence_limit=10.0),
    )
    result = analyze_program_geometry(program(layers=layers))

    assert tuple(item.affected_segment for item in result.blocking_issues) == (
        (10.0, 20.0),
        (30.0, 40.0),
    )


def test_g29_uncoordinated_overlap_is_classified_and_blocked() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    result = analyze_program_geometry(program(layers=layers))

    assert result.classification is GeometryClassification.OVERLAPPING
    assert result.eligibility_status is ProgramEligibilityStatus.BLOCKED
    assert issue_codes(result) == (BlockingIssueCode.UNCOORDINATED_OVERLAP,)
    assert result.blocking_issues[0].affected_segment == (20.0, 40.0)
    assert result.blocking_issues[0].affected_layer_ids == ("L1", "L2")


def test_complete_priority_makes_overlap_eligible() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    result = analyze_program_geometry(
        program(
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L2", "L1"),
        )
    )

    assert result.classification is GeometryClassification.OVERLAPPING
    assert result.eligibility_status is ProgramEligibilityStatus.ELIGIBLE
    assert result.priority_order == ("L2", "L1")


@pytest.mark.parametrize(
    "priority_order",
    [("L1",), ("L1", "UNKNOWN")],
)
def test_incomplete_or_unknown_priority_blocks_with_stable_code(
    priority_order: tuple[str, ...],
) -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    result = analyze_program_geometry(
        program(
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=priority_order,
        )
    )

    assert issue_codes(result) == (BlockingIssueCode.INVALID_PRIORITY_ORDER,)
    assert result.blocking_issues[0].affected_layer_ids == ("L1", "L2")


def test_priority_coordination_without_overlap_is_blocked_as_misleading() -> None:
    result = analyze_program_geometry(
        program(
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L1", "L2"),
        )
    )

    assert result.classification is GeometryClassification.CONTINUOUS
    assert issue_codes(result) == (
        BlockingIssueCode.UNNECESSARY_PRIORITY_COORDINATION,
    )


def test_mixed_topology_discloses_gap_and_overlap_independently() -> None:
    layers = (
        layer("L1", attachment=0.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=20.0),
        layer("L3", attachment=50.0, occurrence_limit=10.0),
    )
    result = analyze_program_geometry(program(layers=layers))

    assert result.classification is GeometryClassification.MIXED
    assert result.has_gaps and result.has_overlaps
    assert issue_codes(result) == (
        BlockingIssueCode.UNACKNOWLEDGED_GAP,
        BlockingIssueCode.UNCOORDINATED_OVERLAP,
    )


def test_acknowledgement_without_gap_is_a_notice_not_a_failure() -> None:
    result = analyze_program_geometry(
        program(intentional_gap_acknowledged=True)
    )

    assert result.eligibility_status is ProgramEligibilityStatus.ELIGIBLE
    assert len(result.notices) == 1
    assert result.warnings == ()


def test_geometry_order_uses_attachment_exhaustion_then_id() -> None:
    layers = (
        layer("Z", attachment=10.0, occurrence_limit=20.0),
        layer("B", attachment=10.0, occurrence_limit=10.0),
        layer("A", attachment=10.0, occurrence_limit=10.0),
    )
    assert tuple(item.layer_id for item in geometry_order(layers)) == (
        "A",
        "B",
        "Z",
    )


def test_request_permutation_cannot_change_geometry() -> None:
    first = analyze_program_geometry(program(layers=LAYERS))
    second = analyze_program_geometry(program(layers=tuple(reversed(LAYERS))))

    assert first == second


def test_contract_geometry_is_independent_of_current_subject_loss() -> None:
    zero_basis_input = replace(
        BASIS_INPUT,
        initial_insured_loss=0.0,
    )
    zero_basis = LossBasisResult(
        basis_input=zero_basis_input,
        included_additions=0.0,
        applied_deductions=0.0,
        ultimate_net_loss_before_inuring=0.0,
        reconciliation_passed=True,
    )
    zero_check = ReconciliationCheck("F09-zero", "F09", 0.0, 0.0, True)
    zero_result = InuringWaterfallResult(
        loss_basis=zero_basis,
        cover_results=(),
        total_inuring_recovery=0.0,
        cat_xl_subject_loss=0.0,
        completion_status=(
            InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
        ),
        reconciliation_checks=(zero_check,),
        explanation_facts=(),
    )
    zero_input = InuringWaterfallInput(loss_basis=zero_basis)
    zero_metadata = build_ct2_run_metadata(
        waterfall_input=zero_input,
        source_version="ct2-test",
    )
    zero_program = program(
        ct2_result=zero_result,
        ct2_metadata=zero_metadata,
    )

    assert analyze_program_geometry(zero_program) == analyze_program_geometry(
        program()
    )


def test_geometry_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="CT3ProgramInput"):
        analyze_program_geometry(object())  # type: ignore[arg-type]
