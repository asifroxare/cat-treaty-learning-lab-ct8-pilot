"""Contract tests for CT1 canonical domain models."""

from dataclasses import FrozenInstanceError
import math

import pytest

from cat_treaty.models import (
    CapacityBasis,
    CapacityState,
    CapacityUtilizationStatus,
    CanonicalEvent,
    SettlementBreakdown,
    SettlementMode,
    TreatyShares,
)


def test_enum_values_are_frozen_contract_literals() -> None:
    assert CapacityBasis.PAYABLE_PLACED_SHARE.value == "payable_placed_share"
    assert CapacityUtilizationStatus.APPLICABLE.value == "applicable"
    assert (
        CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY.value
        == "not_applicable_zero_capacity"
    )
    assert SettlementMode.PAID_SEPARATELY.value == "paid_separately"
    assert (
        SettlementMode.DEDUCTED_FROM_SETTLEMENT.value
        == "deducted_from_settlement"
    )


def test_treaty_shares_default_to_full_compatibility() -> None:
    shares = TreatyShares()

    assert shares.ceded_share == 1.0
    assert shares.placement_share == 1.0


@pytest.mark.parametrize(
    ("ceded_share", "placement_share"),
    [
        (0.0, 0.0),
        (0.0, 1.0),
        (1.0, 0.0),
        (1.0, 1.0),
        (0.9, 0.75),
    ],
)
def test_treaty_shares_accept_closed_interval(
    ceded_share: float,
    placement_share: float,
) -> None:
    shares = TreatyShares(
        ceded_share=ceded_share,
        placement_share=placement_share,
    )

    assert shares.ceded_share == ceded_share
    assert shares.placement_share == placement_share


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("ceded_share", -0.01),
        ("ceded_share", 1.01),
        ("ceded_share", math.nan),
        ("ceded_share", math.inf),
        ("placement_share", -0.01),
        ("placement_share", 1.01),
        ("placement_share", math.nan),
        ("placement_share", math.inf),
    ],
)
def test_treaty_shares_reject_invalid_values(
    field_name: str,
    invalid_value: float,
) -> None:
    values = {
        "ceded_share": 1.0,
        "placement_share": 1.0,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        TreatyShares(**values)


def test_treaty_shares_are_immutable() -> None:
    shares = TreatyShares()

    with pytest.raises(FrozenInstanceError):
        shares.ceded_share = 0.5  # type: ignore[misc]


def test_canonical_event_accepts_valid_values() -> None:
    event = CanonicalEvent(
        annual_trial_id=1,
        event_id="EVT-0001",
        event_time=123.5,
        event_sequence=1,
        subject_loss=2_500_000.0,
    )

    assert event.annual_trial_id == 1
    assert event.event_id == "EVT-0001"
    assert event.event_time == 123.5
    assert event.event_sequence == 1
    assert event.subject_loss == 2_500_000.0


@pytest.mark.parametrize(
    "changes",
    [
        {"annual_trial_id": 0},
        {"event_id": ""},
        {"event_id": "   "},
        {"event_time": -0.01},
        {"event_time": math.nan},
        {"event_time": math.inf},
        {"event_sequence": 0},
        {"subject_loss": -0.01},
        {"subject_loss": math.nan},
        {"subject_loss": math.inf},
    ],
)
def test_canonical_event_rejects_invalid_values(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "event_id": "EVT-0001",
        "event_time": 10.0,
        "event_sequence": 1,
        "subject_loss": 1_000_000.0,
    }
    values.update(changes)

    with pytest.raises(ValueError):
        CanonicalEvent(**values)


def test_zero_capacity_requires_explicit_not_applicable_state() -> None:
    state = CapacityState(
        initial_capacity=0.0,
        available_before=0.0,
        consumed=0.0,
        reinstated=0.0,
        remaining=0.0,
        capacity_utilization=None,
        capacity_utilization_status=(
            CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
        ),
    )

    assert state.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE
    assert state.capacity_utilization is None


@pytest.mark.parametrize(
    "changes",
    [
        {"capacity_utilization": 0.0},
        {
            "capacity_utilization_status":
                CapacityUtilizationStatus.APPLICABLE
        },
        {"consumed": 1.0},
        {"reinstated": 1.0},
        {"remaining": 1.0},
    ],
)
def test_zero_capacity_rejects_false_or_nonzero_state(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "initial_capacity": 0.0,
        "available_before": 0.0,
        "consumed": 0.0,
        "reinstated": 0.0,
        "remaining": 0.0,
        "capacity_utilization": None,
        "capacity_utilization_status": (
            CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
        ),
    }
    values.update(changes)

    with pytest.raises(ValueError):
        CapacityState(**values)


def test_positive_capacity_requires_applicable_finite_utilization() -> None:
    state = CapacityState(
        initial_capacity=1_000_000.0,
        available_before=1_000_000.0,
        consumed=250_000.0,
        reinstated=0.0,
        remaining=750_000.0,
        capacity_utilization=0.25,
        capacity_utilization_status=(
            CapacityUtilizationStatus.APPLICABLE
        ),
    )

    assert state.capacity_utilization == 0.25


@pytest.mark.parametrize(
    "capacity_utilization",
    [None, -0.01, 1.01, math.nan, math.inf],
)
def test_positive_capacity_rejects_invalid_utilization(
    capacity_utilization: float | None,
) -> None:
    with pytest.raises(ValueError):
        CapacityState(
            initial_capacity=1_000_000.0,
            available_before=1_000_000.0,
            consumed=250_000.0,
            reinstated=0.0,
            remaining=750_000.0,
            capacity_utilization=capacity_utilization,
            capacity_utilization_status=(
                CapacityUtilizationStatus.APPLICABLE
            ),
        )


def test_settlement_breakdown_accepts_paid_separately() -> None:
    result = SettlementBreakdown(
        gross_contractual_recovery=500_000.0,
        reinstatement_premium_payable=25_000.0,
        net_cash_settlement=500_000.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
    )

    assert result.net_cash_settlement == 500_000.0


def test_settlement_model_does_not_silently_clamp_negative_cash() -> None:
    result = SettlementBreakdown(
        gross_contractual_recovery=10_000.0,
        reinstatement_premium_payable=15_000.0,
        net_cash_settlement=-5_000.0,
        settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT,
    )

    assert result.net_cash_settlement == -5_000.0


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        ("gross_contractual_recovery", -1.0),
        ("gross_contractual_recovery", math.nan),
        ("reinstatement_premium_payable", -1.0),
        ("reinstatement_premium_payable", math.inf),
        ("net_cash_settlement", math.nan),
        ("net_cash_settlement", math.inf),
    ],
)
def test_settlement_rejects_invalid_monetary_values(
    field_name: str,
    invalid_value: float,
) -> None:
    values = {
        "gross_contractual_recovery": 100.0,
        "reinstatement_premium_payable": 10.0,
        "net_cash_settlement": 100.0,
        "settlement_mode": SettlementMode.PAID_SEPARATELY,
    }
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        SettlementBreakdown(**values)