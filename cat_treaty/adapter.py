"""Numerical-identity adapters for the validated Cat XOL source records."""

from collections.abc import Iterable
import math
from numbers import Real
from typing import Protocol

from cat_treaty.models import (
    CanonicalEvent,
    CanonicalProcessedEvent,
    SettlementMode,
    TreatyShares,
)
from cat_treaty.settlement import calculate_settlement
from cat_treaty.shares import (
    apply_contractual_shares,
    calculate_share_factor,
)


class PricingEventRecord(Protocol):
    """Structural contract matching cat_xol.models.EventRecord."""

    year: int
    event_id: str
    event_time: float
    event_sequence: int
    peril: str
    region: str
    risks_affected: int
    gross_event_loss: float


class PricingProcessedEventRecord(PricingEventRecord, Protocol):
    """Structural contract matching cat_xol ProcessedEventRecord."""

    qualifies_under_two_risk_warranty: bool
    occurrence_recovery_before_capacity_constraint: float
    capacity_before_event: float
    actual_treaty_recovery: float
    capacity_consumed: float
    remaining_capacity_before_reinstatement: float
    amount_reinstated: float
    reinstatement_premium: float | None
    capacity_available_for_next_event: float
    reinstatements_remaining: float
    net_event_loss: float


_REQUIRED_EVENT_FIELDS = (
    "year",
    "event_id",
    "event_time",
    "event_sequence",
    "peril",
    "region",
    "risks_affected",
    "gross_event_loss",
)

_REQUIRED_PROCESSED_FIELDS = (
    "qualifies_under_two_risk_warranty",
    "occurrence_recovery_before_capacity_constraint",
    "capacity_before_event",
    "actual_treaty_recovery",
    "capacity_consumed",
    "remaining_capacity_before_reinstatement",
    "amount_reinstated",
    "reinstatement_premium",
    "capacity_available_for_next_event",
    "reinstatements_remaining",
    "net_event_loss",
)


def _required_field(source: object, field_name: str) -> object:
    """Read one required structural field with an explicit error."""

    try:
        return getattr(source, field_name)
    except AttributeError as exc:
        raise TypeError(
            f"source event missing required field: {field_name}"
        ) from exc


def adapt_event_record(source: PricingEventRecord) -> CanonicalEvent:
    """Map one validated pricing event without numerical transformation."""

    values = {
        field_name: _required_field(source, field_name)
        for field_name in _REQUIRED_EVENT_FIELDS
    }

    return CanonicalEvent(
        annual_trial_id=values["year"],
        event_id=values["event_id"],
        event_time=values["event_time"],
        event_sequence=values["event_sequence"],
        peril=values["peril"],
        region=values["region"],
        risks_affected=values["risks_affected"],
        subject_loss=values["gross_event_loss"],
    )


def adapt_event_records(
    events: Iterable[PricingEventRecord],
) -> tuple[CanonicalEvent, ...]:
    """Adapt events while enforcing source chronology and identity."""

    try:
        iterator = iter(events)
    except TypeError as exc:
        raise TypeError("events must be iterable") from exc

    adapted_events: list[CanonicalEvent] = []
    event_ids_by_trial: dict[int, set[str]] = {}
    last_order_key_by_trial: dict[int, tuple[float, str]] = {}

    for source_event in iterator:
        event = adapt_event_record(source_event)
        trial_id = event.annual_trial_id

        event_ids = event_ids_by_trial.setdefault(trial_id, set())

        if event.event_id in event_ids:
            raise ValueError(
                "duplicate event_id within annual trial: "
                f"{event.event_id}"
            )

        order_key = (event.event_time, event.event_id)
        previous_order_key = last_order_key_by_trial.get(trial_id)

        if (
            previous_order_key is not None
            and order_key < previous_order_key
        ):
            raise ValueError(
                f"events for annual trial {trial_id} are not "
                "chronologically ordered"
            )

        event_ids.add(event.event_id)
        last_order_key_by_trial[trial_id] = order_key
        adapted_events.append(event)

    return tuple(adapted_events)


def _non_negative_finite(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def _require_close(field_name: str, actual: float, expected: float) -> None:
    if not math.isclose(actual, expected):
        raise ValueError(f"source {field_name} does not reconcile")


def adapt_processed_event_record(
    source: PricingProcessedEventRecord,
    *,
    shares: TreatyShares = TreatyShares(),
    settlement_mode: SettlementMode = SettlementMode.PAID_SEPARATELY,
) -> CanonicalProcessedEvent:
    """Adapt one validated processed event to canonical payable fields."""

    if not isinstance(settlement_mode, SettlementMode):
        raise ValueError(
            "settlement_mode must be a supported SettlementMode"
        )

    event = adapt_event_record(source)
    values = {
        field_name: _required_field(source, field_name)
        for field_name in _REQUIRED_PROCESSED_FIELDS
    }

    qualifies = values["qualifies_under_two_risk_warranty"]
    if not isinstance(qualifies, bool):
        raise ValueError(
            "qualifies_under_two_risk_warranty must be boolean"
        )

    unconstrained = _non_negative_finite(
        "occurrence_recovery_before_capacity_constraint",
        values["occurrence_recovery_before_capacity_constraint"],
    )
    capacity_before = _non_negative_finite(
        "capacity_before_event", values["capacity_before_event"]
    )
    actual_recovery = _non_negative_finite(
        "actual_treaty_recovery", values["actual_treaty_recovery"]
    )
    capacity_consumed = _non_negative_finite(
        "capacity_consumed", values["capacity_consumed"]
    )
    remaining_before = _non_negative_finite(
        "remaining_capacity_before_reinstatement",
        values["remaining_capacity_before_reinstatement"],
    )
    reinstated = _non_negative_finite(
        "amount_reinstated", values["amount_reinstated"]
    )
    capacity_next = _non_negative_finite(
        "capacity_available_for_next_event",
        values["capacity_available_for_next_event"],
    )
    reinstatements_remaining = _non_negative_finite(
        "reinstatements_remaining", values["reinstatements_remaining"]
    )
    legacy_net = _non_negative_finite(
        "net_event_loss", values["net_event_loss"]
    )

    _require_close("capacity_consumed", capacity_consumed, actual_recovery)
    if actual_recovery > unconstrained:
        raise ValueError(
            "actual recovery cannot exceed unconstrained recovery"
        )
    if reinstated > actual_recovery:
        raise ValueError(
            "amount_reinstated cannot exceed actual recovery"
        )
    if not qualifies and (unconstrained != 0 or actual_recovery != 0):
        raise ValueError(
            "nonqualifying event must have zero recovery"
        )
    _require_close(
        "remaining_capacity_before_reinstatement",
        remaining_before,
        capacity_before - actual_recovery,
    )
    _require_close(
        "capacity_available_for_next_event",
        capacity_next,
        remaining_before + reinstated,
    )
    _require_close(
        "net_event_loss",
        legacy_net,
        event.subject_loss - actual_recovery,
    )

    factor = calculate_share_factor(shares)
    gross_recovery = apply_contractual_shares(actual_recovery, shares)
    source_premium = values["reinstatement_premium"]

    if source_premium is None:
        premium_payable = None
        settlement = None
    else:
        validated_premium = _non_negative_finite(
            "reinstatement_premium", source_premium
        )
        premium_payable = apply_contractual_shares(
            validated_premium, shares
        )
        settlement = calculate_settlement(
            gross_contractual_recovery=gross_recovery,
            reinstatement_premium_payable=premium_payable,
            settlement_mode=settlement_mode,
        )

    return CanonicalProcessedEvent(
        event=event,
        qualifies_under_two_risk_warranty=qualifies,
        covered_loss_before_capacity_100_percent=unconstrained,
        payable_recovery_before_capacity_constraint=(
            unconstrained * factor
        ),
        gross_contractual_recovery=gross_recovery,
        capacity_before_event=capacity_before * factor,
        capacity_consumed=capacity_consumed * factor,
        remaining_capacity_before_reinstatement=remaining_before * factor,
        amount_reinstated=reinstated * factor,
        capacity_available_for_next_event=capacity_next * factor,
        reinstatements_remaining=reinstatements_remaining,
        net_subject_loss=event.subject_loss - gross_recovery,
        reinstatement_premium_payable=premium_payable,
        settlement=settlement,
    )
