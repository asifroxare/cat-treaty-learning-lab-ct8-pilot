"""CT5 F25--F29 annual-capacity engine tests."""

from dataclasses import replace
import math

import pytest

from cat_treaty.annual_capacity import (
    allocate_reinstatement_tranches,
    apply_annual_capacity,
    calculate_capacity_limits,
    initialize_annual_capacity,
)
from cat_treaty.ct3_models import CatLayerInput
from cat_treaty.ct5_models import (
    CT5CapacityTransition,
    ReinstatementChargeType,
    ReinstatementTimeBasis,
    ReinstatementTranche,
)
from tests.test_ct5_models import layer_terms, tranche


def layer(**changes: object) -> CatLayerInput:
    values: dict[str, object] = {
        "layer_id": "L1",
        "attachment": 10.0,
        "occurrence_limit": 20.0,
        "ceded_share": 1.0,
        "placement_share": 1.0,
        "currency": "USD",
        "description": "20 xs 10",
        "source_reference": "contract:L1",
        "rule_reference": "CT3-F11",
    }
    values.update(changes)
    return CatLayerInput(**values)


def tranches(count: int) -> tuple[ReinstatementTranche, ...]:
    return tuple(
        tranche(
            sequence=index,
            premium_rate=0.0 if index == 1 else 1.0,
            charge_type=(
                ReinstatementChargeType.FREE
                if index == 1
                else ReinstatementChargeType.PAID
            ),
            time_basis=(
                ReinstatementTimeBasis.FULL_TIME
                if index == 1
                else ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM
            ),
        )
        for index in range(1, count + 1)
    )


def test_f25_capacity_uses_payable_placed_share_once() -> None:
    selected_layer = layer(ceded_share=0.9, placement_share=0.75)
    terms = layer_terms(reinstatement_tranches=tranches(2))
    initial, reserve, maximum = calculate_capacity_limits(selected_layer, terms)
    assert initial == pytest.approx(13.5)
    assert reserve == pytest.approx(27.0)
    assert maximum == pytest.approx(40.5)


def test_annual_reset_initializes_independent_state() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    first = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    second = initialize_annual_capacity(layer(), terms, annual_trial_id=2)
    assert first.active_capacity == second.active_capacity == 20.0
    assert first.remaining_reinstatement_reserve == second.remaining_reinstatement_reserve == 20.0
    assert first.annual_trial_id == 1
    assert second.annual_trial_id == 2


def test_g47_no_reinstatement_recovery_stops_at_initial_capacity() -> None:
    terms = layer_terms(reinstatement_tranches=())
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    first = apply_annual_capacity(
        state=state,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=20.0,
    )
    second = apply_annual_capacity(
        state=first.state_after,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=20.0,
    )
    assert first.gross_contractual_recovery == 20.0
    assert first.amount_reinstated == 0.0
    assert second.gross_contractual_recovery == 0.0
    assert second.capacity_constrained_recovery_shortfall == 20.0


def test_g48_one_full_reinstatement_benefits_only_later_event() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    first = apply_annual_capacity(
        state=state,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=35.0,
    )
    assert first.gross_contractual_recovery == 20.0
    assert first.capacity_constrained_recovery_shortfall == 15.0
    assert first.active_capacity_after_recovery == 0.0
    assert first.amount_reinstated == 20.0
    assert first.state_after.active_capacity == 20.0
    second = apply_annual_capacity(
        state=first.state_after,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=20.0,
    )
    assert second.gross_contractual_recovery == 20.0
    assert second.amount_reinstated == 0.0


def test_g49_third_full_event_receives_zero_with_one_reinstatement() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    transitions = []
    for _ in range(3):
        transition = apply_annual_capacity(
            state=state,
            layer=layer(),
            terms=terms,
            pre_annual_capacity_recovery=20.0,
        )
        transitions.append(transition)
        state = transition.state_after
    assert [item.gross_contractual_recovery for item in transitions] == [20.0, 20.0, 0.0]
    assert state.cumulative_recovery == 40.0
    assert state.cumulative_reinstated == 20.0


def test_partial_recovery_restores_only_amount_consumed() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    transition = apply_annual_capacity(
        state=state,
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=7.5,
    )
    assert transition.gross_contractual_recovery == 7.5
    assert transition.active_capacity_after_recovery == 12.5
    assert transition.amount_reinstated == 7.5
    assert transition.state_after.active_capacity == 20.0
    assert transition.tranche_usages[0].amount_used == 7.5


def test_f29_single_event_crosses_two_tranches_in_sequence() -> None:
    usages = allocate_reinstatement_tranches(
        initial_capacity=20.0,
        tranche_count=2,
        cumulative_used_before=15.0,
        amount_to_reinstate=10.0,
    )
    assert tuple(item.tranche_sequence for item in usages) == (1, 2)
    assert tuple(item.amount_used for item in usages) == (5.0, 5.0)
    assert usages[0].capacity_after == 0.0
    assert usages[1].capacity_after == 15.0


def test_transition_crosses_tranches_after_prior_partial_usage() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(2))
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
    assert tuple(item.tranche_sequence for item in current.tranche_usages) == (1, 2)
    assert tuple(item.amount_used for item in current.tranche_usages) == (5.0, 5.0)


def test_f29_never_uses_later_tranche_while_earlier_has_capacity() -> None:
    usages = allocate_reinstatement_tranches(
        initial_capacity=20.0,
        tranche_count=3,
        cumulative_used_before=4.0,
        amount_to_reinstate=8.0,
    )
    assert len(usages) == 1
    assert usages[0].tranche_sequence == 1
    assert usages[0].capacity_before == 16.0
    assert usages[0].capacity_after == 8.0


def test_restoration_after_last_observed_event_is_still_recorded() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    transition = apply_annual_capacity(
        state=initialize_annual_capacity(layer(), terms, annual_trial_id=1),
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=8.0,
    )
    assert transition.amount_reinstated == 8.0
    assert transition.state_after.remaining_reinstatement_reserve == 12.0


def test_zero_share_has_zero_capacity_without_division() -> None:
    selected_layer = layer(ceded_share=0.0)
    terms = layer_terms(reinstatement_tranches=tranches(2))
    state = initialize_annual_capacity(selected_layer, terms, annual_trial_id=1)
    transition = apply_annual_capacity(
        state=state,
        layer=selected_layer,
        terms=terms,
        pre_annual_capacity_recovery=0.0,
    )
    assert state.initial_capacity == 0.0
    assert transition.gross_contractual_recovery == 0.0
    assert transition.tranche_usages == ()


@pytest.mark.parametrize("value", [-1.0, math.inf, math.nan, True, "20"])
def test_apply_rejects_invalid_pre_capacity_recovery(value: object) -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    with pytest.raises(ValueError):
        apply_annual_capacity(
            state=initialize_annual_capacity(layer(), terms, annual_trial_id=1),
            layer=layer(),
            terms=terms,
            pre_annual_capacity_recovery=value,  # type: ignore[arg-type]
        )


def test_layer_terms_and_state_must_match_frozen_layer() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    with pytest.raises(ValueError, match="layer_id"):
        calculate_capacity_limits(layer(), replace(terms, layer_id="OTHER"))
    state = initialize_annual_capacity(layer(), terms, annual_trial_id=1)
    changed_layer = layer(occurrence_limit=25.0)
    with pytest.raises(ValueError, match="frozen layer terms"):
        apply_annual_capacity(
            state=state,
            layer=changed_layer,
            terms=terms,
            pre_annual_capacity_recovery=5.0,
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"initial_capacity": -1.0, "tranche_count": 1, "cumulative_used_before": 0.0, "amount_to_reinstate": 0.0},
        {"initial_capacity": 20.0, "tranche_count": -1, "cumulative_used_before": 0.0, "amount_to_reinstate": 0.0},
        {"initial_capacity": 20.0, "tranche_count": 1, "cumulative_used_before": 21.0, "amount_to_reinstate": 0.0},
        {"initial_capacity": 20.0, "tranche_count": 1, "cumulative_used_before": 15.0, "amount_to_reinstate": 6.0},
    ],
)
def test_f29_rejects_invalid_or_overallocated_requests(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        allocate_reinstatement_tranches(**kwargs)  # type: ignore[arg-type]


def test_capacity_transition_contract_rejects_same_event_overrecovery() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    transition = apply_annual_capacity(
        state=initialize_annual_capacity(layer(), terms, annual_trial_id=1),
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=35.0,
    )
    assert isinstance(transition, CT5CapacityTransition)
    with pytest.raises(ValueError, match="F26"):
        replace(transition, gross_contractual_recovery=35.0, capacity_constrained_recovery_shortfall=0.0)


def test_capacity_transition_rejects_balanced_but_nonautomatic_restoration() -> None:
    terms = layer_terms(reinstatement_tranches=tranches(1))
    transition = apply_annual_capacity(
        state=initialize_annual_capacity(layer(), terms, annual_trial_id=1),
        layer=layer(),
        terms=terms,
        pre_annual_capacity_recovery=10.0,
    )
    bad_after = replace(
        transition.state_after,
        active_capacity=15.0,
        remaining_reinstatement_reserve=15.0,
        cumulative_reinstated=5.0,
    )
    usage = replace(
        transition.tranche_usages[0],
        amount_used=5.0,
        capacity_after=15.0,
    )
    with pytest.raises(ValueError, match="F28"):
        replace(
            transition,
            amount_reinstated=5.0,
            tranche_usages=(usage,),
            state_after=bad_after,
        )


def test_capacity_engine_public_exports() -> None:
    import cat_treaty

    expected = {
        "CT5CapacityTransition",
        "TrancheCapacityUsage",
        "allocate_reinstatement_tranches",
        "apply_annual_capacity",
        "calculate_capacity_limits",
        "initialize_annual_capacity",
    }
    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, name) for name in expected)
