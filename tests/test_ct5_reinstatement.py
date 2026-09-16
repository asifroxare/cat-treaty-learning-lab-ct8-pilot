"""CT5 F30 reinstatement-premium tests."""

from dataclasses import replace
import math

import pytest

from cat_treaty.annual_capacity import apply_annual_capacity, initialize_annual_capacity
from cat_treaty.ct5_models import (
    ReinstatementChargeType,
    ReinstatementPremiumResult,
    ReinstatementTimeBasis,
)
from cat_treaty.reinstatement import (
    calculate_reinstatement_premium,
    calculate_reinstatement_time_factor,
)
from tests.test_ct5_capacity import layer
from tests.test_ct5_models import layer_terms, tranche


def transition_for(
    recovery: float,
    *,
    terms=None,
    selected_layer=None,
):
    selected_terms = terms or layer_terms()
    selected = selected_layer or layer()
    state = initialize_annual_capacity(selected, selected_terms, annual_trial_id=1)
    return apply_annual_capacity(
        state=state,
        layer=selected,
        terms=selected_terms,
        pre_annual_capacity_recovery=recovery,
    )


def test_full_time_paid_reinstatement_is_pro_rata_as_to_amount() -> None:
    terms = layer_terms()
    result = calculate_reinstatement_premium(
        transition=transition_for(10.0, terms=terms),
        terms=terms,
        event_time=1_000.0,
    )
    assert result.reinstatement_premium_payable == pytest.approx(1_000_000.0)
    assert result.tranche_allocations[0].amount_used == 10.0
    assert result.tranche_allocations[0].time_factor == 1.0


def test_free_reinstatement_restores_capacity_with_zero_premium() -> None:
    free = tranche(
        premium_rate=0.0,
        charge_type=ReinstatementChargeType.FREE,
    )
    terms = layer_terms(reinstatement_tranches=(free,))
    transition = transition_for(20.0, terms=terms)
    result = calculate_reinstatement_premium(
        transition=transition,
        terms=terms,
        event_time=2_000.0,
    )
    assert transition.amount_reinstated == 20.0
    assert result.reinstatement_premium_payable == 0.0
    assert result.tranche_allocations[0].premium_rate == 0.0


def test_pro_rata_remaining_term_uses_exact_fraction() -> None:
    timed = tranche(time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM)
    terms = layer_terms(reinstatement_tranches=(timed,))
    result = calculate_reinstatement_premium(
        transition=transition_for(8.0, terms=terms),
        terms=terms,
        event_time=6_570.0,
    )
    assert result.tranche_allocations[0].time_factor == 0.25
    assert result.reinstatement_premium_payable == pytest.approx(200_000.0)


def test_g63_one_event_crossing_two_tranches_uses_each_own_terms() -> None:
    first = tranche(sequence=1, premium_rate=0.5)
    second = tranche(
        sequence=2,
        premium_rate=1.0,
        time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM,
    )
    terms = layer_terms(reinstatement_tranches=(first, second))
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    prior = apply_annual_capacity(
        state=state,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=15.0,
    )
    current = apply_annual_capacity(
        state=prior.state_after,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=10.0,
    )
    result = calculate_reinstatement_premium(
        transition=current,
        terms=terms,
        event_time=6_570.0,
    )
    assert tuple(item.amount_used for item in result.tranche_allocations) == (5.0, 5.0)
    assert tuple(item.time_factor for item in result.tranche_allocations) == (1.0, 0.25)
    assert tuple(item.reinstatement_premium_payable for item in result.tranche_allocations) == pytest.approx((250_000.0, 125_000.0))
    assert result.reinstatement_premium_payable == pytest.approx(375_000.0)


def test_g66_amount_and_time_proration_are_multiplicative() -> None:
    timed = tranche(time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM)
    terms = layer_terms(reinstatement_tranches=(timed,))
    result = calculate_reinstatement_premium(
        transition=transition_for(8.0, terms=terms),
        terms=terms,
        event_time=6_570.0,
    )
    expected = 2_000_000.0 * (8.0 / 20.0) * 0.25
    assert result.reinstatement_premium_payable == expected == 200_000.0


def test_paid_rate_above_one_hundred_percent_is_supported() -> None:
    expensive = tranche(premium_rate=3.0)
    terms = layer_terms(
        original_layer_premium=10.0,
        reinstatement_tranches=(expensive,),
    )
    result = calculate_reinstatement_premium(
        transition=transition_for(1.0, terms=terms),
        terms=terms,
        event_time=0.0,
    )
    assert result.reinstatement_premium_payable == 1.5


def test_premium_is_due_after_last_observed_event() -> None:
    terms = layer_terms()
    result = calculate_reinstatement_premium(
        transition=transition_for(20.0, terms=terms),
        terms=terms,
        event_time=8_000.0,
    )
    assert result.reinstatement_premium_payable == 2_000_000.0


def test_no_reinstatement_usage_returns_zero_premium() -> None:
    terms = layer_terms(reinstatement_tranches=())
    result = calculate_reinstatement_premium(
        transition=transition_for(20.0, terms=terms),
        terms=terms,
        event_time=100.0,
    )
    assert result.tranche_allocations == ()
    assert result.reinstatement_premium_payable == 0.0


def test_zero_payable_capacity_returns_zero_without_division() -> None:
    terms = layer_terms()
    selected_layer = layer(placement_share=0.0)
    result = calculate_reinstatement_premium(
        transition=transition_for(0.0, terms=terms, selected_layer=selected_layer),
        terms=terms,
        event_time=100.0,
    )
    assert result.initial_capacity == 0.0
    assert result.tranche_allocations == ()
    assert result.reinstatement_premium_payable == 0.0


@pytest.mark.parametrize(
    "event_time",
    [-1.0, 8_760.0, 9_000.0, math.nan, math.inf, True, "100"],
)
def test_invalid_event_time_is_rejected_before_pricing(event_time: object) -> None:
    terms = layer_terms()
    with pytest.raises(ValueError):
        calculate_reinstatement_premium(
            transition=transition_for(5.0, terms=terms),
            terms=terms,
            event_time=event_time,  # type: ignore[arg-type]
        )


def test_treaty_start_is_inclusive_and_end_is_exclusive() -> None:
    assert calculate_reinstatement_time_factor(
        event_time=0.0,
        treaty_term_start=0.0,
        treaty_term_end=8_760.0,
        time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM,
    ) == 1.0
    with pytest.raises(ValueError, match="inclusive-start/exclusive-end"):
        calculate_reinstatement_time_factor(
            event_time=8_760.0,
            treaty_term_start=0.0,
            treaty_term_end=8_760.0,
            time_basis=ReinstatementTimeBasis.FULL_TIME,
        )


def test_pricing_rejects_layer_mismatch() -> None:
    terms = layer_terms()
    with pytest.raises(ValueError, match="layer_id"):
        calculate_reinstatement_premium(
            transition=transition_for(5.0, terms=terms),
            terms=replace(terms, layer_id="OTHER"),
            event_time=100.0,
        )


def test_result_rejects_total_not_equal_to_allocation_sum() -> None:
    terms = layer_terms()
    result = calculate_reinstatement_premium(
        transition=transition_for(10.0, terms=terms),
        terms=terms,
        event_time=100.0,
    )
    assert isinstance(result, ReinstatementPremiumResult)
    with pytest.raises(ValueError, match="does not reconcile"):
        replace(result, reinstatement_premium_payable=0.0)


def test_f30_does_not_mutate_capacity_transition() -> None:
    terms = layer_terms()
    transition = transition_for(10.0, terms=terms)
    before = transition.state_after
    calculate_reinstatement_premium(
        transition=transition,
        terms=terms,
        event_time=100.0,
    )
    assert transition.state_after == before


def test_reinstatement_pricing_public_exports() -> None:
    import cat_treaty

    expected = {
        "ReinstatementPremiumResult",
        "calculate_reinstatement_premium",
        "calculate_reinstatement_time_factor",
    }
    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, name) for name in expected)
