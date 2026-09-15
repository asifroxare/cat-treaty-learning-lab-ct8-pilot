"""CT3 occurrence Cat XL program recovery and reconciliation engine."""

import math

from cat_treaty.ct2_models import ExplanationFact, ReconciliationCheck
from cat_treaty.ct3_models import (
    CatLayerInput,
    CatLayerResult,
    CT3AssessmentResult,
    CT3ProgramInput,
    CT3ProgramResult,
    GeometrySegmentType,
    OverlapCoordination,
    ProgramEligibilityStatus,
    ProgramGeometry,
)
from cat_treaty.geometry import analyze_program_geometry, geometry_order


class ProgramRecoveryBlockedError(ValueError):
    """Raised when recovery is requested for contractually blocked geometry."""

    def __init__(self, geometry: ProgramGeometry) -> None:
        self.geometry = geometry
        codes = ", ".join(item.code.value for item in geometry.blocking_issues)
        super().__init__(f"program recovery is blocked: {codes}")


def evaluate_cat_xl_program(
    program_input: CT3ProgramInput,
    *,
    source_version: str,
) -> CT3AssessmentResult:
    """Return one authoritative eligible or blocked CT3 assessment."""

    geometry = analyze_program_geometry(program_input)
    from cat_treaty.ct3_metadata import build_ct3_run_metadata

    metadata = build_ct3_run_metadata(
        program_input=program_input,
        source_version=source_version,
    )
    if geometry.eligibility_status is ProgramEligibilityStatus.BLOCKED:
        return CT3AssessmentResult(
            program_input=program_input,
            geometry=geometry,
            metadata=metadata,
            program_result=None,
        )
    result = calculate_program_recovery(program_input, geometry=geometry)
    return CT3AssessmentResult(program_input, geometry, metadata, result)


def calculate_program_recovery(
    program_input: CT3ProgramInput,
    *,
    geometry: ProgramGeometry | None = None,
) -> CT3ProgramResult:
    """Apply F11-F16 to one program whose geometry is eligible."""

    if not isinstance(program_input, CT3ProgramInput):
        raise TypeError("program_input must be CT3ProgramInput")
    analysed = (
        analyze_program_geometry(program_input)
        if geometry is None
        else geometry
    )
    if not isinstance(analysed, ProgramGeometry):
        raise TypeError("geometry must be ProgramGeometry")
    expected_geometry = analyze_program_geometry(program_input)
    if analysed != expected_geometry:
        raise ValueError("geometry does not match program_input")
    if analysed.eligibility_status is ProgramEligibilityStatus.BLOCKED:
        raise ProgramRecoveryBlockedError(analysed)

    subject_loss = float(program_input.ct2_result.cat_xl_subject_loss)
    ordered_layers = geometry_order(program_input.layers)
    allocated = _allocated_covered_losses(
        layers=ordered_layers,
        subject_loss=subject_loss,
        coordination=program_input.overlap_coordination,
        priority_order=program_input.priority_order,
    )
    priority_positions = (
        {
            layer_id: position
            for position, layer_id in enumerate(
                program_input.priority_order or (),
                start=1,
            )
        }
        if program_input.overlap_coordination is OverlapCoordination.PRIORITY
        else {}
    )
    layer_results = tuple(
        _build_layer_result(
            layer=layer,
            geometry_position=position,
            priority_position=priority_positions.get(layer.layer_id),
            subject_loss=subject_loss,
            allocated_covered_loss=allocated[layer.layer_id],
        )
        for position, layer in enumerate(ordered_layers, start=1)
    )

    recovery = math.fsum(
        item.gross_contractual_recovery for item in layer_results
    )
    insurer_net = subject_loss - recovery
    base_retention = min(subject_loss, float(ordered_layers[0].attachment))
    gap_loss = math.fsum(
        _reached_interval_measure(subject_loss, segment.start, segment.end)
        for segment in analysed.segments
        if segment.segment_type is GeometrySegmentType.GAP
    )
    above_tower = max(
        subject_loss - max(float(item.exhaustion) for item in ordered_layers),
        0.0,
    )
    in_layer_retention = math.fsum(
        item.retained_participation for item in layer_results
    )
    allocated_total = math.fsum(
        item.allocated_covered_loss for item in layer_results
    )

    checks = (
        _check("F15-loss", "F15", subject_loss, recovery + insurer_net),
        _check(
            "F16-loss-bands",
            "F16",
            subject_loss,
            base_retention + gap_loss + allocated_total + above_tower,
        ),
        _check(
            "F16-retained-buckets",
            "F16",
            insurer_net,
            base_retention + gap_loss + in_layer_retention + above_tower,
        ),
    )
    facts = _explanation_facts(
        recovery=recovery,
        insurer_net=insurer_net,
        base_retention=base_retention,
        gap_loss=gap_loss,
        in_layer_retention=in_layer_retention,
        above_tower=above_tower,
    )
    assumptions = (
        "CT3 evaluates one completed occurrence and applies no annual capacity.",
        "Ceded share and placement share are applied separately by layer.",
    )

    return CT3ProgramResult(
        program_input=program_input,
        geometry=analysed,
        layer_results=layer_results,
        total_gross_contractual_recovery=recovery,
        insurer_net_loss=insurer_net,
        base_retention=base_retention,
        gap_loss=gap_loss,
        in_layer_retained_participation=in_layer_retention,
        above_tower_loss=above_tower,
        reconciliation_checks=checks,
        explanation_facts=facts,
        warnings=analysed.warnings,
        assumption_disclosures=assumptions,
    )


def _covered_loss(layer: CatLayerInput, subject_loss: float) -> float:
    return min(
        max(subject_loss - float(layer.attachment), 0.0),
        float(layer.occurrence_limit),
    )


def _allocated_covered_losses(
    *,
    layers: tuple[CatLayerInput, ...],
    subject_loss: float,
    coordination: OverlapCoordination,
    priority_order: tuple[str, ...] | None,
) -> dict[str, float]:
    if coordination is OverlapCoordination.NONE:
        return {
            layer.layer_id: _covered_loss(layer, subject_loss)
            for layer in layers
        }

    by_id = {item.layer_id: item for item in layers}
    prior_intervals: list[tuple[float, float]] = []
    allocated: dict[str, float] = {}
    for layer_id in priority_order or ():
        layer = by_id[layer_id]
        start = float(layer.attachment)
        end = min(float(layer.exhaustion), subject_loss)
        if end <= start:
            allocated[layer_id] = 0.0
            continue
        allocated[layer_id] = _uncovered_measure(start, end, prior_intervals)
        prior_intervals.append((start, end))
    return allocated


def _uncovered_measure(
    start: float,
    end: float,
    prior_intervals: list[tuple[float, float]],
) -> float:
    clipped = sorted(
        (
            max(start, prior_start),
            min(end, prior_end),
        )
        for prior_start, prior_end in prior_intervals
        if min(end, prior_end) > max(start, prior_start)
    )
    covered = 0.0
    merged_end = start
    for overlap_start, overlap_end in clipped:
        if overlap_end <= merged_end:
            continue
        covered += overlap_end - max(overlap_start, merged_end)
        merged_end = overlap_end
    return max((end - start) - covered, 0.0)


def _build_layer_result(
    *,
    layer: CatLayerInput,
    geometry_position: int,
    priority_position: int | None,
    subject_loss: float,
    allocated_covered_loss: float,
) -> CatLayerResult:
    covered = _covered_loss(layer, subject_loss)
    factor = float(layer.ceded_share) * float(layer.placement_share)
    recovery_before = covered * factor
    recovery = allocated_covered_loss * factor
    return CatLayerResult(
        layer_input=layer,
        geometry_position=geometry_position,
        priority_position=priority_position,
        covered_loss_before_coordination=covered,
        allocated_covered_loss=allocated_covered_loss,
        covered_loss_removed_by_coordination=covered - allocated_covered_loss,
        recovery_before_coordination=recovery_before,
        gross_contractual_recovery=recovery,
        retained_participation=allocated_covered_loss - recovery,
        attachment_reached=subject_loss >= float(layer.attachment),
        exhaustion_reached=subject_loss >= float(layer.exhaustion),
        trace_references=("F11", "F12", "F13", "F14"),
    )


def _reached_interval_measure(subject_loss: float, start: float, end: float) -> float:
    return max(min(subject_loss, end) - start, 0.0)


def _check(
    check_id: str,
    formula_reference: str,
    left_value: float,
    right_value: float,
) -> ReconciliationCheck:
    return ReconciliationCheck(
        check_id=check_id,
        formula_reference=formula_reference,
        left_value=left_value,
        right_value=right_value,
        passed=math.isclose(
            left_value,
            right_value,
            rel_tol=1e-12,
            abs_tol=1e-6,
        ),
    )


def _explanation_facts(
    *,
    recovery: float,
    insurer_net: float,
    base_retention: float,
    gap_loss: float,
    in_layer_retention: float,
    above_tower: float,
) -> tuple[ExplanationFact, ...]:
    values = (
        ("total_gross_contractual_recovery", recovery, "F15"),
        ("insurer_net_loss", insurer_net, "F15"),
        ("base_retention", base_retention, "F16"),
        ("gap_loss", gap_loss, "F16"),
        ("in_layer_retained_participation", in_layer_retention, "F16"),
        ("above_tower_loss", above_tower, "F16"),
    )
    return tuple(
        ExplanationFact(
            metric_name=name,
            value=value,
            meaning=name.replace("_", " ").capitalize(),
            driver_statement=(
                f"This retained or recovered bucket contributes {value:g} "
                "to the occurrence reconciliation."
            ),
            trace_reference=trace,
        )
        for name, value, trace in values
    )
