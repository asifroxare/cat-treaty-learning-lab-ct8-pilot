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
    peril: str = "unspecified"
    region: str = "unspecified"
    risks_affected: int = 0

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

        if not isinstance(self.peril, str) or not self.peril.strip():
            raise ValueError("peril must be a non-empty string")

        if not isinstance(self.region, str) or not self.region.strip():
            raise ValueError("region must be a non-empty string")

        if (
            isinstance(self.risks_affected, bool)
            or not isinstance(self.risks_affected, int)
            or self.risks_affected < 0
        ):
            raise ValueError(
                "risks_affected must be a non-negative integer"
            )

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


@dataclass(frozen=True, slots=True)
class CanonicalProcessedEvent:
    """Canonical CT1 view of one processed pricing-engine event."""

    event: CanonicalEvent
    qualifies_under_two_risk_warranty: bool
    covered_loss_before_capacity_100_percent: float
    payable_recovery_before_capacity_constraint: float
    gross_contractual_recovery: float
    capacity_before_event: float
    capacity_consumed: float
    remaining_capacity_before_reinstatement: float
    amount_reinstated: float
    capacity_available_for_next_event: float
    reinstatements_remaining: float
    net_subject_loss: float
    reinstatement_premium_payable: float | None
    settlement: SettlementBreakdown | None
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        if not isinstance(self.event, CanonicalEvent):
            raise ValueError("event must be a CanonicalEvent")
        if not isinstance(self.qualifies_under_two_risk_warranty, bool):
            raise ValueError(
                "qualifies_under_two_risk_warranty must be boolean"
            )

        for field_name, value in (
            (
                "covered_loss_before_capacity_100_percent",
                self.covered_loss_before_capacity_100_percent,
            ),
            (
                "payable_recovery_before_capacity_constraint",
                self.payable_recovery_before_capacity_constraint,
            ),
            (
                "gross_contractual_recovery",
                self.gross_contractual_recovery,
            ),
            ("capacity_before_event", self.capacity_before_event),
            ("capacity_consumed", self.capacity_consumed),
            (
                "remaining_capacity_before_reinstatement",
                self.remaining_capacity_before_reinstatement,
            ),
            ("amount_reinstated", self.amount_reinstated),
            (
                "capacity_available_for_next_event",
                self.capacity_available_for_next_event,
            ),
            ("reinstatements_remaining", self.reinstatements_remaining),
            ("net_subject_loss", self.net_subject_loss),
        ):
            _validate_finite_number(field_name, value, non_negative=True)

        if self.reinstatement_premium_payable is not None:
            _validate_finite_number(
                "reinstatement_premium_payable",
                self.reinstatement_premium_payable,
                non_negative=True,
            )

        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError(
                "capacity_basis must be payable_placed_share in CT1"
            )

        if not math.isclose(
            self.capacity_consumed,
            self.gross_contractual_recovery,
        ):
            raise ValueError(
                "capacity_consumed must equal gross_contractual_recovery"
            )

        if self.reinstatement_premium_payable is None:
            if self.settlement is not None:
                raise ValueError(
                    "settlement must be null until premium is finalized"
                )
        else:
            if not isinstance(self.settlement, SettlementBreakdown):
                raise ValueError(
                    "finalized premium requires SettlementBreakdown"
                )
            if not math.isclose(
                self.settlement.gross_contractual_recovery,
                self.gross_contractual_recovery,
            ):
                raise ValueError(
                    "settlement gross recovery must match event recovery"
                )
            if not math.isclose(
                self.settlement.reinstatement_premium_payable,
                self.reinstatement_premium_payable,
            ):
                raise ValueError(
                    "settlement premium must match event premium"
                )


@dataclass(frozen=True, slots=True)
class CanonicalYearRecord:
    """Canonical CT1 payable view of one annual pricing-engine record."""

    annual_trial_id: int
    event_count: int
    qualifying_event_count: int
    gross_annual_loss: float
    largest_gross_event_loss: float
    gross_contractual_recovery: float
    net_subject_loss: float
    reinstatements_used: float
    maximum_occurrence_recovery: float
    layer_attached: bool
    layer_exhausted: bool
    reinstatement_premium_payable: float | None
    settlement: SettlementBreakdown | None
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    def __post_init__(self) -> None:
        _validate_positive_integer("annual_trial_id", self.annual_trial_id)
        for field_name, value in (
            ("event_count", self.event_count),
            ("qualifying_event_count", self.qualifying_event_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

        if self.qualifying_event_count > self.event_count:
            raise ValueError(
                "qualifying_event_count cannot exceed event_count"
            )

        for field_name, value in (
            ("gross_annual_loss", self.gross_annual_loss),
            ("largest_gross_event_loss", self.largest_gross_event_loss),
            (
                "gross_contractual_recovery",
                self.gross_contractual_recovery,
            ),
            ("net_subject_loss", self.net_subject_loss),
            ("reinstatements_used", self.reinstatements_used),
            (
                "maximum_occurrence_recovery",
                self.maximum_occurrence_recovery,
            ),
        ):
            _validate_finite_number(field_name, value, non_negative=True)

        if not isinstance(self.layer_attached, bool):
            raise ValueError("layer_attached must be boolean")
        if not isinstance(self.layer_exhausted, bool):
            raise ValueError("layer_exhausted must be boolean")
        if self.capacity_basis is not CapacityBasis.PAYABLE_PLACED_SHARE:
            raise ValueError(
                "capacity_basis must be payable_placed_share in CT1"
            )

        if self.reinstatement_premium_payable is not None:
            _validate_finite_number(
                "reinstatement_premium_payable",
                self.reinstatement_premium_payable,
                non_negative=True,
            )

        if self.reinstatement_premium_payable is None:
            if self.settlement is not None:
                raise ValueError(
                    "settlement must be null until premium is finalized"
                )
        elif not isinstance(self.settlement, SettlementBreakdown):
            raise ValueError(
                "finalized annual premium requires SettlementBreakdown"
            )


@dataclass(frozen=True, slots=True)
class CanonicalPricingComponents:
    """Identity view of the validated technical-pricing components."""

    pure_premium: float
    risk_loading: float
    expense_loading: float
    capital_loading: float
    pre_profit_subtotal: float
    profit_loading: float
    original_technical_premium: float

    def __post_init__(self) -> None:
        for field_name in self.__dataclass_fields__:
            _validate_finite_number(
                field_name, getattr(self, field_name), non_negative=True
            )


@dataclass(frozen=True, slots=True)
class CanonicalPremiumMetrics:
    """Identity view of one original or expected-all-in premium basis."""

    premium: float
    rate_on_line: float
    payback_period: float | None
    expected_loss_ratio: float | None
    commercial_rate_on_epi: float | None

    def __post_init__(self) -> None:
        _validate_finite_number("premium", self.premium, non_negative=True)
        _validate_finite_number(
            "rate_on_line", self.rate_on_line, non_negative=True
        )
        for field_name in (
            "payback_period",
            "expected_loss_ratio",
            "commercial_rate_on_epi",
        ):
            value = getattr(self, field_name)
            if value is not None:
                _validate_finite_number(
                    field_name, value, non_negative=True
                )


@dataclass(frozen=True, slots=True)
class CanonicalPricingView:
    """Original-premium and expected-all-in pricing metrics."""

    name: str
    original: CanonicalPremiumMetrics
    expected_reinstatement_premium: float
    expected_all_in: CanonicalPremiumMetrics
    reinstatement_premium_basis: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("pricing view name must be non-empty")
        if not isinstance(self.original, CanonicalPremiumMetrics):
            raise ValueError("original must be CanonicalPremiumMetrics")
        if not isinstance(self.expected_all_in, CanonicalPremiumMetrics):
            raise ValueError(
                "expected_all_in must be CanonicalPremiumMetrics"
            )
        if (
            not isinstance(self.reinstatement_premium_basis, str)
            or not self.reinstatement_premium_basis.strip()
        ):
            raise ValueError(
                "reinstatement_premium_basis must be non-empty"
            )
        _validate_finite_number(
            "expected_reinstatement_premium",
            self.expected_reinstatement_premium,
            non_negative=True,
        )


@dataclass(frozen=True, slots=True)
class CanonicalPricingResult:
    """Numerical-identity snapshot of validated 100% layer pricing."""

    components: CanonicalPricingComponents
    expected_reinstatement_premium: float
    expected_all_in_premium: float
    technical: CanonicalPricingView
    target_rol: CanonicalPricingView | None
    target_payback: CanonicalPricingView | None

    def __post_init__(self) -> None:
        if not isinstance(self.components, CanonicalPricingComponents):
            raise ValueError(
                "components must be CanonicalPricingComponents"
            )
        if not isinstance(self.technical, CanonicalPricingView):
            raise ValueError("technical must be CanonicalPricingView")
        for field_name in ("target_rol", "target_payback"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(
                value, CanonicalPricingView
            ):
                raise ValueError(
                    f"{field_name} must be CanonicalPricingView or null"
                )
        _validate_finite_number(
            "expected_reinstatement_premium",
            self.expected_reinstatement_premium,
            non_negative=True,
        )
        _validate_finite_number(
            "expected_all_in_premium",
            self.expected_all_in_premium,
            non_negative=True,
        )
