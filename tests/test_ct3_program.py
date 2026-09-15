"""F11-F16 CT3 occurrence program recovery tests."""

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
    OverlapCoordination,
    ProgramEligibilityStatus,
)
from cat_treaty.geometry import analyze_program_geometry
from cat_treaty.program import (
    ProgramRecoveryBlockedError,
    calculate_program_recovery,
    evaluate_cat_xl_program,
)
from tests.test_ct3_models import BASIS_INPUT, LAYERS, layer, program


def program_at_loss(loss: float, **changes: object):
    basis_input = replace(BASIS_INPUT, initial_insured_loss=loss)
    basis = LossBasisResult(
        basis_input=basis_input,
        included_additions=0.0,
        applied_deductions=0.0,
        ultimate_net_loss_before_inuring=loss,
        reconciliation_passed=True,
    )
    check = ReconciliationCheck("F09", "F09", loss, loss, True)
    result = InuringWaterfallResult(
        loss_basis=basis,
        cover_results=(),
        total_inuring_recovery=0.0,
        cat_xl_subject_loss=loss,
        completion_status=(
            InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
        ),
        reconciliation_checks=(check,),
        explanation_facts=(),
    )
    waterfall_input = InuringWaterfallInput(loss_basis=basis)
    metadata = build_ct2_run_metadata(
        waterfall_input=waterfall_input,
        source_version="ct2-test",
    )
    return program(ct2_result=result, ct2_metadata=metadata, **changes)


def test_g26_continuous_program_recovery_reconciles_exactly() -> None:
    assessment = evaluate_cat_xl_program(program())
    result = assessment.program_result

    assert result is not None
    assert tuple(
        item.gross_contractual_recovery for item in result.layer_results
    ) == (20_000_000.0, 15_000_000.0)
    assert result.total_gross_contractual_recovery == 35_000_000.0
    assert result.insurer_net_loss == 10_000_000.0
    assert result.base_retention == 10_000_000.0
    assert result.gap_loss == 0.0
    assert result.in_layer_retained_participation == 0.0
    assert result.above_tower_loss == 0.0
    assert len(result.reconciliation_checks) == 3
    assert all(item.passed for item in result.reconciliation_checks)


@pytest.mark.parametrize(
    ("loss", "expected_recovery", "expected_base", "expected_above"),
    [
        (0.0, 0.0, 0.0, 0.0),
        (5_000_000.0, 0.0, 5_000_000.0, 0.0),
        (10_000_000.0, 0.0, 10_000_000.0, 0.0),
        (30_000_000.0, 20_000_000.0, 10_000_000.0, 0.0),
        (60_000_000.0, 50_000_000.0, 10_000_000.0, 0.0),
        (80_000_000.0, 50_000_000.0, 10_000_000.0, 20_000_000.0),
    ],
)
def test_f11_boundaries_and_f16_above_tower_bucket(
    loss: float,
    expected_recovery: float,
    expected_base: float,
    expected_above: float,
) -> None:
    result = calculate_program_recovery(program_at_loss(loss))

    assert result.total_gross_contractual_recovery == expected_recovery
    assert result.base_retention == expected_base
    assert result.above_tower_loss == expected_above
    assert result.insurer_net_loss == loss - expected_recovery


def test_g27_gap_loss_is_retained_and_separately_reconciled() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=20.0),
        layer("L2", attachment=50.0, occurrence_limit=20.0),
    )
    result = calculate_program_recovery(
        program_at_loss(
            60.0,
            layers=layers,
            intentional_gap_acknowledged=True,
        )
    )

    assert result.total_gross_contractual_recovery == 30.0
    assert result.base_retention == 10.0
    assert result.gap_loss == 20.0
    assert result.insurer_net_loss == 30.0
    assert result.warnings


def test_g31_each_layer_applies_separate_ceded_and_placement_shares() -> None:
    layers = (
        replace(LAYERS[0], ceded_share=0.9, placement_share=0.75),
        replace(LAYERS[1], ceded_share=1.0, placement_share=0.5),
    )
    result = calculate_program_recovery(program(layers=layers))

    assert tuple(
        item.gross_contractual_recovery for item in result.layer_results
    ) == (13_500_000.0, 7_500_000.0)
    assert result.total_gross_contractual_recovery == 21_000_000.0
    assert result.in_layer_retained_participation == 14_000_000.0
    assert result.insurer_net_loss == 24_000_000.0


def test_zero_share_layer_retains_its_entire_allocated_band() -> None:
    layers = (replace(LAYERS[0], placement_share=0.0), LAYERS[1])
    result = calculate_program_recovery(program(layers=layers))

    assert result.layer_results[0].gross_contractual_recovery == 0.0
    assert result.layer_results[0].retained_participation == 20_000_000.0
    assert result.total_gross_contractual_recovery == 15_000_000.0


def test_g30_priority_overlap_allocates_each_reached_band_once() -> None:
    layers = (
        layer("L1", attachment=10.0, occurrence_limit=30.0),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    request = program_at_loss(
        45.0,
        layers=layers,
        overlap_coordination=OverlapCoordination.PRIORITY,
        priority_order=("L1", "L2"),
    )
    result = calculate_program_recovery(request)

    first, second = result.layer_results
    assert first.covered_loss_before_coordination == 30.0
    assert first.allocated_covered_loss == 30.0
    assert second.covered_loss_before_coordination == 25.0
    assert second.allocated_covered_loss == 5.0
    assert second.covered_loss_removed_by_coordination == 20.0
    assert second.recovery_before_coordination == 25.0
    assert second.gross_contractual_recovery == 5.0
    assert result.total_gross_contractual_recovery == 35.0
    assert result.insurer_net_loss == 10.0


def test_priority_order_changes_allocation_not_total_covered_union() -> None:
    layers = (
        layer(
            "L1",
            attachment=10.0,
            occurrence_limit=30.0,
            ceded_share=0.5,
        ),
        layer("L2", attachment=20.0, occurrence_limit=30.0),
    )
    first_priority = calculate_program_recovery(
        program_at_loss(
            45.0,
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L1", "L2"),
        )
    )
    second_priority = calculate_program_recovery(
        program_at_loss(
            45.0,
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L2", "L1"),
        )
    )

    assert tuple(item.allocated_covered_loss for item in first_priority.layer_results) == (30.0, 5.0)
    assert tuple(item.allocated_covered_loss for item in second_priority.layer_results) == (10.0, 25.0)
    assert first_priority.total_gross_contractual_recovery == 20.0
    assert second_priority.total_gross_contractual_recovery == 30.0
    assert sum(item.allocated_covered_loss for item in first_priority.layer_results) == 35.0
    assert sum(item.allocated_covered_loss for item in second_priority.layer_results) == 35.0


def test_three_way_overlap_union_is_allocated_only_once() -> None:
    layers = (
        layer("L1", attachment=0.0, occurrence_limit=40.0),
        layer("L2", attachment=10.0, occurrence_limit=40.0),
        layer("L3", attachment=20.0, occurrence_limit=40.0),
    )
    result = calculate_program_recovery(
        program_at_loss(
            55.0,
            layers=layers,
            overlap_coordination=OverlapCoordination.PRIORITY,
            priority_order=("L2", "L3", "L1"),
        )
    )

    by_id = {item.layer_input.layer_id: item for item in result.layer_results}
    assert by_id["L2"].allocated_covered_loss == 40.0
    assert by_id["L3"].allocated_covered_loss == 5.0
    assert by_id["L1"].allocated_covered_loss == 10.0
    assert result.total_gross_contractual_recovery == 55.0
    assert result.insurer_net_loss == 0.0


@pytest.mark.parametrize(
    "scenario",
    [
        program(
            layers=(
                layer("L1", attachment=0.0, occurrence_limit=10.0),
                layer("L2", attachment=20.0, occurrence_limit=10.0),
            )
        ),
        program(
            layers=(
                layer("L1", attachment=0.0, occurrence_limit=20.0),
                layer("L2", attachment=10.0, occurrence_limit=20.0),
            )
        ),
    ],
)
def test_blocked_program_returns_geometry_and_no_recovery(scenario: object) -> None:
    assessment = evaluate_cat_xl_program(scenario)  # type: ignore[arg-type]

    assert assessment.geometry.eligibility_status is ProgramEligibilityStatus.BLOCKED
    assert assessment.geometry.segments
    assert assessment.program_result is None
    with pytest.raises(ProgramRecoveryBlockedError) as error:
        calculate_program_recovery(scenario)  # type: ignore[arg-type]
    assert error.value.geometry == assessment.geometry


def test_external_geometry_must_match_program_request() -> None:
    request = program()
    altered = replace(
        analyze_program_geometry(request),
        notices=("Not part of the authoritative analysis.",),
    )
    with pytest.raises(ValueError, match="does not match"):
        calculate_program_recovery(request, geometry=altered)


def test_layer_result_order_is_geometry_order_not_request_order() -> None:
    result = calculate_program_recovery(program(layers=tuple(reversed(LAYERS))))

    assert tuple(item.layer_input.layer_id for item in result.layer_results) == (
        "L1",
        "L2",
    )
    assert tuple(item.geometry_position for item in result.layer_results) == (1, 2)


def test_explanation_facts_cover_every_reconciliation_driver() -> None:
    result = calculate_program_recovery(program())

    assert {item.metric_name for item in result.explanation_facts} == {
        "total_gross_contractual_recovery",
        "insurer_net_loss",
        "base_retention",
        "gap_loss",
        "in_layer_retained_participation",
        "above_tower_loss",
    }


def test_program_engine_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match="CT3ProgramInput"):
        calculate_program_recovery(object())  # type: ignore[arg-type]
