"""CT1 reinstatement-premium settlement presentation."""

import math
from numbers import Real

from cat_treaty.models import SettlementBreakdown, SettlementMode


def _require_non_negative_finite(field_name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field_name} must be a real number")

    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return result


def calculate_settlement(
    *,
    gross_contractual_recovery: float,
    reinstatement_premium_payable: float,
    settlement_mode: SettlementMode = SettlementMode.PAID_SEPARATELY,
) -> SettlementBreakdown:
    """Return the required three-way settlement presentation.

    This function does not calculate contractual recovery, reinstatement
    premium, or capacity. It only presents already-authoritative values under
    the selected settlement convention.
    """

    gross_recovery = _require_non_negative_finite(
        "gross_contractual_recovery",
        gross_contractual_recovery,
    )
    premium_payable = _require_non_negative_finite(
        "reinstatement_premium_payable",
        reinstatement_premium_payable,
    )

    if not isinstance(settlement_mode, SettlementMode):
        raise ValueError(
            "settlement_mode must be a supported SettlementMode"
        )

    if settlement_mode is SettlementMode.PAID_SEPARATELY:
        net_cash_settlement = gross_recovery
    else:
        net_cash_settlement = gross_recovery - premium_payable

    return SettlementBreakdown(
        gross_contractual_recovery=gross_recovery,
        reinstatement_premium_payable=premium_payable,
        net_cash_settlement=net_cash_settlement,
        settlement_mode=settlement_mode,
    )
