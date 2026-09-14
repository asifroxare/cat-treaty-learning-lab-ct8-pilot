"""CT1 functional-share and payable-capacity regression tests."""

import math

import pytest

from cat_treaty.models import (
    CapacityBasis,
    CapacityUtilizationStatus,
    TreatyShares,
)
from cat_treaty.shares import (
    apply_contractual_shares,
    calculate_share_factor,
    scale_payable_capacity,
)


@pytest.mark.parametrize(
    ("ceded_share", "placement_share", "expected_factor"),
    [
        (1.0, 1.0, 1.0),
        (0.9, 1.0, 0.9),
        (1.0, 0.75, 0.75),
        (0.9, 0.75, 0.675),
        (0.0, 1.0, 0.0),
        (1.0, 0.0, 0.0),
    ],
)
def test_f02_six_functional_share_cases(
    ceded_share: float,
    placement_share: float,
    expected_factor: float,
) -> None:
    shares = TreatyShares(ceded_share, placement_share)

    assert calculate_share_factor(shares) == pytest.approx(expected_factor)
    assert apply_contractual_shares(1_000_000.0, shares) == pytest.approx(
        1_000_000.0 * expected_factor
    )


def test_default_shares_preserve_covered_loss_exactly() -> None:
    covered_loss = 1_234_567.8901234567

    assert apply_contractual_shares(covered_loss, TreatyShares()) == covered_loss


@pytest.mark.parametrize(
    "invalid_loss",
    [-1.0, math.nan, math.inf, -math.inf, True, "100"],
)
def test_contractual_shares_reject_invalid_covered_loss(
    invalid_loss: object,
) -> None:
    with pytest.raises(ValueError):
        apply_contractual_shares(invalid_loss, TreatyShares())


def test_share_functions_require_treaty_shares() -> None:
    with pytest.raises(TypeError, match="shares must be a TreatyShares"):
        calculate_share_factor(object())

    with pytest.raises(TypeError, match="shares must be a TreatyShares"):
        apply_contractual_shares(100.0, object())


def test_positive_share_scales_every_capacity_amount() -> None:
    shares = TreatyShares(0.9, 0.75)

    state = scale_payable_capacity(
        initial_capacity_100_percent=1_000_000.0,
        available_before_100_percent=800_000.0,
        consumed_100_percent=300_000.0,
        reinstated_100_percent=100_000.0,
        remaining_100_percent=600_000.0,
        capacity_utilization_100_percent=0.4,
        shares=shares,
    )

    assert state.capacity_basis is CapacityBasis.PAYABLE_PLACED_SHARE
    assert state.initial_capacity == pytest.approx(675_000.0)
    assert state.available_before == pytest.approx(540_000.0)
    assert state.consumed == pytest.approx(202_500.0)
    assert state.reinstated == pytest.approx(67_500.0)
    assert state.remaining == pytest.approx(405_000.0)
    assert state.capacity_utilization == 0.4
    assert (
        state.capacity_utilization_status
        is CapacityUtilizationStatus.APPLICABLE
    )


@pytest.mark.parametrize(
    "shares",
    [TreatyShares(0.0, 1.0), TreatyShares(1.0, 0.0)],
)
def test_g14_g15_zero_share_returns_explicit_zero_capacity(
    shares: TreatyShares,
) -> None:
    state = scale_payable_capacity(
        initial_capacity_100_percent=1_000_000.0,
        available_before_100_percent=750_000.0,
        consumed_100_percent=250_000.0,
        reinstated_100_percent=0.0,
        remaining_100_percent=500_000.0,
        capacity_utilization_100_percent=0.5,
        shares=shares,
    )

    assert state.initial_capacity == 0.0
    assert state.available_before == 0.0
    assert state.consumed == 0.0
    assert state.reinstated == 0.0
    assert state.remaining == 0.0
    assert state.capacity_utilization is None
    assert (
        state.capacity_utilization_status
        is CapacityUtilizationStatus.NOT_APPLICABLE_ZERO_CAPACITY
    )


def test_g13_two_event_proportional_equivalence() -> None:
    shares = TreatyShares(0.9, 0.75)
    factor = 0.675

    event_one = scale_payable_capacity(
        initial_capacity_100_percent=1_000_000.0,
        available_before_100_percent=1_000_000.0,
        consumed_100_percent=1_000_000.0,
        reinstated_100_percent=1_000_000.0,
        remaining_100_percent=1_000_000.0,
        capacity_utilization_100_percent=0.5,
        shares=shares,
    )
    event_two = scale_payable_capacity(
        initial_capacity_100_percent=1_000_000.0,
        available_before_100_percent=1_000_000.0,
        consumed_100_percent=500_000.0,
        reinstated_100_percent=0.0,
        remaining_100_percent=500_000.0,
        capacity_utilization_100_percent=0.75,
        shares=shares,
    )

    assert event_one.initial_capacity == pytest.approx(1_000_000.0 * factor)
    assert event_one.consumed == pytest.approx(1_000_000.0 * factor)
    assert event_one.reinstated == pytest.approx(1_000_000.0 * factor)
    assert event_one.remaining == pytest.approx(1_000_000.0 * factor)
    assert event_one.capacity_utilization == 0.5

    assert event_two.available_before == pytest.approx(1_000_000.0 * factor)
    assert event_two.consumed == pytest.approx(500_000.0 * factor)
    assert event_two.remaining == pytest.approx(500_000.0 * factor)
    assert event_two.capacity_utilization == 0.75

    total_payable_consumed = event_one.consumed + event_two.consumed
    assert total_payable_consumed == pytest.approx(1_500_000.0 * factor)


@pytest.mark.parametrize(
    "field_name",
    [
        "initial_capacity_100_percent",
        "available_before_100_percent",
        "consumed_100_percent",
        "reinstated_100_percent",
        "remaining_100_percent",
    ],
)
@pytest.mark.parametrize("invalid_value", [-1.0, math.nan, math.inf, True])
def test_capacity_scaling_rejects_invalid_monetary_inputs(
    field_name: str,
    invalid_value: object,
) -> None:
    values: dict[str, object] = {
        "initial_capacity_100_percent": 1_000_000.0,
        "available_before_100_percent": 1_000_000.0,
        "consumed_100_percent": 250_000.0,
        "reinstated_100_percent": 0.0,
        "remaining_100_percent": 750_000.0,
        "capacity_utilization_100_percent": 0.25,
        "shares": TreatyShares(),
    }
    values[field_name] = invalid_value

    with pytest.raises(ValueError):
        scale_payable_capacity(**values)


@pytest.mark.parametrize(
    "invalid_utilization",
    [None, -0.01, 1.01, math.nan, math.inf, True],
)
def test_positive_capacity_rejects_invalid_source_utilization(
    invalid_utilization: object,
) -> None:
    with pytest.raises(ValueError):
        scale_payable_capacity(
            initial_capacity_100_percent=1_000_000.0,
            available_before_100_percent=1_000_000.0,
            consumed_100_percent=250_000.0,
            reinstated_100_percent=0.0,
            remaining_100_percent=750_000.0,
            capacity_utilization_100_percent=invalid_utilization,
            shares=TreatyShares(),
        )


def test_capacity_scaling_requires_treaty_shares() -> None:
    with pytest.raises(TypeError, match="shares must be a TreatyShares"):
        scale_payable_capacity(
            initial_capacity_100_percent=1_000_000.0,
            available_before_100_percent=1_000_000.0,
            consumed_100_percent=250_000.0,
            reinstated_100_percent=0.0,
            remaining_100_percent=750_000.0,
            capacity_utilization_100_percent=0.25,
            shares=object(),
        )
