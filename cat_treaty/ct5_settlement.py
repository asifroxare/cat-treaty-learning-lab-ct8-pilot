"""CT5 F31 three-way settlement presentation."""

import math
from numbers import Real

from cat_treaty.ct5_models import CT5Settlement
from cat_treaty.models import SettlementMode


def _non_negative_finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def calculate_ct5_settlement(
    *,
    gross_contractual_recovery: float,
    reinstatement_premium_payable: float,
    settlement_mode: SettlementMode = SettlementMode.PAID_SEPARATELY,
) -> CT5Settlement:
    """Present authoritative recovery and premium under the selected F31 mode.

    This function is deliberately calculation-neutral: it does not determine
    recovery, premium, capacity, or tranche usage.
    """

    gross = _non_negative_finite(
        "gross_contractual_recovery", gross_contractual_recovery
    )
    premium = _non_negative_finite(
        "reinstatement_premium_payable", reinstatement_premium_payable
    )
    if not isinstance(settlement_mode, SettlementMode):
        raise ValueError("settlement_mode must be a supported SettlementMode")
    net_cash = (
        gross
        if settlement_mode is SettlementMode.PAID_SEPARATELY
        else gross - premium
    )
    return CT5Settlement(
        gross_contractual_recovery=gross,
        reinstatement_premium_payable=premium,
        net_cash_settlement=net_cash,
        settlement_mode=settlement_mode,
    )

