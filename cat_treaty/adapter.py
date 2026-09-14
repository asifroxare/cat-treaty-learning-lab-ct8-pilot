"""Numerical-identity adapters for the validated Cat XOL source records."""

from collections.abc import Iterable
import math
from numbers import Real
from typing import Protocol

from cat_treaty.models import (
    CanonicalEvent,
    CanonicalPremiumMetrics,
    CanonicalPricingComponents,
    CanonicalPricingResult,
    CanonicalPricingView,
    CanonicalProcessedEvent,
    CanonicalYearRecord,
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


class PricingTreatyYearRecord(Protocol):
    """Structural contract matching cat_xol.models.TreatyYearRecord."""

    year: int
    event_count: int
    qualifying_event_count: int
    gross_annual_loss: float
    largest_gross_event_loss: float
    total_annual_recovery: float
    net_annual_loss: float
    reinstatements_used: float
    total_reinstatement_premium: float | None
    maximum_occurrence_recovery: float
    layer_attached: bool
    layer_exhausted: bool


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

_REQUIRED_YEAR_FIELDS = (
    "year",
    "event_count",
    "qualifying_event_count",
    "gross_annual_loss",
    "largest_gross_event_loss",
    "total_annual_recovery",
    "net_annual_loss",
    "reinstatements_used",
    "total_reinstatement_premium",
    "maximum_occurrence_recovery",
    "layer_attached",
    "layer_exhausted",
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


def _non_negative_integer(field_name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


def adapt_treaty_year_record(
    source: PricingTreatyYearRecord,
    *,
    shares: TreatyShares = TreatyShares(),
    settlement_mode: SettlementMode = SettlementMode.PAID_SEPARATELY,
) -> CanonicalYearRecord:
    """Adapt one annual source record to a canonical payable-share view."""

    if not isinstance(settlement_mode, SettlementMode):
        raise ValueError(
            "settlement_mode must be a supported SettlementMode"
        )

    values = {
        field_name: _required_field(source, field_name)
        for field_name in _REQUIRED_YEAR_FIELDS
    }

    year = values["year"]
    if isinstance(year, bool) or not isinstance(year, int) or year < 1:
        raise ValueError("year must be a positive integer")

    event_count = _non_negative_integer(
        "event_count", values["event_count"]
    )
    qualifying_count = _non_negative_integer(
        "qualifying_event_count", values["qualifying_event_count"]
    )
    if qualifying_count > event_count:
        raise ValueError(
            "qualifying_event_count cannot exceed event_count"
        )

    gross_loss = _non_negative_finite(
        "gross_annual_loss", values["gross_annual_loss"]
    )
    largest_loss = _non_negative_finite(
        "largest_gross_event_loss", values["largest_gross_event_loss"]
    )
    source_recovery = _non_negative_finite(
        "total_annual_recovery", values["total_annual_recovery"]
    )
    source_net = _non_negative_finite(
        "net_annual_loss", values["net_annual_loss"]
    )
    reinstatements_used = _non_negative_finite(
        "reinstatements_used", values["reinstatements_used"]
    )
    maximum_recovery = _non_negative_finite(
        "maximum_occurrence_recovery",
        values["maximum_occurrence_recovery"],
    )

    if largest_loss > gross_loss:
        raise ValueError(
            "largest_gross_event_loss cannot exceed gross_annual_loss"
        )
    if maximum_recovery > source_recovery:
        raise ValueError(
            "maximum_occurrence_recovery cannot exceed total_annual_recovery"
        )
    _require_close(
        "net_annual_loss", source_net, gross_loss - source_recovery
    )

    layer_attached = values["layer_attached"]
    layer_exhausted = values["layer_exhausted"]
    if not isinstance(layer_attached, bool):
        raise ValueError("layer_attached must be boolean")
    if not isinstance(layer_exhausted, bool):
        raise ValueError("layer_exhausted must be boolean")

    factor = calculate_share_factor(shares)
    payable_recovery = apply_contractual_shares(source_recovery, shares)
    source_premium = values["total_reinstatement_premium"]

    if source_premium is None:
        premium_payable = None
        settlement = None
    else:
        validated_premium = _non_negative_finite(
            "total_reinstatement_premium", source_premium
        )
        premium_payable = apply_contractual_shares(
            validated_premium, shares
        )
        settlement = calculate_settlement(
            gross_contractual_recovery=payable_recovery,
            reinstatement_premium_payable=premium_payable,
            settlement_mode=settlement_mode,
        )

    return CanonicalYearRecord(
        annual_trial_id=year,
        event_count=event_count,
        qualifying_event_count=qualifying_count,
        gross_annual_loss=gross_loss,
        largest_gross_event_loss=largest_loss,
        gross_contractual_recovery=payable_recovery,
        net_subject_loss=gross_loss - payable_recovery,
        reinstatements_used=reinstatements_used,
        maximum_occurrence_recovery=maximum_recovery * factor,
        layer_attached=layer_attached,
        layer_exhausted=layer_exhausted,
        reinstatement_premium_payable=premium_payable,
        settlement=settlement,
    )


def _adapt_pricing_components(source: object) -> CanonicalPricingComponents:
    names = (
        "pure_premium",
        "risk_loading",
        "expense_loading",
        "capital_loading",
        "pre_profit_subtotal",
        "profit_loading",
        "original_technical_premium",
    )
    values = {
        name: _non_negative_finite(name, _required_field(source, name))
        for name in names
    }
    return CanonicalPricingComponents(**values)


def _optional_non_negative(field_name: str, value: object) -> float | None:
    if value is None:
        return None
    return _non_negative_finite(field_name, value)


def _adapt_premium_metrics(source: object) -> CanonicalPremiumMetrics:
    return CanonicalPremiumMetrics(
        premium=_non_negative_finite(
            "premium", _required_field(source, "premium")
        ),
        rate_on_line=_non_negative_finite(
            "rate_on_line", _required_field(source, "rate_on_line")
        ),
        payback_period=_optional_non_negative(
            "payback_period", _required_field(source, "payback_period")
        ),
        expected_loss_ratio=_optional_non_negative(
            "expected_loss_ratio",
            _required_field(source, "expected_loss_ratio"),
        ),
        commercial_rate_on_epi=_optional_non_negative(
            "commercial_rate_on_epi",
            _required_field(source, "commercial_rate_on_epi"),
        ),
    )


def _adapt_pricing_view(source: object) -> CanonicalPricingView:
    name = _required_field(source, "name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("pricing view name must be non-empty")
    premium_basis = _required_field(
        source, "reinstatement_premium_basis"
    )
    if not isinstance(premium_basis, str) or not premium_basis.strip():
        raise ValueError(
            "reinstatement_premium_basis must be non-empty"
        )

    original = _adapt_premium_metrics(_required_field(source, "original"))
    expected_reinstatement = _non_negative_finite(
        "expected_reinstatement_premium",
        _required_field(source, "expected_reinstatement_premium"),
    )
    expected_all_in = _adapt_premium_metrics(
        _required_field(source, "expected_all_in")
    )
    _require_close(
        "expected_all_in premium",
        expected_all_in.premium,
        original.premium + expected_reinstatement,
    )

    return CanonicalPricingView(
        name=name,
        original=original,
        expected_reinstatement_premium=expected_reinstatement,
        expected_all_in=expected_all_in,
        reinstatement_premium_basis=premium_basis,
    )


def adapt_pricing_result(source: object) -> CanonicalPricingResult:
    """Map the validated 100% pricing result without repricing."""

    required = (
        "components",
        "expected_reinstatement_premium",
        "expected_all_in_premium",
        "technical",
        "target_rol",
        "target_payback",
    )
    values = {name: _required_field(source, name) for name in required}

    components = _adapt_pricing_components(values["components"])
    expected_reinstatement = _non_negative_finite(
        "expected_reinstatement_premium",
        values["expected_reinstatement_premium"],
    )
    expected_all_in = _non_negative_finite(
        "expected_all_in_premium", values["expected_all_in_premium"]
    )
    technical = _adapt_pricing_view(values["technical"])
    target_rol = (
        None
        if values["target_rol"] is None
        else _adapt_pricing_view(values["target_rol"])
    )
    target_payback = (
        None
        if values["target_payback"] is None
        else _adapt_pricing_view(values["target_payback"])
    )

    _require_close(
        "expected_all_in_premium",
        expected_all_in,
        components.original_technical_premium + expected_reinstatement,
    )
    _require_close(
        "technical original premium",
        technical.original.premium,
        components.original_technical_premium,
    )
    _require_close(
        "technical expected_reinstatement_premium",
        technical.expected_reinstatement_premium,
        expected_reinstatement,
    )
    _require_close(
        "technical expected_all_in",
        technical.expected_all_in.premium,
        expected_all_in,
    )

    return CanonicalPricingResult(
        components=components,
        expected_reinstatement_premium=expected_reinstatement,
        expected_all_in_premium=expected_all_in,
        technical=technical,
        target_rol=target_rol,
        target_payback=target_payback,
    )
