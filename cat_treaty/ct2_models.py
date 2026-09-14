"""Immutable CT2 loss-basis and ordered-inuring domain models.

The models validate contractual inputs and completed calculation records. They
do not calculate Ultimate Net Loss or inuring recoveries.
"""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real


class LossComponentCategory(str, Enum):
    """Contract-defined additions and deductions in F03."""

    LOSS_ADJUSTMENT_EXPENSE = "loss_adjustment_expense"
    OTHER_INCLUDED_COST = "other_included_cost"
    SALVAGE = "salvage"
    SUBROGATION = "subrogation"
    OTHER_NON_INURING_RECOVERY = "other_non_inuring_recovery"
    CONTRACT_EXCLUSION = "contract_exclusion"


class InuringCoverType(str, Enum):
    """Inuring cover labels supported by the CT2 contract."""

    QUOTA_SHARE = "quota_share"
    SURPLUS_SHARE = "surplus_share"
    FACULTATIVE = "facultative"
    PER_RISK_XL = "per_risk_xl"
    OTHER = "other"


class InuringValuationMode(str, Enum):
    """How a CT2 inuring recovery enters the waterfall."""

    CALCULATED_PROPORTIONAL = "calculated_proportional"
    SUPPLIED_RECOVERY = "supplied_recovery"


class InuringCompletionStatus(str, Enum):
    """Successful states that may provide subject loss to CT3."""

    COMPLETE = "complete"
    COMPLETE_NO_INURING_COVERS = "complete_no_inuring_covers"


class BindingConstraint(str, Enum):
    """A limit that reduced or exactly capped an inuring recovery."""

    OCCURRENCE_LIMIT = "occurrence_limit"
    AGGREGATE_REMAINING = "aggregate_remaining"


_ADDITION_CATEGORIES = frozenset(
    {
        LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
        LossComponentCategory.OTHER_INCLUDED_COST,
    }
)


def _nonblank(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _finite(
    field_name: str,
    value: object,
    *,
    non_negative: bool = True,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if non_negative and result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def _fraction(field_name: str, value: object) -> float:
    result = _finite(field_name, value)
    if result > 1:
        raise ValueError(f"{field_name} must lie in [0, 1]")
    return result


def _positive_integer(field_name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def _positive_optional(field_name: str, value: object | None) -> None:
    if value is None:
        return
    if _finite(field_name, value) <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def _require_enum(field_name: str, value: object, enum_type: type[Enum]) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{field_name} must be a supported {enum_type.__name__}")


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-6)


@dataclass(frozen=True, slots=True)
class LossComponent:
    """One visible F03 input component with contract inclusion metadata."""

    component_id: str
    category: LossComponentCategory
    label: str
    amount: float
    included: bool
    source_reference: str
    rule_reference: str

    def __post_init__(self) -> None:
        _nonblank("component_id", self.component_id)
        _require_enum("category", self.category, LossComponentCategory)
        _nonblank("label", self.label)
        _finite("amount", self.amount)
        if not isinstance(self.included, bool):
            raise ValueError("included must be boolean")
        _nonblank("source_reference", self.source_reference)
        _nonblank("rule_reference", self.rule_reference)

    @property
    def applied_amount(self) -> float:
        """Return zero for disclosed-but-excluded components."""

        return float(self.amount) if self.included else 0.0

    @property
    def is_addition(self) -> bool:
        return self.category in _ADDITION_CATEGORIES


@dataclass(frozen=True, slots=True)
class LossBasisInput:
    """Validated inputs required to construct CT2 Ultimate Net Loss."""

    occurrence_id: str
    reporting_currency: str
    source_stage_declaration: str
    source_reference: str
    initial_insured_loss: float
    components: tuple[LossComponent, ...] = ()
    ground_up_loss: float | None = None

    def __post_init__(self) -> None:
        _nonblank("occurrence_id", self.occurrence_id)
        _nonblank("reporting_currency", self.reporting_currency)
        _nonblank("source_stage_declaration", self.source_stage_declaration)
        _nonblank("source_reference", self.source_reference)
        _finite("initial_insured_loss", self.initial_insured_loss)
        if self.ground_up_loss is not None:
            _finite("ground_up_loss", self.ground_up_loss)
        if not isinstance(self.components, tuple):
            raise ValueError("components must be a tuple")
        if not all(isinstance(item, LossComponent) for item in self.components):
            raise ValueError("components must contain LossComponent values")
        ids = tuple(item.component_id for item in self.components)
        if len(ids) != len(set(ids)):
            raise ValueError("component_id values must be unique")


@dataclass(frozen=True, slots=True)
class LossBasisResult:
    """Completed, independently reconciled F03/F04 record."""

    basis_input: LossBasisInput
    included_additions: float
    applied_deductions: float
    ultimate_net_loss_before_inuring: float
    reconciliation_passed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.basis_input, LossBasisInput):
            raise ValueError("basis_input must be a LossBasisInput")
        additions = _finite("included_additions", self.included_additions)
        deductions = _finite("applied_deductions", self.applied_deductions)
        unl = _finite(
            "ultimate_net_loss_before_inuring",
            self.ultimate_net_loss_before_inuring,
        )
        if not isinstance(self.reconciliation_passed, bool):
            raise ValueError("reconciliation_passed must be boolean")

        expected_additions = math.fsum(
            component.applied_amount
            for component in self.basis_input.components
            if component.is_addition
        )
        expected_deductions = math.fsum(
            component.applied_amount
            for component in self.basis_input.components
            if not component.is_addition
        )
        expected_unl = (
            float(self.basis_input.initial_insured_loss)
            + expected_additions
            - expected_deductions
        )
        if expected_unl < 0:
            raise ValueError("applied deductions exceed insured loss and additions")
        if not _close(additions, expected_additions):
            raise ValueError("included_additions do not reconcile")
        if not _close(deductions, expected_deductions):
            raise ValueError("applied_deductions do not reconcile")
        if not _close(unl, expected_unl):
            raise ValueError("ultimate_net_loss_before_inuring does not reconcile")
        if not self.reconciliation_passed:
            raise ValueError("a completed LossBasisResult must be reconciled")


@dataclass(frozen=True, slots=True)
class InuringCoverInput:
    """One explicitly ordered inuring-cover instruction."""

    cover_id: str
    cover_type: InuringCoverType
    order: int
    valuation_mode: InuringValuationMode
    scope_fraction: float
    currency: str
    description: str
    source_reference: str
    rule_reference: str
    cession_rate: float | None = None
    occurrence_limit: float | None = None
    aggregate_remaining_before: float | None = None
    supplied_recovery: float | None = None
    recovery_source_id: str | None = None

    def __post_init__(self) -> None:
        _nonblank("cover_id", self.cover_id)
        _require_enum("cover_type", self.cover_type, InuringCoverType)
        _positive_integer("order", self.order)
        _require_enum(
            "valuation_mode",
            self.valuation_mode,
            InuringValuationMode,
        )
        _fraction("scope_fraction", self.scope_fraction)
        _nonblank("currency", self.currency)
        _nonblank("description", self.description)
        _nonblank("source_reference", self.source_reference)
        _nonblank("rule_reference", self.rule_reference)
        _positive_optional("occurrence_limit", self.occurrence_limit)
        if self.aggregate_remaining_before is not None:
            _finite(
                "aggregate_remaining_before",
                self.aggregate_remaining_before,
            )

        if self.valuation_mode is InuringValuationMode.CALCULATED_PROPORTIONAL:
            self._validate_calculated_mode()
        else:
            self._validate_supplied_mode()

    def _validate_calculated_mode(self) -> None:
        if self.cover_type is not InuringCoverType.QUOTA_SHARE:
            raise ValueError(
                "calculated_proportional is supported only for quota_share in CT2"
            )
        if self.cession_rate is None:
            raise ValueError("calculated_proportional requires cession_rate")
        _fraction("cession_rate", self.cession_rate)
        if self.supplied_recovery is not None:
            raise ValueError("calculated_proportional forbids supplied_recovery")
        if self.recovery_source_id is not None:
            raise ValueError("calculated_proportional forbids recovery_source_id")

    def _validate_supplied_mode(self) -> None:
        if self.cession_rate is not None:
            raise ValueError("supplied_recovery mode forbids cession_rate")
        if self.supplied_recovery is None:
            raise ValueError("supplied_recovery mode requires supplied_recovery")
        _finite("supplied_recovery", self.supplied_recovery)
        if self.recovery_source_id is None:
            raise ValueError("supplied_recovery mode requires recovery_source_id")
        _nonblank("recovery_source_id", self.recovery_source_id)


@dataclass(frozen=True, slots=True)
class InuringWaterfallInput:
    """Collection-level contract for one explicitly ordered waterfall."""

    loss_basis: LossBasisResult
    covers: tuple[InuringCoverInput, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.loss_basis, LossBasisResult):
            raise ValueError("loss_basis must be a LossBasisResult")
        if not isinstance(self.covers, tuple) or not all(
            isinstance(item, InuringCoverInput) for item in self.covers
        ):
            raise ValueError("covers must contain InuringCoverInput values")

        orders = tuple(item.order for item in self.covers)
        if orders != tuple(range(1, len(orders) + 1)):
            raise ValueError("cover order must be contiguous from 1")

        cover_ids = tuple(item.cover_id for item in self.covers)
        if len(cover_ids) != len(set(cover_ids)):
            raise ValueError("cover_id values must be unique")

        source_ids = tuple(
            item.recovery_source_id
            for item in self.covers
            if item.recovery_source_id is not None
        )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("recovery_source_id values must be unique")

        reporting_currency = self.loss_basis.basis_input.reporting_currency
        if any(item.currency != reporting_currency for item in self.covers):
            raise ValueError("cover currencies must match reporting_currency")


@dataclass(frozen=True, slots=True)
class InuringCoverResult:
    """One immutable, reconciled row in the ordered waterfall."""

    cover_input: InuringCoverInput
    incoming_loss: float
    cover_subject_loss: float
    recovery_before_limits: float
    payable_recovery: float
    outgoing_loss: float
    aggregate_remaining_after: float | None
    binding_constraints: tuple[BindingConstraint, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.cover_input, InuringCoverInput):
            raise ValueError("cover_input must be an InuringCoverInput")
        incoming = _finite("incoming_loss", self.incoming_loss)
        subject = _finite("cover_subject_loss", self.cover_subject_loss)
        before_limits = _finite(
            "recovery_before_limits",
            self.recovery_before_limits,
        )
        payable = _finite("payable_recovery", self.payable_recovery)
        outgoing = _finite("outgoing_loss", self.outgoing_loss)
        if subject > incoming and not _close(subject, incoming):
            raise ValueError("cover_subject_loss cannot exceed incoming_loss")
        if before_limits > subject and not _close(before_limits, subject):
            raise ValueError(
                "recovery_before_limits cannot exceed cover_subject_loss"
            )
        if payable > before_limits and not _close(payable, before_limits):
            raise ValueError("payable_recovery cannot exceed recovery_before_limits")
        if not _close(incoming, payable + outgoing):
            raise ValueError("incoming_loss must equal payable_recovery plus outgoing_loss")

        self._validate_aggregate(payable)
        self._validate_constraints(payable, before_limits)

    @property
    def cover_id(self) -> str:
        return self.cover_input.cover_id

    @property
    def cover_type(self) -> InuringCoverType:
        return self.cover_input.cover_type

    @property
    def order(self) -> int:
        return self.cover_input.order

    @property
    def valuation_mode(self) -> InuringValuationMode:
        return self.cover_input.valuation_mode

    @property
    def currency(self) -> str:
        return self.cover_input.currency

    @property
    def occurrence_limit(self) -> float | None:
        return self.cover_input.occurrence_limit

    @property
    def aggregate_remaining_before(self) -> float | None:
        return self.cover_input.aggregate_remaining_before

    @property
    def source_reference(self) -> str:
        return self.cover_input.source_reference

    @property
    def rule_reference(self) -> str:
        return self.cover_input.rule_reference

    def _validate_aggregate(self, payable: float) -> None:
        before = self.aggregate_remaining_before
        after = self.aggregate_remaining_after
        if before is None:
            if after is not None:
                raise ValueError(
                    "aggregate_remaining_after must be null when before is null"
                )
            return
        before_value = _finite("aggregate_remaining_before", before)
        if after is None:
            raise ValueError(
                "aggregate_remaining_after is required when before is present"
            )
        after_value = _finite("aggregate_remaining_after", after)
        if payable > before_value and not _close(payable, before_value):
            raise ValueError("payable_recovery cannot exceed aggregate remaining")
        if not _close(after_value, before_value - payable):
            raise ValueError("aggregate remaining before/after does not reconcile")

    def _validate_constraints(self, payable: float, before_limits: float) -> None:
        if not isinstance(self.binding_constraints, tuple):
            raise ValueError("binding_constraints must be a tuple")
        if not all(
            isinstance(item, BindingConstraint)
            for item in self.binding_constraints
        ):
            raise ValueError(
                "binding_constraints must contain BindingConstraint values"
            )
        if len(self.binding_constraints) != len(set(self.binding_constraints)):
            raise ValueError("binding_constraints must be unique")
        if BindingConstraint.OCCURRENCE_LIMIT in self.binding_constraints:
            if self.occurrence_limit is None or not _close(
                payable,
                float(self.occurrence_limit),
            ):
                raise ValueError("occurrence_limit is not binding")
        if BindingConstraint.AGGREGATE_REMAINING in self.binding_constraints:
            if self.aggregate_remaining_before is None or not _close(
                payable,
                float(self.aggregate_remaining_before),
            ):
                raise ValueError("aggregate_remaining is not binding")
        if not self.binding_constraints and payable < before_limits:
            raise ValueError("a reduced recovery requires a binding constraint")


@dataclass(frozen=True, slots=True)
class ReconciliationCheck:
    """Machine-checkable equality included in the CT2 audit response."""

    check_id: str
    formula_reference: str
    left_value: float
    right_value: float
    passed: bool

    def __post_init__(self) -> None:
        _nonblank("check_id", self.check_id)
        _nonblank("formula_reference", self.formula_reference)
        left = _finite("left_value", self.left_value)
        right = _finite("right_value", self.right_value)
        if not isinstance(self.passed, bool):
            raise ValueError("passed must be boolean")
        if self.passed != _close(left, right):
            raise ValueError("passed must match the reconciled values")


@dataclass(frozen=True, slots=True)
class ExplanationFact:
    """Deterministic learning content attached to a material result."""

    metric_name: str
    value: float
    meaning: str
    driver_statement: str
    trace_reference: str

    def __post_init__(self) -> None:
        _nonblank("metric_name", self.metric_name)
        _finite("value", self.value)
        _nonblank("meaning", self.meaning)
        _nonblank("driver_statement", self.driver_statement)
        _nonblank("trace_reference", self.trace_reference)


@dataclass(frozen=True, slots=True)
class InuringWaterfallResult:
    """Completed CT2 result eligible to supply subject loss to CT3."""

    loss_basis: LossBasisResult
    cover_results: tuple[InuringCoverResult, ...]
    total_inuring_recovery: float
    cat_xl_subject_loss: float
    completion_status: InuringCompletionStatus
    reconciliation_checks: tuple[ReconciliationCheck, ...]
    explanation_facts: tuple[ExplanationFact, ...]
    warnings: tuple[str, ...] = ()
    assumption_disclosures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.loss_basis, LossBasisResult):
            raise ValueError("loss_basis must be a LossBasisResult")
        if not isinstance(self.cover_results, tuple) or not all(
            isinstance(item, InuringCoverResult) for item in self.cover_results
        ):
            raise ValueError("cover_results must contain InuringCoverResult values")
        _require_enum(
            "completion_status",
            self.completion_status,
            InuringCompletionStatus,
        )
        total = _finite("total_inuring_recovery", self.total_inuring_recovery)
        subject = _finite("cat_xl_subject_loss", self.cat_xl_subject_loss)
        self._validate_collections()
        self._validate_status()
        self._validate_waterfall(total, subject)

    def _validate_collections(self) -> None:
        if not isinstance(self.reconciliation_checks, tuple) or not all(
            isinstance(item, ReconciliationCheck)
            for item in self.reconciliation_checks
        ):
            raise ValueError(
                "reconciliation_checks must contain ReconciliationCheck values"
            )
        if not self.reconciliation_checks or not all(
            item.passed for item in self.reconciliation_checks
        ):
            raise ValueError("completed result requires passed reconciliation checks")
        if not isinstance(self.explanation_facts, tuple) or not all(
            isinstance(item, ExplanationFact) for item in self.explanation_facts
        ):
            raise ValueError(
                "explanation_facts must contain ExplanationFact values"
            )
        for field_name, values in (
            ("warnings", self.warnings),
            ("assumption_disclosures", self.assumption_disclosures),
        ):
            if not isinstance(values, tuple) or not all(
                isinstance(item, str) and item.strip() for item in values
            ):
                raise ValueError(f"{field_name} must contain non-empty strings")

    def _validate_status(self) -> None:
        if self.cover_results:
            if self.completion_status is not InuringCompletionStatus.COMPLETE:
                raise ValueError("cover results require complete status")
        elif self.completion_status is not (
            InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
        ):
            raise ValueError(
                "no covers require complete_no_inuring_covers status"
            )

    def _validate_waterfall(self, total: float, subject: float) -> None:
        unl = float(self.loss_basis.ultimate_net_loss_before_inuring)
        if self.cover_results:
            orders = tuple(item.order for item in self.cover_results)
            if orders != tuple(range(1, len(orders) + 1)):
                raise ValueError("cover result order must be contiguous from 1")
            ids = tuple(item.cover_id for item in self.cover_results)
            if len(ids) != len(set(ids)):
                raise ValueError("cover_id values must be unique")
            currencies = {item.currency for item in self.cover_results}
            if currencies != {self.loss_basis.basis_input.reporting_currency}:
                raise ValueError("cover currencies must match reporting_currency")
            if not _close(self.cover_results[0].incoming_loss, unl):
                raise ValueError("first cover incoming loss must equal UNL")
            for previous, current in zip(
                self.cover_results,
                self.cover_results[1:],
                strict=False,
            ):
                if not _close(previous.outgoing_loss, current.incoming_loss):
                    raise ValueError("cover results must form a sequential waterfall")
            if not _close(self.cover_results[-1].outgoing_loss, subject):
                raise ValueError("final outgoing loss must equal Cat XL subject loss")
        elif not _close(unl, subject):
            raise ValueError("no-cover subject loss must equal UNL")

        calculated_total = math.fsum(
            item.payable_recovery for item in self.cover_results
        )
        if not _close(total, calculated_total):
            raise ValueError("total_inuring_recovery does not reconcile")
        if not _close(unl, total + subject):
            raise ValueError("UNL must equal recovery plus Cat XL subject loss")
