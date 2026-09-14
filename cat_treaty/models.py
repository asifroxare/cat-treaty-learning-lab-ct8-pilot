"""Canonical immutable domain models for CT1.

This module validates and stores contractual values. It does not perform
occurrence recovery, share, capacity, reinstatement, or settlement calculations.
"""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real


class CapacityBasis(str, Enum):
    """Supported treaty-capacity measurement basis."""

    PAYABLE_PLACED_SHARE = "payable_placed_share"


class CapacityUtilizationStatus(str, Enum):
    """Whether capacity utilization has a meaningful denominator."""

    APPLICABLE = "applicable"
    NOT_APPLICABLE_ZERO_CAPACITY = "not_applicable_zero_capacity"


class SettlementMode(str, Enum):
    """How reinstatement premium is presented in the cash settlement."""

    PAID_SEPARATELY = "paid_separately"
    DEDUCTED_FROM_SETTLEMENT = "deducted_from_settlement"


def _validate_finite_number(
    field_name: str,
    value: Real,
    *,
    non_negative: bool,
) -> None:
    """Require a real, finite number and optionally prohibit negatives."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")

    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")

    if non_negative and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_positive_integer(field_name: str, value: int) -> None:
    """Require a positive integer while rejecting booleans."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class TreatyShares:
    """Shares fixed for the complete annual trial in CT1."""

    ceded_share: float = 1.0
    placement_share: float = 1.0

    def __post_init__(self) -> None:
        for field_name, value in (
            ("ceded_share", self.ceded_share),
            ("placement_share", self.placement_share),
        ):
            _validate_finite_number(
                field_name,
                value,
                non_negative=True,
            )
            if value > 1:
                raise ValueError(
                    f"{field_name} must lie in the closed interval [0, 1]"
                )


@dataclass(frozen=True, slots=True)
class CanonicalEvent:
    """Canonical CT0 event record used by the compatibility boundary."""

    annual_trial_id: int
    event_id: str
    event_time: float
    event_sequence: int
    subject_loss: float

    def __post_init__(self) -> None:
        _validate_positive_integer(
            "annual_trial_id",
            self.annual_trial_id,
        )
        _validate_positive_integer(
            "event_sequence",
            self.event_sequence,
        )

        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        _validate_finite_number(
            "event_time",
            self.event_time,
            non_negative=True,
        )
        _validate_finite_number(
            "subject_loss",
            self.subject_loss,
            non_negative=True,
        )


@dataclass(frozen=True, slots=True)
class CapacityState:
    """Validated payable-placed capacity state for one ledger step."""

    initial_capacity: float
    available_before: float
    consumed: float
    reinstated: float
    remaining: float
    capacity_utilization: float | None
    capacity_utilization_status: CapacityUtilizationStatus
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        for field_name, value in (
            ("initial_capacity", self.initial_capacity),
            ("available_before", self.available_before),
            ("consumed", self.consumed),
            ("reinstated", self.reinstated),
            ("remaining", self.remaining),
        ):
            _validate_finite_number(
                field_name,
                value,
                non_negative=True,
            )

        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError(
                "capacity_basis must be payable_placed_share in CT1"
            )

        if not isinstance(
            self.capacity_utilization_status,
            CapacityUtilizationStatus,
        ):
            raise ValueError(
                "capacity_utilization_status must be a supported status"
            )

        if self.initial_capacity == 0:
            self._validate_zero_capacity_state()
        else:
            self._validate_positive_capacity_state()

    def _validate_zero_capacity_state(self) -> None:
        """Enforce the frozen CT1 zero-capacity convention."""

        if any(
            value != 0
            for value in (
                self.available_before,
                self.consumed,
                self.reinstated,
                self.remaining,
            )
        ):
            raise ValueError(
                "all capacity values must be zero when initial capacity is zero"
            )

        if self.capacity_utilization is not None:
            raise ValueError(
                "capacity_utilization must be null for zero capacity"
            )

        if (
            self.capacity_utilization_status
            is not CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
        ):
            raise ValueError(
                "zero capacity requires not_applicable_zero_capacity status"
            )

    def _validate_positive_capacity_state(self) -> None:
        """Require an applicable finite utilization for positive capacity."""

        if (
            self.capacity_utilization_status
            is not CapacityUtilizationStatus.APPLICABLE
        ):
            raise ValueError(
                "positive capacity requires applicable utilization status"
            )

        if self.capacity_utilization is None:
            raise ValueError(
                "positive capacity requires capacity_utilization"
            )

        _validate_finite_number(
            "capacity_utilization",
            self.capacity_utilization,
            non_negative=True,
        )

        if self.capacity_utilization > 1:
            raise ValueError(
                "capacity_utilization must lie in the closed interval [0, 1]"
            )


@dataclass(frozen=True, slots=True)
class SettlementBreakdown:
    """Three-way settlement record required by CT1."""

    gross_contractual_recovery: float
    reinstatement_premium_payable: float
    net_cash_settlement: float
    settlement_mode: SettlementMode

    def __post_init__(self) -> None:
        _validate_finite_number(
            "gross_contractual_recovery",
            self.gross_contractual_recovery,
            non_negative=True,
        )
        _validate_finite_number(
            "reinstatement_premium_payable",
            self.reinstatement_premium_payable,
            non_negative=True,
        )
        _validate_finite_number(
            "net_cash_settlement",
            self.net_cash_settlement,
            non_negative=False,
        )

        if not isinstance(self.settlement_mode, SettlementMode):
            raise ValueError(
                "settlement_mode must be a supported SettlementMode"
            )