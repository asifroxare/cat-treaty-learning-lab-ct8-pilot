"""CT1 functional shares and payable-placed capacity scaling."""

import math
from numbers import Real

from cat_treaty.models import (
    CapacityState,
    CapacityUtilizationStatus,
    TreatyShares,
)


def _require_shares(shares: object) -> TreatyShares:
    if not isinstance(shares, TreatyShares):
        raise TypeError("shares must be a TreatyShares")
    return shares


def _require_non_negative_finite(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")

    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def _require_utilization(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(
            "capacity_utilization_100_percent must be a real number"
        )

    result = float(value)
    if not math.isfinite(result):
        raise ValueError(
            "capacity_utilization_100_percent must be finite"
        )
    if not 0 <= result <= 1:
        raise ValueError(
            "capacity_utilization_100_percent must lie in [0, 1]"
        )
    return result


def calculate_share_factor(shares: TreatyShares) -> float:
    """Return the functional ceded-and-placed share factor."""

    validated_shares = _require_shares(shares)
    return (
        validated_shares.ceded_share
        * validated_shares.placement_share
    )


def apply_contractual_shares(
    covered_loss: float,
    shares: TreatyShares,
) -> float:
    """Apply F02 to authoritative covered loss without layer recalculation."""

    validated_loss = _require_non_negative_finite(
        "covered_loss",
        covered_loss,
    )
    factor = calculate_share_factor(shares)

    if factor == 1.0:
        return validated_loss
    if factor == 0.0:
        return 0.0
    return validated_loss * factor


def scale_payable_capacity(
    *,
    initial_capacity_100_percent: float,
    available_before_100_percent: float,
    consumed_100_percent: float,
    reinstated_100_percent: float,
    remaining_100_percent: float,
    capacity_utilization_100_percent: float,
    shares: TreatyShares,
) -> CapacityState:
    """Scale an authoritative 100% capacity state to payable placed share.

    The function does not recreate occurrence or reinstatement mechanics. It
    applies one constant annual-trial share factor to the validated source
    ledger and preserves its utilization fraction when payable capacity exists.
    """

    factor = calculate_share_factor(shares)
    initial = _require_non_negative_finite(
        "initial_capacity_100_percent",
        initial_capacity_100_percent,
    )
    available_before = _require_non_negative_finite(
        "available_before_100_percent",
        available_before_100_percent,
    )
    consumed = _require_non_negative_finite(
        "consumed_100_percent",
        consumed_100_percent,
    )
    reinstated = _require_non_negative_finite(
        "reinstated_100_percent",
        reinstated_100_percent,
    )
    remaining = _require_non_negative_finite(
        "remaining_100_percent",
        remaining_100_percent,
    )
    utilization = _require_utilization(
        capacity_utilization_100_percent
    )

    if factor == 0.0:
        return CapacityState(
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

    return CapacityState(
        initial_capacity=initial * factor,
        available_before=available_before * factor,
        consumed=consumed * factor,
        reinstated=reinstated * factor,
        remaining=remaining * factor,
        capacity_utilization=utilization,
        capacity_utilization_status=CapacityUtilizationStatus.APPLICABLE,
    )
