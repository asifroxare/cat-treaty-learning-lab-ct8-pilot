"""Immutable CT3 multi-layer program domain contracts.

These models validate requests, diagnostic geometry, and completed result
records. Geometry construction and F11-F16 calculations live in later CT3
implementation units.
"""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real

from cat_treaty.ct2_metadata import CT2RunMetadata, build_ct2_run_metadata
from cat_treaty.ct2_models import (
    ExplanationFact,
    InuringWaterfallInput,
    InuringWaterfallResult,
    ReconciliationCheck,
)


class OverlapCoordination(str, Enum):
    NONE = "none"
    PRIORITY = "priority"


class GeometryClassification(str, Enum):
    SINGLE_LAYER = "single_layer"
    CONTINUOUS = "continuous"
    VENTILATED = "ventilated"
    OVERLAPPING = "overlapping"
    MIXED = "mixed"


class GeometrySegmentType(str, Enum):
    COVERED = "covered"
    GAP = "gap"
    OVERLAP = "overlap"


class ProgramEligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    BLOCKED = "blocked"


class BlockingIssueCode(str, Enum):
    UNACKNOWLEDGED_GAP = "unacknowledged_gap"
    UNCOORDINATED_OVERLAP = "uncoordinated_overlap"
    INVALID_PRIORITY_ORDER = "invalid_priority_order"
    UNNECESSARY_PRIORITY_COORDINATION = "unnecessary_priority_coordination"


def _nonblank(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _finite(field_name: str, value: object, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if result < 0 or (positive and result <= 0):
        qualifier = "greater than zero" if positive else "non-negative"
        raise ValueError(f"{field_name} must be {qualifier}")
    return result


def _fraction(field_name: str, value: object) -> float:
    result = _finite(field_name, value)
    if result > 1:
        raise ValueError(f"{field_name} must lie in [0, 1]")
    return result


def _enum(field_name: str, value: object, enum_type: type[Enum]) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{field_name} must be a supported {enum_type.__name__}")


def _strings(field_name: str, values: object) -> None:
    if not isinstance(values, tuple) or not all(
        isinstance(item, str) and item.strip() for item in values
    ):
        raise ValueError(f"{field_name} must contain non-empty strings")


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-6)


@dataclass(frozen=True, slots=True)
class CatLayerInput:
    """Contract terms for one CT3 occurrence Cat XL layer."""

    layer_id: str
    attachment: float
    occurrence_limit: float
    ceded_share: float
    placement_share: float
    currency: str
    description: str
    source_reference: str
    rule_reference: str

    def __post_init__(self) -> None:
        _nonblank("layer_id", self.layer_id)
        attachment = _finite("attachment", self.attachment)
        limit = _finite("occurrence_limit", self.occurrence_limit, positive=True)
        _fraction("ceded_share", self.ceded_share)
        _fraction("placement_share", self.placement_share)
        for name in ("currency", "description", "source_reference", "rule_reference"):
            _nonblank(name, getattr(self, name))
        if not math.isfinite(attachment + limit):
            raise ValueError("layer exhaustion must be finite")

    @property
    def exhaustion(self) -> float:
        return float(self.attachment) + float(self.occurrence_limit)


@dataclass(frozen=True, slots=True)
class CT3ProgramInput:
    """Validated CT2 entry record and multi-layer CT3 contract request."""

    program_id: str
    ct2_result: InuringWaterfallResult
    ct2_metadata: CT2RunMetadata
    layers: tuple[CatLayerInput, ...]
    intentional_gap_acknowledged: bool
    overlap_coordination: OverlapCoordination
    priority_order: tuple[str, ...] | None
    description: str
    source_reference: str
    rule_reference: str

    def __post_init__(self) -> None:
        _nonblank("program_id", self.program_id)
        if not isinstance(self.ct2_result, InuringWaterfallResult):
            raise ValueError("ct2_result must be a completed InuringWaterfallResult")
        if not isinstance(self.ct2_metadata, CT2RunMetadata):
            raise ValueError("ct2_metadata must be CT2RunMetadata")
        if not isinstance(self.layers, tuple) or not all(
            isinstance(item, CatLayerInput) for item in self.layers
        ):
            raise ValueError("layers must contain CatLayerInput values")
        if not 1 <= len(self.layers) <= 4:
            raise ValueError("CT3 requires one to four layers")
        layer_ids = tuple(item.layer_id for item in self.layers)
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("layer_id values must be unique")
        currency = self.ct2_result.loss_basis.basis_input.reporting_currency
        if any(item.currency != currency for item in self.layers):
            raise ValueError("layer currencies must match CT2 reporting currency")
        if not isinstance(self.intentional_gap_acknowledged, bool):
            raise ValueError("intentional_gap_acknowledged must be boolean")
        _enum("overlap_coordination", self.overlap_coordination, OverlapCoordination)
        self._validate_priority_shape()
        for name in ("description", "source_reference", "rule_reference"):
            _nonblank(name, getattr(self, name))
        self._validate_ct2_identity(currency)

    def _validate_priority_shape(self) -> None:
        if self.priority_order is not None:
            _strings("priority_order", self.priority_order)
            if not self.priority_order:
                raise ValueError("priority_order cannot be empty")
            if len(self.priority_order) != len(set(self.priority_order)):
                raise ValueError("priority_order values must be unique")
        if self.overlap_coordination is OverlapCoordination.NONE:
            if self.priority_order is not None:
                raise ValueError("priority_order requires priority coordination")
        elif self.priority_order is None:
            raise ValueError("priority coordination requires priority_order")

    def _validate_ct2_identity(self, currency: str) -> None:
        basis = self.ct2_result.loss_basis.basis_input
        metadata = self.ct2_metadata
        if metadata.occurrence_id != basis.occurrence_id:
            raise ValueError("CT2 occurrence identity does not match")
        if metadata.reporting_currency != currency:
            raise ValueError("CT2 reporting currency does not match")
        waterfall_input = InuringWaterfallInput(
            loss_basis=self.ct2_result.loss_basis,
            covers=tuple(row.cover_input for row in self.ct2_result.cover_results),
        )
        rebuilt = build_ct2_run_metadata(
            waterfall_input=waterfall_input,
            source_version=metadata.source_version,
            engine_version=metadata.engine_version,
            schema_version=metadata.schema_version,
        )
        if rebuilt.input_hash != metadata.input_hash:
            raise ValueError("CT2 input hash does not match completed waterfall")


@dataclass(frozen=True, slots=True)
class GeometrySegment:
    start: float
    end: float
    segment_type: GeometrySegmentType
    layer_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        start = _finite("start", self.start)
        end = _finite("end", self.end, positive=True)
        if end <= start:
            raise ValueError("geometry segment end must exceed start")
        _enum("segment_type", self.segment_type, GeometrySegmentType)
        _strings("layer_ids", self.layer_ids) if self.layer_ids else None
        if len(self.layer_ids) != len(set(self.layer_ids)):
            raise ValueError("segment layer_ids must be unique")
        expected = {
            GeometrySegmentType.GAP: 0,
            GeometrySegmentType.COVERED: 1,
        }
        if self.segment_type in expected and len(self.layer_ids) != expected[self.segment_type]:
            raise ValueError("segment type does not match layer membership")
        if self.segment_type is GeometrySegmentType.OVERLAP and len(self.layer_ids) < 2:
            raise ValueError("overlap segment requires at least two layers")


@dataclass(frozen=True, slots=True)
class BlockingIssue:
    code: BlockingIssueCode
    affected_segment: tuple[float, float] | None
    affected_layer_ids: tuple[str, ...]
    message: str
    rule_reference: str

    def __post_init__(self) -> None:
        _enum("code", self.code, BlockingIssueCode)
        if self.affected_segment is not None:
            if not isinstance(self.affected_segment, tuple) or len(self.affected_segment) != 2:
                raise ValueError("affected_segment must be a two-value tuple")
            start = _finite("affected_segment start", self.affected_segment[0])
            end = _finite("affected_segment end", self.affected_segment[1], positive=True)
            if end <= start:
                raise ValueError("affected_segment end must exceed start")
        _strings("affected_layer_ids", self.affected_layer_ids) if self.affected_layer_ids else None
        if len(self.affected_layer_ids) != len(set(self.affected_layer_ids)):
            raise ValueError("affected_layer_ids must be unique")
        _nonblank("message", self.message)
        _nonblank("rule_reference", self.rule_reference)


@dataclass(frozen=True, slots=True)
class ProgramGeometry:
    sorted_layer_ids: tuple[str, ...]
    boundaries: tuple[float, ...]
    classification: GeometryClassification
    has_gaps: bool
    has_overlaps: bool
    segments: tuple[GeometrySegment, ...]
    intentional_gap_acknowledged: bool
    overlap_coordination: OverlapCoordination
    priority_order: tuple[str, ...] | None
    eligibility_status: ProgramEligibilityStatus
    blocking_issues: tuple[BlockingIssue, ...]
    notices: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _strings("sorted_layer_ids", self.sorted_layer_ids)
        if len(self.sorted_layer_ids) != len(set(self.sorted_layer_ids)):
            raise ValueError("sorted_layer_ids must be unique")
        if not isinstance(self.boundaries, tuple) or len(self.boundaries) < 2:
            raise ValueError("boundaries must contain at least two values")
        values = tuple(_finite("boundary", value) for value in self.boundaries)
        if any(right <= left for left, right in zip(values, values[1:], strict=False)):
            raise ValueError("boundaries must be strictly increasing")
        _enum("classification", self.classification, GeometryClassification)
        if not isinstance(self.has_gaps, bool) or not isinstance(self.has_overlaps, bool):
            raise ValueError("geometry flags must be boolean")
        if not isinstance(self.segments, tuple) or not all(
            isinstance(item, GeometrySegment) for item in self.segments
        ):
            raise ValueError("segments must contain GeometrySegment values")
        if tuple((item.start, item.end) for item in self.segments) != tuple(
            zip(values, values[1:], strict=False)
        ):
            raise ValueError("segments must exactly span consecutive boundaries")
        observed_gaps = any(item.segment_type is GeometrySegmentType.GAP for item in self.segments)
        observed_overlaps = any(item.segment_type is GeometrySegmentType.OVERLAP for item in self.segments)
        if self.has_gaps != observed_gaps or self.has_overlaps != observed_overlaps:
            raise ValueError("geometry flags do not match segments")
        expected = self._expected_classification()
        if self.classification is not expected:
            raise ValueError("geometry classification does not match topology")
        if not isinstance(self.intentional_gap_acknowledged, bool):
            raise ValueError("intentional_gap_acknowledged must be boolean")
        _enum("overlap_coordination", self.overlap_coordination, OverlapCoordination)
        if self.priority_order is not None:
            _strings("priority_order", self.priority_order)
        _enum("eligibility_status", self.eligibility_status, ProgramEligibilityStatus)
        if not isinstance(self.blocking_issues, tuple) or not all(
            isinstance(item, BlockingIssue) for item in self.blocking_issues
        ):
            raise ValueError("blocking_issues must contain BlockingIssue values")
        if (self.eligibility_status is ProgramEligibilityStatus.BLOCKED) != bool(self.blocking_issues):
            raise ValueError("eligibility status must match blocking issues")
        _strings("notices", self.notices)
        _strings("warnings", self.warnings)

    def _expected_classification(self) -> GeometryClassification:
        if len(self.sorted_layer_ids) == 1:
            return GeometryClassification.SINGLE_LAYER
        if self.has_gaps and self.has_overlaps:
            return GeometryClassification.MIXED
        if self.has_gaps:
            return GeometryClassification.VENTILATED
        if self.has_overlaps:
            return GeometryClassification.OVERLAPPING
        return GeometryClassification.CONTINUOUS


@dataclass(frozen=True, slots=True)
class CatLayerResult:
    layer_input: CatLayerInput
    geometry_position: int
    priority_position: int | None
    covered_loss_before_coordination: float
    allocated_covered_loss: float
    covered_loss_removed_by_coordination: float
    recovery_before_coordination: float
    gross_contractual_recovery: float
    retained_participation: float
    attachment_reached: bool
    exhaustion_reached: bool
    trace_references: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.layer_input, CatLayerInput):
            raise ValueError("layer_input must be CatLayerInput")
        if isinstance(self.geometry_position, bool) or not isinstance(self.geometry_position, int) or self.geometry_position < 1:
            raise ValueError("geometry_position must be a positive integer")
        if self.priority_position is not None and (
            isinstance(self.priority_position, bool)
            or not isinstance(self.priority_position, int)
            or self.priority_position < 1
        ):
            raise ValueError("priority_position must be a positive integer or null")
        covered = _finite("covered_loss_before_coordination", self.covered_loss_before_coordination)
        allocated = _finite("allocated_covered_loss", self.allocated_covered_loss)
        removed = _finite("covered_loss_removed_by_coordination", self.covered_loss_removed_by_coordination)
        before = _finite("recovery_before_coordination", self.recovery_before_coordination)
        recovery = _finite("gross_contractual_recovery", self.gross_contractual_recovery)
        retained = _finite("retained_participation", self.retained_participation)
        factor = float(self.layer_input.ceded_share) * float(self.layer_input.placement_share)
        if allocated > covered and not _close(allocated, covered):
            raise ValueError("allocated covered loss cannot exceed covered loss")
        checks = (
            (covered, allocated + removed, "coordination removal"),
            (before, covered * factor, "recovery before coordination"),
            (recovery, allocated * factor, "gross contractual recovery"),
            (retained, allocated - recovery, "retained participation"),
        )
        for actual, expected, name in checks:
            if not _close(actual, expected):
                raise ValueError(f"{name} does not reconcile")
        if not isinstance(self.attachment_reached, bool) or not isinstance(self.exhaustion_reached, bool):
            raise ValueError("layer reach indicators must be boolean")
        if self.exhaustion_reached and not self.attachment_reached:
            raise ValueError("exhaustion cannot be reached before attachment")
        _strings("trace_references", self.trace_references)


@dataclass(frozen=True, slots=True)
class CT3ProgramResult:
    program_input: CT3ProgramInput
    geometry: ProgramGeometry
    layer_results: tuple[CatLayerResult, ...]
    total_gross_contractual_recovery: float
    insurer_net_loss: float
    base_retention: float
    gap_loss: float
    in_layer_retained_participation: float
    above_tower_loss: float
    reconciliation_checks: tuple[ReconciliationCheck, ...]
    explanation_facts: tuple[ExplanationFact, ...]
    warnings: tuple[str, ...] = ()
    assumption_disclosures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.program_input, CT3ProgramInput):
            raise ValueError("program_input must be CT3ProgramInput")
        if not isinstance(self.geometry, ProgramGeometry):
            raise ValueError("geometry must be ProgramGeometry")
        if self.geometry.eligibility_status is not ProgramEligibilityStatus.ELIGIBLE:
            raise ValueError("blocked geometry cannot produce a program result")
        if not isinstance(self.layer_results, tuple) or not all(
            isinstance(item, CatLayerResult) for item in self.layer_results
        ):
            raise ValueError("layer_results must contain CatLayerResult values")
        requested = {item.layer_id for item in self.program_input.layers}
        returned = {item.layer_input.layer_id for item in self.layer_results}
        if returned != requested or len(returned) != len(self.layer_results):
            raise ValueError("layer results must match every requested layer exactly once")
        recovery = _finite("total_gross_contractual_recovery", self.total_gross_contractual_recovery)
        net = _finite("insurer_net_loss", self.insurer_net_loss)
        buckets = tuple(
            _finite(name, getattr(self, name))
            for name in (
                "base_retention", "gap_loss", "in_layer_retained_participation", "above_tower_loss"
            )
        )
        subject = float(self.program_input.ct2_result.cat_xl_subject_loss)
        if not _close(recovery, math.fsum(item.gross_contractual_recovery for item in self.layer_results)):
            raise ValueError("total recovery does not reconcile to layers")
        if not _close(subject, recovery + net):
            raise ValueError("F15 does not reconcile")
        if not _close(net, math.fsum(buckets)):
            raise ValueError("F16 retained buckets do not reconcile")
        if not isinstance(self.reconciliation_checks, tuple) or not self.reconciliation_checks or not all(
            isinstance(item, ReconciliationCheck) and item.passed for item in self.reconciliation_checks
        ):
            raise ValueError("completed result requires passed reconciliation checks")
        if not isinstance(self.explanation_facts, tuple) or not all(
            isinstance(item, ExplanationFact) for item in self.explanation_facts
        ):
            raise ValueError("explanation_facts must contain ExplanationFact values")
        _strings("warnings", self.warnings)
        _strings("assumption_disclosures", self.assumption_disclosures)


@dataclass(frozen=True, slots=True)
class CT3AssessmentResult:
    """One response envelope for eligible and blocked program assessments."""

    program_input: CT3ProgramInput
    geometry: ProgramGeometry
    program_result: CT3ProgramResult | None

    def __post_init__(self) -> None:
        if not isinstance(self.program_input, CT3ProgramInput):
            raise ValueError("program_input must be CT3ProgramInput")
        if not isinstance(self.geometry, ProgramGeometry):
            raise ValueError("geometry must be ProgramGeometry")
        blocked = self.geometry.eligibility_status is ProgramEligibilityStatus.BLOCKED
        if blocked and self.program_result is not None:
            raise ValueError("blocked assessment must have null program_result")
        if not blocked:
            if not isinstance(self.program_result, CT3ProgramResult):
                raise ValueError("eligible assessment requires program_result")
            if self.program_result.program_input != self.program_input or self.program_result.geometry != self.geometry:
                raise ValueError("program result must belong to this assessment")
