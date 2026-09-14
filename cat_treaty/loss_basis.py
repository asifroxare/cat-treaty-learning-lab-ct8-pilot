"""CT2 Ultimate Net Loss construction and F03/F04 reconciliation."""

import math

from cat_treaty.ct2_models import (
    LossBasisInput,
    LossBasisResult,
    LossComponentCategory,
)


_ADDITION_CATEGORIES = frozenset(
    {
        LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
        LossComponentCategory.OTHER_INCLUDED_COST,
    }
)


def _finite_sum(field_name: str, values: list[float]) -> float:
    """Sum validated components and reject a non-finite derived amount."""

    try:
        result = math.fsum(values)
    except OverflowError as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def build_loss_basis(basis_input: LossBasisInput) -> LossBasisResult:
    """Apply F03 and return a constructor-verified F04 result.

    Component direction is determined only by its frozen category. Excluded
    components remain in ``basis_input`` but contribute zero applied effect.
    """

    if not isinstance(basis_input, LossBasisInput):
        raise TypeError("basis_input must be a LossBasisInput")

    included_additions = _finite_sum(
        "included_additions",
        [
            component.applied_amount
            for component in basis_input.components
            if component.category in _ADDITION_CATEGORIES
        ],
    )
    applied_deductions = _finite_sum(
        "applied_deductions",
        [
            component.applied_amount
            for component in basis_input.components
            if component.category not in _ADDITION_CATEGORIES
        ],
    )
    ultimate_net_loss_before_inuring = _finite_sum(
        "ultimate_net_loss_before_inuring",
        [
            float(basis_input.initial_insured_loss),
            included_additions,
            -applied_deductions,
        ],
    )
    if ultimate_net_loss_before_inuring < 0:
        raise ValueError(
            "applied deductions exceed insured loss and included additions"
        )

    return LossBasisResult(
        basis_input=basis_input,
        included_additions=included_additions,
        applied_deductions=applied_deductions,
        ultimate_net_loss_before_inuring=(
            ultimate_net_loss_before_inuring
        ),
        reconciliation_passed=True,
    )


def verify_loss_basis_reconciliation(result: LossBasisResult) -> bool:
    """Independently recompute F04 from the immutable result record."""

    if not isinstance(result, LossBasisResult):
        raise TypeError("result must be a LossBasisResult")

    left_value = _finite_sum(
        "F04 left side",
        [
            float(result.basis_input.initial_insured_loss),
            float(result.included_additions),
        ],
    )
    right_value = _finite_sum(
        "F04 right side",
        [
            float(result.ultimate_net_loss_before_inuring),
            float(result.applied_deductions),
        ],
    )
    return math.isclose(
        left_value,
        right_value,
        rel_tol=1e-12,
        abs_tol=1e-6,
    )
