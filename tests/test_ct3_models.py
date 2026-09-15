"""Validation tests for immutable CT3 program domain models."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import (
    ExplanationFact,
    InuringCompletionStatus,
    InuringWaterfallInput,
    InuringWaterfallResult,
    LossBasisInput,
    LossBasisResult,
    ReconciliationCheck,
)
from cat_treaty.ct3_models import (
    BlockingIssue,
    BlockingIssueCode,
    CatLayerInput,
    CatLayerResult,
    CT3AssessmentResult,
    CT3ProgramInput,
    CT3ProgramResult,
    GeometryClassification,
    GeometrySegment,
    GeometrySegmentType,
    OverlapCoordination,
    ProgramEligibilityStatus,
    ProgramGeometry,
)


BASIS_INPUT = LossBasisInput(
    occurrence_id="OCC-CT3",
    reporting_currency="USD",
    source_stage_declaration="insured_loss_after_policy_terms",
    source_reference="catalogue:ct3",
    initial_insured_loss=45_000_000.0,
)
BASIS_RESULT = LossBasisResult(
    basis_input=BASIS_INPUT,
    included_additions=0.0,
    applied_deductions=0.0,
    ultimate_net_loss_before_inuring=45_000_000.0,
    reconciliation_passed=True,
)
CT2_CHECK = ReconciliationCheck(
    check_id="F09",
    formula_reference="F09",
    left_value=45_000_000.0,
    right_value=45_000_000.0,
    passed=True,
)
CT2_RESULT = InuringWaterfallResult(
    loss_basis=BASIS_RESULT,
    cover_results=(),
    total_inuring_recovery=0.0,
    cat_xl_subject_loss=45_000_000.0,
    completion_status=InuringCompletionStatus.COMPLETE_NO_INURING_COVERS,
    reconciliation_checks=(CT2_CHECK,),
    explanation_facts=(),
)
CT2_INPUT = InuringWaterfallInput(loss_basis=BASIS_RESULT)
CT2_METADATA = build_ct2_run_metadata(
    waterfall_input=CT2_INPUT,
    source_version="ct2-test",
)


def layer(layer_id: str = "L1", **changes: object) -> CatLayerInput:
    values: dict[str, object] = {
        "layer_id": layer_id,
        "attachment": 10_000_000.0,
        "occurrence_limit": 20_000_000.0,
        "ceded_share": 1.0,
        "placement_share": 1.0,
        "currency": "USD",
        "description": "Occurrence layer",
        "source_reference": "slip:1",
        "rule_reference": "F10-F11",
    }
    values.update(changes)
    return CatLayerInput(**values)


LAYERS = (
    layer(),
    layer("L2", attachment=30_000_000.0, occurrence_limit=30_000_000.0),
)


def program(**changes: object) -> CT3ProgramInput:
    values: dict[str, object] = {
        "program_id": "PROGRAM-1",
        "ct2_result": CT2_RESULT,
        "ct2_metadata": CT2_METADATA,
        "layers": LAYERS,
        "intentional_gap_acknowledged": False,
        "overlap_coordination": OverlapCoordination.NONE,
        "priority_order": None,
        "description": "Continuous two-layer tower",
        "source_reference": "slip:program",
        "rule_reference": "CT3",
    }
    values.update(changes)
    return CT3ProgramInput(**values)


SEGMENTS = (
    GeometrySegment(10_000_000.0, 30_000_000.0, GeometrySegmentType.COVERED, ("L1",)),
    GeometrySegment(30_000_000.0, 60_000_000.0, GeometrySegmentType.COVERED, ("L2",)),
)


def geometry(**changes: object) -> ProgramGeometry:
    values: dict[str, object] = {
        "sorted_layer_ids": ("L1", "L2"),
        "boundaries": (10_000_000.0, 30_000_000.0, 60_000_000.0),
        "classification": GeometryClassification.CONTINUOUS,
        "has_gaps": False,
        "has_overlaps": False,
        "segments": SEGMENTS,
        "intentional_gap_acknowledged": False,
        "overlap_coordination": OverlapCoordination.NONE,
        "priority_order": None,
        "eligibility_status": ProgramEligibilityStatus.ELIGIBLE,
        "blocking_issues": (),
    }
    values.update(changes)
    return ProgramGeometry(**values)


def layer_result(item: CatLayerInput, position: int, covered: float) -> CatLayerResult:
    factor = item.ceded_share * item.placement_share
    recovery = covered * factor
    return CatLayerResult(
        layer_input=item,
        geometry_position=position,
        priority_position=None,
        covered_loss_before_coordination=covered,
        allocated_covered_loss=covered,
        covered_loss_removed_by_coordination=0.0,
        recovery_before_coordination=recovery,
        gross_contractual_recovery=recovery,
        retained_participation=covered - recovery,
        attachment_reached=True,
        exhaustion_reached=covered == item.occurrence_limit,
        trace_references=("F11", "F13", "F14"),
    )


RESULTS = (
    layer_result(LAYERS[0], 1, 20_000_000.0),
    layer_result(LAYERS[1], 2, 15_000_000.0),
)
PROGRAM_CHECK = ReconciliationCheck(
    check_id="F15",
    formula_reference="F15",
    left_value=45_000_000.0,
    right_value=45_000_000.0,
    passed=True,
)
FACT = ExplanationFact(
    metric_name="total_gross_contractual_recovery",
    value=35_000_000.0,
    meaning="Program recovery",
    driver_statement="Both layers attach.",
    trace_reference="F15",
)


def completed_result(**changes: object) -> CT3ProgramResult:
    request = program()
    analysed = geometry()
    values: dict[str, object] = {
        "program_input": request,
        "geometry": analysed,
        "layer_results": RESULTS,
        "total_gross_contractual_recovery": 35_000_000.0,
        "insurer_net_loss": 10_000_000.0,
        "base_retention": 10_000_000.0,
        "gap_loss": 0.0,
        "in_layer_retained_participation": 0.0,
        "above_tower_loss": 0.0,
        "reconciliation_checks": (PROGRAM_CHECK,),
        "explanation_facts": (FACT,),
    }
    values.update(changes)
    return CT3ProgramResult(**values)


def test_ct3_enum_literals_are_frozen() -> None:
    assert GeometryClassification.OVERLAPPING.value == "overlapping"
    assert BlockingIssueCode.UNCOORDINATED_OVERLAP.value == "uncoordinated_overlap"
    assert ProgramEligibilityStatus.BLOCKED.value == "blocked"
    assert OverlapCoordination.PRIORITY.value == "priority"


def test_layer_is_immutable_and_derives_f10_exhaustion() -> None:
    item = layer()
    assert item.exhaustion == 30_000_000.0
    with pytest.raises(FrozenInstanceError):
        item.attachment = 0.0  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    [
        ("layer_id", " "),
        ("attachment", -1.0),
        ("attachment", math.nan),
        ("occurrence_limit", 0.0),
        ("occurrence_limit", math.inf),
        ("ceded_share", -0.1),
        ("ceded_share", 1.1),
        ("placement_share", math.nan),
        ("currency", ""),
        ("source_reference", " "),
    ],
)
def test_layer_rejects_invalid_terms(field_name: str, invalid: object) -> None:
    with pytest.raises(ValueError):
        layer(**{field_name: invalid})


def test_program_accepts_one_to_four_layers_and_preserves_input_order() -> None:
    assert program(layers=(LAYERS[1], LAYERS[0])).layers == (LAYERS[1], LAYERS[0])
    assert len(program(layers=(LAYERS[0],)).layers) == 1
    assert len(program(layers=LAYERS + (layer("L3", attachment=60e6), layer("L4", attachment=80e6))).layers) == 4


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"layers": ()}, "one to four"),
        ({"layers": LAYERS + (layer("L3"), layer("L4"), layer("L5"))}, "one to four"),
        ({"layers": (LAYERS[0], LAYERS[0])}, "unique"),
        ({"layers": (replace(LAYERS[0], currency="EUR"),)}, "currency"),
        ({"intentional_gap_acknowledged": 1}, "boolean"),
        ({"overlap_coordination": "none"}, "supported"),
        ({"priority_order": ("L1",)}, "requires priority"),
    ],
)
def test_program_rejects_invalid_collection_contract(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        program(**changes)


def test_priority_mode_requires_a_unique_nonblank_order_but_defers_completeness() -> None:
    request = program(
        overlap_coordination=OverlapCoordination.PRIORITY,
        priority_order=("L1",),
    )
    assert request.priority_order == ("L1",)
    for invalid in (None, (), ("L1", "L1"), ("",)):
        with pytest.raises(ValueError):
            program(
                overlap_coordination=OverlapCoordination.PRIORITY,
                priority_order=invalid,
            )


def test_program_rejects_mismatched_ct2_identity_and_hash() -> None:
    with pytest.raises(ValueError, match="occurrence"):
        program(ct2_metadata=replace(CT2_METADATA, occurrence_id="OTHER"))
    with pytest.raises(ValueError, match="currency"):
        program(ct2_metadata=replace(CT2_METADATA, reporting_currency="EUR"))
    with pytest.raises(ValueError, match="hash"):
        program(ct2_metadata=replace(CT2_METADATA, input_hash="0" * 64))


@pytest.mark.parametrize(
    ("kind", "members"),
    [
        (GeometrySegmentType.GAP, ()),
        (GeometrySegmentType.COVERED, ("L1",)),
        (GeometrySegmentType.OVERLAP, ("L1", "L2")),
    ],
)
def test_geometry_segment_membership_matches_type(kind: GeometrySegmentType, members: tuple[str, ...]) -> None:
    assert GeometrySegment(1.0, 2.0, kind, members).segment_type is kind


@pytest.mark.parametrize(
    ("kind", "members"),
    [
        (GeometrySegmentType.GAP, ("L1",)),
        (GeometrySegmentType.COVERED, ()),
        (GeometrySegmentType.OVERLAP, ("L1",)),
    ],
)
def test_geometry_segment_rejects_wrong_membership(kind: GeometrySegmentType, members: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        GeometrySegment(1.0, 2.0, kind, members)


def test_continuous_geometry_is_valid_and_immutable() -> None:
    analysed = geometry()
    assert analysed.classification is GeometryClassification.CONTINUOUS
    with pytest.raises(FrozenInstanceError):
        analysed.has_gaps = True  # type: ignore[misc]


def test_topology_classification_is_independent_of_blocked_eligibility() -> None:
    overlap = GeometrySegment(10.0, 20.0, GeometrySegmentType.OVERLAP, ("L1", "L2"))
    issue = BlockingIssue(
        code=BlockingIssueCode.UNCOORDINATED_OVERLAP,
        affected_segment=(10.0, 20.0),
        affected_layer_ids=("L1", "L2"),
        message="Overlap requires coordination.",
        rule_reference="section-9",
    )
    analysed = geometry(
        boundaries=(10.0, 20.0),
        segments=(overlap,),
        classification=GeometryClassification.OVERLAPPING,
        has_overlaps=True,
        eligibility_status=ProgramEligibilityStatus.BLOCKED,
        blocking_issues=(issue,),
    )
    assert analysed.classification is GeometryClassification.OVERLAPPING
    assert analysed.eligibility_status is ProgramEligibilityStatus.BLOCKED


@pytest.mark.parametrize(
    "changes",
    [
        {"boundaries": (10.0, 10.0)},
        {"has_gaps": True},
        {"classification": GeometryClassification.VENTILATED},
        {"eligibility_status": ProgramEligibilityStatus.BLOCKED},
        {"blocking_issues": (BlockingIssue(BlockingIssueCode.UNACKNOWLEDGED_GAP, None, (), "Gap", "section-8"),)},
        {"segments": ()},
    ],
)
def test_geometry_rejects_inconsistent_state(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        geometry(**changes)


def test_layer_result_enforces_f13_f14_and_coordination_reconciliation() -> None:
    item = layer(ceded_share=0.9, placement_share=0.75)
    result = layer_result(item, 1, 20.0)
    assert result.gross_contractual_recovery == 13.5
    assert result.retained_participation == 6.5
    for changes in (
        {"allocated_covered_loss": 21.0},
        {"covered_loss_removed_by_coordination": 1.0},
        {"recovery_before_coordination": 1.0},
        {"gross_contractual_recovery": 1.0},
        {"retained_participation": 1.0},
        {"exhaustion_reached": True, "attachment_reached": False},
    ):
        with pytest.raises(ValueError):
            replace(result, **changes)


def test_completed_program_reconciles_g26_and_is_immutable() -> None:
    result = completed_result()
    assert result.total_gross_contractual_recovery == 35_000_000.0
    assert result.insurer_net_loss == 10_000_000.0
    with pytest.raises(FrozenInstanceError):
        result.insurer_net_loss = 0.0  # type: ignore[misc]


@pytest.mark.parametrize(
    "changes",
    [
        {"total_gross_contractual_recovery": 34_000_000.0},
        {"insurer_net_loss": 9_000_000.0},
        {"base_retention": 9_000_000.0},
        {"layer_results": RESULTS[:1]},
        {"reconciliation_checks": ()},
    ],
)
def test_completed_program_rejects_failed_f15_f16_or_incomplete_rows(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        completed_result(**changes)


def test_assessment_envelope_requires_result_only_when_eligible() -> None:
    result = completed_result()
    assessment = CT3AssessmentResult(result.program_input, result.geometry, result)
    assert assessment.program_result is result

    issue = BlockingIssue(
        BlockingIssueCode.UNCOORDINATED_OVERLAP,
        (10.0, 20.0),
        ("L1", "L2"),
        "Coordination missing.",
        "section-9",
    )
    blocked = geometry(
        boundaries=(10.0, 20.0),
        segments=(GeometrySegment(10.0, 20.0, GeometrySegmentType.OVERLAP, ("L1", "L2")),),
        classification=GeometryClassification.OVERLAPPING,
        has_overlaps=True,
        eligibility_status=ProgramEligibilityStatus.BLOCKED,
        blocking_issues=(issue,),
    )
    assert CT3AssessmentResult(program(), blocked, None).program_result is None
    with pytest.raises(ValueError):
        CT3AssessmentResult(program(), blocked, result)
    with pytest.raises(ValueError):
        CT3AssessmentResult(program(), geometry(), None)
