"""F03/F04 Ultimate Net Loss engine tests."""

from dataclasses import FrozenInstanceError
import math

import pytest

from cat_treaty.ct2_models import (
    LossBasisInput,
    LossComponent,
    LossComponentCategory,
)
from cat_treaty.loss_basis import (
    build_loss_basis,
    verify_loss_basis_reconciliation,
)


def component(
    component_id: str,
    category: LossComponentCategory,
    amount: float,
    *,
    included: bool = True,
) -> LossComponent:
    return LossComponent(
        component_id=component_id,
        category=category,
        label=component_id.replace("_", " ").title(),
        amount=amount,
        included=included,
        source_reference=f"scenario:{component_id}",
        rule_reference="F03",
    )


def basis_input(
    *,
    initial_insured_loss: float = 1_000.0,
    components: tuple[LossComponent, ...] = (),
) -> LossBasisInput:
    return LossBasisInput(
        occurrence_id="OCC-001",
        reporting_currency="USD",
        source_stage_declaration="insured_loss_after_policy_terms",
        source_reference="catalogue:EVT-001",
        initial_insured_loss=initial_insured_loss,
        ground_up_loss=1_200.0,
        components=components,
    )


def test_f03_no_components_preserves_initial_insured_loss() -> None:
    source = basis_input()

    result = build_loss_basis(source)

    assert result.basis_input is source
    assert result.included_additions == 0.0
    assert result.applied_deductions == 0.0
    assert result.ultimate_net_loss_before_inuring == 1_000.0
    assert result.reconciliation_passed is True
    assert verify_loss_basis_reconciliation(result) is True


def test_g17_all_f03_categories_reconcile() -> None:
    source = basis_input(
        components=(
            component(
                "lae",
                LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
                100.0,
            ),
            component(
                "included_cost",
                LossComponentCategory.OTHER_INCLUDED_COST,
                25.0,
            ),
            component("salvage", LossComponentCategory.SALVAGE, 40.0),
            component(
                "subrogation",
                LossComponentCategory.SUBROGATION,
                30.0,
            ),
            component(
                "other_recovery",
                LossComponentCategory.OTHER_NON_INURING_RECOVERY,
                20.0,
            ),
            component(
                "exclusion",
                LossComponentCategory.CONTRACT_EXCLUSION,
                10.0,
            ),
        )
    )

    result = build_loss_basis(source)

    assert result.included_additions == 125.0
    assert result.applied_deductions == 100.0
    assert result.ultimate_net_loss_before_inuring == 1_025.0
    assert verify_loss_basis_reconciliation(result) is True


def test_excluded_components_remain_visible_with_zero_effect() -> None:
    excluded_addition = component(
        "excluded_lae",
        LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
        500.0,
        included=False,
    )
    excluded_deduction = component(
        "excluded_salvage",
        LossComponentCategory.SALVAGE,
        300.0,
        included=False,
    )
    source = basis_input(components=(excluded_addition, excluded_deduction))

    result = build_loss_basis(source)

    assert result.basis_input.components == (
        excluded_addition,
        excluded_deduction,
    )
    assert result.included_additions == 0.0
    assert result.applied_deductions == 0.0
    assert result.ultimate_net_loss_before_inuring == 1_000.0


@pytest.mark.parametrize(
    "category",
    [
        LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
        LossComponentCategory.OTHER_INCLUDED_COST,
    ],
)
def test_each_addition_category_increases_unl(
    category: LossComponentCategory,
) -> None:
    result = build_loss_basis(
        basis_input(components=(component("addition", category, 100.0),))
    )

    assert result.included_additions == 100.0
    assert result.ultimate_net_loss_before_inuring == 1_100.0


@pytest.mark.parametrize(
    "category",
    [
        LossComponentCategory.SALVAGE,
        LossComponentCategory.SUBROGATION,
        LossComponentCategory.OTHER_NON_INURING_RECOVERY,
        LossComponentCategory.CONTRACT_EXCLUSION,
    ],
)
def test_each_deduction_category_reduces_unl(
    category: LossComponentCategory,
) -> None:
    result = build_loss_basis(
        basis_input(components=(component("deduction", category, 100.0),))
    )

    assert result.applied_deductions == 100.0
    assert result.ultimate_net_loss_before_inuring == 900.0


def test_deductions_equal_to_loss_and_additions_allow_zero_unl() -> None:
    result = build_loss_basis(
        basis_input(
            components=(
                component(
                    "exclusion",
                    LossComponentCategory.CONTRACT_EXCLUSION,
                    1_000.0,
                ),
            )
        )
    )

    assert result.ultimate_net_loss_before_inuring == 0.0
    assert verify_loss_basis_reconciliation(result) is True


def test_g25_deductions_above_available_loss_are_rejected() -> None:
    source = basis_input(
        components=(
            component(
                "exclusion",
                LossComponentCategory.CONTRACT_EXCLUSION,
                1_000.01,
            ),
        )
    )

    with pytest.raises(ValueError, match="deductions exceed"):
        build_loss_basis(source)


def test_derived_overflow_is_rejected_explicitly() -> None:
    source = basis_input(
        initial_insured_loss=1e308,
        components=(
            component(
                "large_lae",
                LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
                1e308,
            ),
        ),
    )

    with pytest.raises(ValueError, match="finite"):
        build_loss_basis(source)


def test_boolean_or_unvalidated_input_is_rejected() -> None:
    for invalid in (None, True, 1.0, object()):
        with pytest.raises(TypeError, match="LossBasisInput"):
            build_loss_basis(invalid)  # type: ignore[arg-type]


def test_result_and_source_are_not_mutated() -> None:
    source = basis_input(
        components=(
            component(
                "lae",
                LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
                100.0,
            ),
        )
    )

    result = build_loss_basis(source)

    assert source.initial_insured_loss == 1_000.0
    with pytest.raises(FrozenInstanceError):
        result.ultimate_net_loss_before_inuring = 0.0  # type: ignore[misc]


def test_component_order_does_not_change_f03_result() -> None:
    components = (
        component(
            "lae",
            LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
            0.1,
        ),
        component("salvage", LossComponentCategory.SALVAGE, 0.2),
        component(
            "cost",
            LossComponentCategory.OTHER_INCLUDED_COST,
            0.3,
        ),
    )

    forward = build_loss_basis(basis_input(components=components))
    reverse = build_loss_basis(basis_input(components=tuple(reversed(components))))

    assert forward.included_additions == reverse.included_additions
    assert forward.applied_deductions == reverse.applied_deductions
    assert (
        forward.ultimate_net_loss_before_inuring
        == reverse.ultimate_net_loss_before_inuring
    )


def test_independent_reconciliation_requires_result_type() -> None:
    with pytest.raises(TypeError, match="LossBasisResult"):
        verify_loss_basis_reconciliation(object())  # type: ignore[arg-type]
