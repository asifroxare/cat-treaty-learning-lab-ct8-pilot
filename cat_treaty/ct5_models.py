"""Immutable CT5 annual-capacity, reinstatement, and settlement contracts.

This module owns validation and state shape only.  F25--F37 calculations are
implemented by later CT5 checkpoints.
"""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real

from cat_treaty.models import CapacityBasis, SettlementMode


RELATIVE_TOLERANCE = 1e-12
ABSOLUTE_CURRENCY_TOLERANCE = 1e-6


class ReinstatementTimeBasis(str, Enum):
    FULL_TIME = "full_time"
    PRO_RATA_REMAINING_TERM = "pro_rata_remaining_term"


class ReinstatementChargeType(str, Enum):
    FREE = "free"
    PAID = "paid"


class CT5UtilizationStatus(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE_ZERO_CAPACITY = "not_applicable_zero_capacity"
    NOT_APPLICABLE_NO_REINSTATEMENT_CAPACITY = (
        "not_applicable_no_reinstatement_capacity"
    )


class CT5MetricPerspective(str, Enum):
    SUBJECT = "subject"
    GROSS_RECOVERY_POST_ANNUAL_CAPACITY = (
        "gross_recovery_post_annual_capacity"
    )
    INSURER_NET_POST_ANNUAL_CAPACITY = "insurer_net_post_annual_capacity"
    REINSTATEMENT_PREMIUM_PAYABLE = "reinstatement_premium_payable"
    NET_CASH_SETTLEMENT = "net_cash_settlement"
    CAPACITY_CONSTRAINED_RECOVERY_SHORTFALL = (
        "capacity_constrained_recovery_shortfall"
    )


def _nonblank(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _finite(
    name: str,
    value: object,
    *,
    non_negative: bool = True,
    positive: bool = False,
) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if positive and result <= 0:
        raise ValueError(f"{name} must be greater than zero")
    if non_negative and result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _enum(name: str, value: object, enum_type: type[Enum]) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{name} must be a supported {enum_type.__name__}")


def _tuple_of(name: str, values: object, item_type: type[object]) -> None:
    if not isinstance(values, tuple) or not all(
        isinstance(item, item_type) for item in values
    ):
        raise ValueError(f"{name} must contain {item_type.__name__} values")


def _strings(name: str, values: object, *, allow_empty: bool = True) -> None:
    if (
        not isinstance(values, tuple)
        or (not allow_empty and not values)
        or not all(isinstance(item, str) and item.strip() for item in values)
    ):
        raise ValueError(f"{name} must contain non-empty strings")


def _unique(name: str, values: tuple[object, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{name} values must be unique")


def _close(left: float, right: float) -> bool:
    return math.isclose(
        left,
        right,
        rel_tol=RELATIVE_TOLERANCE,
        abs_tol=ABSOLUTE_CURRENCY_TOLERANCE,
    )


@dataclass(frozen=True, slots=True)
class ReinstatementTranche:
    sequence: int
    premium_rate: float
    time_basis: ReinstatementTimeBasis
    charge_type: ReinstatementChargeType
    source_reference: str
    rule_reference: str

    def __post_init__(self) -> None:
        _positive_int("sequence", self.sequence)
        rate = _finite("premium_rate", self.premium_rate)
        _enum("time_basis", self.time_basis, ReinstatementTimeBasis)
        _enum("charge_type", self.charge_type, ReinstatementChargeType)
        _nonblank("source_reference", self.source_reference)
        _nonblank("rule_reference", self.rule_reference)
        if self.charge_type is ReinstatementChargeType.FREE and rate != 0:
            raise ValueError("free tranche requires zero premium_rate")
        if self.charge_type is ReinstatementChargeType.PAID and rate <= 0:
            raise ValueError("paid tranche requires positive premium_rate")


@dataclass(frozen=True, slots=True)
class CT5LayerTerms:
    layer_id: str
    original_layer_premium: float
    premium_basis_declaration: str
    reinstatement_tranches: tuple[ReinstatementTranche, ...]
    treaty_term_start: float
    treaty_term_end: float
    settlement_mode: SettlementMode
    source_reference: str
    rule_reference: str
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        _nonblank("layer_id", self.layer_id)
        _finite("original_layer_premium", self.original_layer_premium)
        _nonblank("premium_basis_declaration", self.premium_basis_declaration)
        _tuple_of(
            "reinstatement_tranches",
            self.reinstatement_tranches,
            ReinstatementTranche,
        )
        sequences = tuple(item.sequence for item in self.reinstatement_tranches)
        if sequences != tuple(range(1, len(sequences) + 1)):
            raise ValueError("tranche sequences must be contiguous from one")
        start = _finite("treaty_term_start", self.treaty_term_start)
        end = _finite("treaty_term_end", self.treaty_term_end)
        if end <= start:
            raise ValueError("treaty_term_end must exceed treaty_term_start")
        _enum("settlement_mode", self.settlement_mode, SettlementMode)
        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError("CT5 capacity_basis must be payable_placed_share")
        _nonblank("source_reference", self.source_reference)
        _nonblank("rule_reference", self.rule_reference)


@dataclass(frozen=True, slots=True)
class CT5TreatyTerms:
    program_id: str
    layer_terms: tuple[CT5LayerTerms, ...]
    source_reference: str
    rule_reference: str

    def __post_init__(self) -> None:
        _nonblank("program_id", self.program_id)
        _tuple_of("layer_terms", self.layer_terms, CT5LayerTerms)
        if not 1 <= len(self.layer_terms) <= 4:
            raise ValueError("CT5 requires one to four layer term records")
        _unique("layer_id", tuple(item.layer_id for item in self.layer_terms))
        _nonblank("source_reference", self.source_reference)
        _nonblank("rule_reference", self.rule_reference)


@dataclass(frozen=True, slots=True)
class CT5CapacityState:
    layer_id: str
    annual_trial_id: int
    completed_event_count: int
    initial_capacity: float
    active_capacity: float
    initial_reinstatement_reserve: float
    remaining_reinstatement_reserve: float
    cumulative_recovery: float
    cumulative_reinstated: float
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        _nonblank("layer_id", self.layer_id)
        _positive_int("annual_trial_id", self.annual_trial_id)
        if (
            isinstance(self.completed_event_count, bool)
            or not isinstance(self.completed_event_count, int)
            or self.completed_event_count < 0
        ):
            raise ValueError("completed_event_count must be a non-negative integer")
        values = {
            name: _finite(name, getattr(self, name))
            for name in (
                "initial_capacity",
                "active_capacity",
                "initial_reinstatement_reserve",
                "remaining_reinstatement_reserve",
                "cumulative_recovery",
                "cumulative_reinstated",
            )
        }
        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError("CT5 capacity_basis must be payable_placed_share")
        if values["active_capacity"] > values["initial_capacity"] and not _close(
            values["active_capacity"], values["initial_capacity"]
        ):
            raise ValueError("active_capacity cannot exceed initial_capacity")
        if values["remaining_reinstatement_reserve"] > values[
            "initial_reinstatement_reserve"
        ] and not _close(
            values["remaining_reinstatement_reserve"],
            values["initial_reinstatement_reserve"],
        ):
            raise ValueError("remaining reserve cannot exceed initial reserve")
        if not _close(
            values["initial_capacity"]
            + values["cumulative_reinstated"]
            - values["cumulative_recovery"],
            values["active_capacity"],
        ):
            raise ValueError("capacity state fails F34 reconciliation")
        if not _close(
            values["initial_reinstatement_reserve"]
            - values["cumulative_reinstated"],
            values["remaining_reinstatement_reserve"],
        ):
            raise ValueError("capacity state fails F35 reconciliation")
        if self.completed_event_count == 0 and (
            values["cumulative_recovery"] != 0
            or values["cumulative_reinstated"] != 0
            or not _close(values["active_capacity"], values["initial_capacity"])
            or not _close(
                values["remaining_reinstatement_reserve"],
                values["initial_reinstatement_reserve"],
            )
        ):
            raise ValueError("initial state cannot contain annual activity")


@dataclass(frozen=True, slots=True)
class TrancheAllocation:
    tranche_sequence: int
    capacity_before: float
    amount_used: float
    capacity_after: float
    premium_rate: float
    time_basis: ReinstatementTimeBasis
    time_factor: float
    reinstatement_premium_payable: float
    rule_reference: str

    def __post_init__(self) -> None:
        _positive_int("tranche_sequence", self.tranche_sequence)
        before = _finite("capacity_before", self.capacity_before)
        used = _finite("amount_used", self.amount_used)
        after = _finite("capacity_after", self.capacity_after)
        _finite("premium_rate", self.premium_rate)
        _enum("time_basis", self.time_basis, ReinstatementTimeBasis)
        factor = _finite("time_factor", self.time_factor)
        if factor > 1:
            raise ValueError("time_factor must lie in [0, 1]")
        _finite(
            "reinstatement_premium_payable",
            self.reinstatement_premium_payable,
        )
        _nonblank("rule_reference", self.rule_reference)
        if used > before and not _close(used, before):
            raise ValueError("amount_used cannot exceed tranche capacity_before")
        if not _close(before, used + after):
            raise ValueError("tranche allocation does not reconcile")
        if self.time_basis is ReinstatementTimeBasis.FULL_TIME and factor != 1:
            raise ValueError("full_time allocation requires time_factor 1")


@dataclass(frozen=True, slots=True)
class CT5Settlement:
    gross_contractual_recovery: float
    reinstatement_premium_payable: float
    net_cash_settlement: float
    settlement_mode: SettlementMode

    def __post_init__(self) -> None:
        gross = _finite(
            "gross_contractual_recovery", self.gross_contractual_recovery
        )
        premium = _finite(
            "reinstatement_premium_payable",
            self.reinstatement_premium_payable,
        )
        cash = _finite(
            "net_cash_settlement",
            self.net_cash_settlement,
            non_negative=False,
        )
        _enum("settlement_mode", self.settlement_mode, SettlementMode)
        expected = (
            gross
            if self.settlement_mode is SettlementMode.PAID_SEPARATELY
            else gross - premium
        )
        if not _close(cash, expected):
            raise ValueError("settlement does not reconcile under F31")


@dataclass(frozen=True, slots=True)
class CT5LayerEventLedgerRow:
    annual_trial_id: int
    occurrence_sequence: int
    event_id: str
    layer_id: str
    pre_annual_capacity_recovery: float
    active_capacity_before: float
    reinstatement_reserve_before: float
    gross_contractual_recovery: float
    capacity_constrained_recovery_shortfall: float
    active_capacity_after_recovery: float
    amount_reinstated: float
    active_capacity_for_next_event: float
    reinstatement_reserve_after: float
    tranche_allocations: tuple[TrancheAllocation, ...]
    reinstatement_premium_payable: float
    trace_references: tuple[str, ...]
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _positive_int("occurrence_sequence", self.occurrence_sequence)
        _nonblank("event_id", self.event_id)
        _nonblank("layer_id", self.layer_id)
        pre = _finite(
            "pre_annual_capacity_recovery", self.pre_annual_capacity_recovery
        )
        active_before = _finite("active_capacity_before", self.active_capacity_before)
        reserve_before = _finite(
            "reinstatement_reserve_before", self.reinstatement_reserve_before
        )
        recovery = _finite(
            "gross_contractual_recovery", self.gross_contractual_recovery
        )
        shortfall = _finite(
            "capacity_constrained_recovery_shortfall",
            self.capacity_constrained_recovery_shortfall,
        )
        after_recovery = _finite(
            "active_capacity_after_recovery", self.active_capacity_after_recovery
        )
        reinstated = _finite("amount_reinstated", self.amount_reinstated)
        next_active = _finite(
            "active_capacity_for_next_event", self.active_capacity_for_next_event
        )
        reserve_after = _finite(
            "reinstatement_reserve_after", self.reinstatement_reserve_after
        )
        premium = _finite(
            "reinstatement_premium_payable",
            self.reinstatement_premium_payable,
        )
        _tuple_of("tranche_allocations", self.tranche_allocations, TrancheAllocation)
        _strings("trace_references", self.trace_references, allow_empty=False)
        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError("CT5 capacity_basis must be payable_placed_share")
        for actual, expected, message in (
            (pre, recovery + shortfall, "pre-capacity recovery"),
            (active_before, recovery + after_recovery, "active capacity"),
            (next_active, after_recovery + reinstated, "restored capacity"),
            (reserve_before, reserve_after + reinstated, "reinstatement reserve"),
            (
                reinstated,
                math.fsum(item.amount_used for item in self.tranche_allocations),
                "tranche usage",
            ),
            (
                premium,
                math.fsum(
                    item.reinstatement_premium_payable
                    for item in self.tranche_allocations
                ),
                "tranche premium",
            ),
        ):
            if not _close(actual, expected):
                raise ValueError(f"{message} does not reconcile")
        sequences = tuple(item.tranche_sequence for item in self.tranche_allocations)
        if sequences != tuple(sorted(sequences)) or len(sequences) != len(set(sequences)):
            raise ValueError("tranche allocations must be unique and ordered")


@dataclass(frozen=True, slots=True)
class CT5EventLedgerRow:
    annual_trial_id: int
    occurrence_sequence: int
    event_id: str
    subject_loss: float
    gross_contractual_recovery_pre_annual_capacity: float
    gross_contractual_recovery: float
    capacity_constrained_recovery_shortfall: float
    insurer_net_subject_loss: float
    reinstatement_premium_payable: float
    net_cash_settlement: float
    settlement_mode: SettlementMode
    layer_rows: tuple[CT5LayerEventLedgerRow, ...]
    reconciliation_passed: bool
    trace_references: tuple[str, ...]

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _positive_int("occurrence_sequence", self.occurrence_sequence)
        _nonblank("event_id", self.event_id)
        subject = _finite("subject_loss", self.subject_loss)
        pre = _finite(
            "gross_contractual_recovery_pre_annual_capacity",
            self.gross_contractual_recovery_pre_annual_capacity,
        )
        gross = _finite("gross_contractual_recovery", self.gross_contractual_recovery)
        shortfall = _finite(
            "capacity_constrained_recovery_shortfall",
            self.capacity_constrained_recovery_shortfall,
        )
        net = _finite("insurer_net_subject_loss", self.insurer_net_subject_loss)
        premium = _finite(
            "reinstatement_premium_payable",
            self.reinstatement_premium_payable,
        )
        cash = _finite(
            "net_cash_settlement", self.net_cash_settlement, non_negative=False
        )
        _enum("settlement_mode", self.settlement_mode, SettlementMode)
        _tuple_of("layer_rows", self.layer_rows, CT5LayerEventLedgerRow)
        if not self.layer_rows:
            raise ValueError("event ledger requires layer rows")
        _unique("layer_id", tuple(item.layer_id for item in self.layer_rows))
        if any(
            item.annual_trial_id != self.annual_trial_id
            or item.occurrence_sequence != self.occurrence_sequence
            or item.event_id != self.event_id
            for item in self.layer_rows
        ):
            raise ValueError("layer row identity must match the event row")
        _strings("trace_references", self.trace_references, allow_empty=False)
        if not isinstance(self.reconciliation_passed, bool) or not self.reconciliation_passed:
            raise ValueError("completed event ledger requires passed reconciliation")
        checks = (
            (pre, math.fsum(item.pre_annual_capacity_recovery for item in self.layer_rows), "pre-capacity recovery"),
            (gross, math.fsum(item.gross_contractual_recovery for item in self.layer_rows), "gross recovery"),
            (shortfall, pre - gross, "capacity shortfall"),
            (subject, gross + net, "F32 subject loss"),
            (premium, math.fsum(item.reinstatement_premium_payable for item in self.layer_rows), "premium"),
        )
        for actual, expected, message in checks:
            if not _close(actual, expected):
                raise ValueError(f"{message} does not reconcile")
        CT5Settlement(gross, premium, cash, self.settlement_mode)


@dataclass(frozen=True, slots=True)
class CT5LayerAnnualSummary:
    annual_trial_id: int
    layer_id: str
    initial_capacity: float
    initial_reinstatement_reserve: float
    total_recovery: float
    total_reinstated: float
    final_active_capacity: float
    final_reinstatement_reserve: float
    realized_capacity_utilization: float | None
    realized_capacity_utilization_status: CT5UtilizationStatus
    reinstatement_reserve_utilization: float | None
    reinstatement_reserve_utilization_status: CT5UtilizationStatus

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _nonblank("layer_id", self.layer_id)
        values = {
            name: _finite(name, getattr(self, name))
            for name in (
                "initial_capacity",
                "initial_reinstatement_reserve",
                "total_recovery",
                "total_reinstated",
                "final_active_capacity",
                "final_reinstatement_reserve",
            )
        }
        for name in (
            "realized_capacity_utilization_status",
            "reinstatement_reserve_utilization_status",
        ):
            _enum(name, getattr(self, name), CT5UtilizationStatus)
        if not _close(
            values["initial_capacity"] + values["total_reinstated"] - values["total_recovery"],
            values["final_active_capacity"],
        ):
            raise ValueError("annual layer summary fails F34")
        if not _close(
            values["initial_reinstatement_reserve"] - values["total_reinstated"],
            values["final_reinstatement_reserve"],
        ):
            raise ValueError("annual layer summary fails F35")
        self._validate_utilization(
            "realized_capacity_utilization",
            self.realized_capacity_utilization,
            self.realized_capacity_utilization_status,
            values["initial_capacity"] + values["total_reinstated"],
            values["total_recovery"],
            CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY,
        )
        reserve_na = (
            CT5UtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
            if values["initial_capacity"] == 0
            else CT5UtilizationStatus.NOT_APPLICABLE_NO_REINSTATEMENT_CAPACITY
        )
        self._validate_utilization(
            "reinstatement_reserve_utilization",
            self.reinstatement_reserve_utilization,
            self.reinstatement_reserve_utilization_status,
            values["initial_reinstatement_reserve"],
            values["total_reinstated"],
            reserve_na,
        )

    @staticmethod
    def _validate_utilization(
        name: str,
        value: float | None,
        status: CT5UtilizationStatus,
        denominator: float,
        numerator: float,
        zero_status: CT5UtilizationStatus,
    ) -> None:
        if denominator == 0:
            if value is not None or status is not zero_status:
                raise ValueError(f"{name} requires null and {zero_status.value}")
            return
        if status is not CT5UtilizationStatus.APPLICABLE or value is None:
            raise ValueError(f"{name} requires an applicable value")
        ratio = _finite(name, value)
        if ratio > 1 or not _close(ratio, numerator / denominator):
            raise ValueError(f"{name} does not match its frozen denominator")


@dataclass(frozen=True, slots=True)
class CT5AnnualLedgerRow:
    annual_trial_id: int
    event_rows: tuple[CT5EventLedgerRow, ...]
    layer_summaries: tuple[CT5LayerAnnualSummary, ...]
    subject_loss: float
    gross_contractual_recovery: float
    capacity_constrained_recovery_shortfall: float
    insurer_net_subject_loss: float
    reinstatement_premium_payable: float
    net_cash_settlement: float
    maximum_occurrence_recovery: float
    reconciliation_passed: bool

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _tuple_of("event_rows", self.event_rows, CT5EventLedgerRow)
        _tuple_of("layer_summaries", self.layer_summaries, CT5LayerAnnualSummary)
        if any(item.annual_trial_id != self.annual_trial_id for item in self.event_rows):
            raise ValueError("event row annual_trial_id must match annual ledger")
        if any(item.annual_trial_id != self.annual_trial_id for item in self.layer_summaries):
            raise ValueError("layer summary annual_trial_id must match annual ledger")
        sequences = tuple(item.occurrence_sequence for item in self.event_rows)
        if sequences != tuple(range(1, len(sequences) + 1)):
            raise ValueError("event sequence must be contiguous from one")
        _unique("event_id", tuple(item.event_id for item in self.event_rows))
        _unique("layer_id", tuple(item.layer_id for item in self.layer_summaries))
        values = {
            name: _finite(
                name,
                getattr(self, name),
                non_negative=name != "net_cash_settlement",
            )
            for name in (
                "subject_loss",
                "gross_contractual_recovery",
                "capacity_constrained_recovery_shortfall",
                "insurer_net_subject_loss",
                "reinstatement_premium_payable",
                "net_cash_settlement",
                "maximum_occurrence_recovery",
            )
        }
        if not isinstance(self.reconciliation_passed, bool) or not self.reconciliation_passed:
            raise ValueError("completed annual ledger requires passed reconciliation")
        for field in (
            "subject_loss",
            "gross_contractual_recovery",
            "capacity_constrained_recovery_shortfall",
            "insurer_net_subject_loss",
            "reinstatement_premium_payable",
            "net_cash_settlement",
        ):
            expected = math.fsum(getattr(item, field) for item in self.event_rows)
            if not _close(values[field], expected):
                raise ValueError(f"annual {field} does not reconcile")
        expected_oep = max(
            (item.gross_contractual_recovery for item in self.event_rows),
            default=0.0,
        )
        if not _close(values["maximum_occurrence_recovery"], expected_oep):
            raise ValueError("maximum_occurrence_recovery does not reconcile")
        if not _close(
            values["subject_loss"],
            values["gross_contractual_recovery"]
            + values["insurer_net_subject_loss"],
        ):
            raise ValueError("annual F33 subject loss does not reconcile")

