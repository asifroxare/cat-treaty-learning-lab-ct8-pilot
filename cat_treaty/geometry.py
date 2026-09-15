"""Deterministic CT3 layer geometry and contractual eligibility analysis."""

from collections.abc import Iterable

from cat_treaty.ct3_models import (
    BlockingIssue,
    BlockingIssueCode,
    CatLayerInput,
    CT3ProgramInput,
    GeometryClassification,
    GeometrySegment,
    GeometrySegmentType,
    OverlapCoordination,
    ProgramEligibilityStatus,
    ProgramGeometry,
)


def geometry_order(layers: Iterable[CatLayerInput]) -> tuple[CatLayerInput, ...]:
    """Return layers in frozen attachment/exhaustion/ID order."""

    materialized = tuple(layers)
    if not all(isinstance(item, CatLayerInput) for item in materialized):
        raise TypeError("layers must contain CatLayerInput values")
    return tuple(
        sorted(
            materialized,
            key=lambda item: (
                float(item.attachment),
                float(item.exhaustion),
                item.layer_id,
            ),
        )
    )


def analyze_program_geometry(program_input: CT3ProgramInput) -> ProgramGeometry:
    """Build finite segments, classify topology, and determine eligibility."""

    if not isinstance(program_input, CT3ProgramInput):
        raise TypeError("program_input must be CT3ProgramInput")

    ordered_layers = geometry_order(program_input.layers)
    sorted_layer_ids = tuple(item.layer_id for item in ordered_layers)
    boundaries = tuple(
        sorted(
            {
                float(boundary)
                for layer in ordered_layers
                for boundary in (layer.attachment, layer.exhaustion)
            }
        )
    )
    segments = tuple(
        _build_segment(start, end, ordered_layers)
        for start, end in zip(boundaries, boundaries[1:], strict=False)
    )
    has_gaps = any(
        item.segment_type is GeometrySegmentType.GAP for item in segments
    )
    has_overlaps = any(
        item.segment_type is GeometrySegmentType.OVERLAP for item in segments
    )
    classification = _classify(len(ordered_layers), has_gaps, has_overlaps)
    issues = _blocking_issues(
        program_input=program_input,
        segments=segments,
        sorted_layer_ids=sorted_layer_ids,
        has_gaps=has_gaps,
        has_overlaps=has_overlaps,
    )
    notices = _notices(program_input, has_gaps)
    warnings = _warnings(program_input, segments)

    return ProgramGeometry(
        sorted_layer_ids=sorted_layer_ids,
        boundaries=boundaries,
        classification=classification,
        has_gaps=has_gaps,
        has_overlaps=has_overlaps,
        segments=segments,
        intentional_gap_acknowledged=(
            program_input.intentional_gap_acknowledged
        ),
        overlap_coordination=program_input.overlap_coordination,
        priority_order=program_input.priority_order,
        eligibility_status=(
            ProgramEligibilityStatus.BLOCKED
            if issues
            else ProgramEligibilityStatus.ELIGIBLE
        ),
        blocking_issues=issues,
        notices=notices,
        warnings=warnings,
    )


def _build_segment(
    start: float,
    end: float,
    ordered_layers: tuple[CatLayerInput, ...],
) -> GeometrySegment:
    layer_ids = tuple(
        layer.layer_id
        for layer in ordered_layers
        if float(layer.attachment) <= start and float(layer.exhaustion) >= end
    )
    if not layer_ids:
        segment_type = GeometrySegmentType.GAP
    elif len(layer_ids) == 1:
        segment_type = GeometrySegmentType.COVERED
    else:
        segment_type = GeometrySegmentType.OVERLAP
    return GeometrySegment(start, end, segment_type, layer_ids)


def _classify(
    layer_count: int,
    has_gaps: bool,
    has_overlaps: bool,
) -> GeometryClassification:
    if layer_count == 1:
        return GeometryClassification.SINGLE_LAYER
    if has_gaps and has_overlaps:
        return GeometryClassification.MIXED
    if has_gaps:
        return GeometryClassification.VENTILATED
    if has_overlaps:
        return GeometryClassification.OVERLAPPING
    return GeometryClassification.CONTINUOUS


def _blocking_issues(
    *,
    program_input: CT3ProgramInput,
    segments: tuple[GeometrySegment, ...],
    sorted_layer_ids: tuple[str, ...],
    has_gaps: bool,
    has_overlaps: bool,
) -> tuple[BlockingIssue, ...]:
    issues: list[BlockingIssue] = []

    if has_gaps and not program_input.intentional_gap_acknowledged:
        issues.extend(
            BlockingIssue(
                code=BlockingIssueCode.UNACKNOWLEDGED_GAP,
                affected_segment=(segment.start, segment.end),
                affected_layer_ids=(),
                message=(
                    "Internal program gap requires explicit intentional-gap "
                    "acknowledgement before recovery."
                ),
                rule_reference="CT3-section-8",
            )
            for segment in segments
            if segment.segment_type is GeometrySegmentType.GAP
        )

    if has_overlaps:
        if program_input.overlap_coordination is OverlapCoordination.NONE:
            issues.extend(
                BlockingIssue(
                    code=BlockingIssueCode.UNCOORDINATED_OVERLAP,
                    affected_segment=(segment.start, segment.end),
                    affected_layer_ids=segment.layer_ids,
                    message=(
                        "Overlapping loss band requires an explicit frozen "
                        "coordination rule before recovery."
                    ),
                    rule_reference="CT3-section-9",
                )
                for segment in segments
                if segment.segment_type is GeometrySegmentType.OVERLAP
            )
        elif not _is_complete_priority(
            program_input.priority_order,
            sorted_layer_ids,
        ):
            issues.append(
                BlockingIssue(
                    code=BlockingIssueCode.INVALID_PRIORITY_ORDER,
                    affected_segment=None,
                    affected_layer_ids=sorted_layer_ids,
                    message=(
                        "Priority order must contain every program layer ID "
                        "exactly once and no unknown IDs."
                    ),
                    rule_reference="CT3-section-9",
                )
            )
    elif program_input.overlap_coordination is OverlapCoordination.PRIORITY:
        issues.append(
            BlockingIssue(
                code=BlockingIssueCode.UNNECESSARY_PRIORITY_COORDINATION,
                affected_segment=None,
                affected_layer_ids=sorted_layer_ids,
                message=(
                    "Priority coordination is not permitted when the program "
                    "contains no overlapping segment."
                ),
                rule_reference="CT3-section-9",
            )
        )

    return tuple(issues)


def _is_complete_priority(
    priority_order: tuple[str, ...] | None,
    sorted_layer_ids: tuple[str, ...],
) -> bool:
    return (
        priority_order is not None
        and len(priority_order) == len(sorted_layer_ids)
        and set(priority_order) == set(sorted_layer_ids)
    )


def _notices(
    program_input: CT3ProgramInput,
    has_gaps: bool,
) -> tuple[str, ...]:
    if program_input.intentional_gap_acknowledged and not has_gaps:
        return (
            "Intentional-gap acknowledgement was supplied but no internal "
            "program gap exists.",
        )
    return ()


def _warnings(
    program_input: CT3ProgramInput,
    segments: tuple[GeometrySegment, ...],
) -> tuple[str, ...]:
    if not program_input.intentional_gap_acknowledged:
        return ()
    return tuple(
        f"Intentional ventilation retained from {segment.start:g} to {segment.end:g}."
        for segment in segments
        if segment.segment_type is GeometrySegmentType.GAP
    )
