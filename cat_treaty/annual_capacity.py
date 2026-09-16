"""CT5 F25--F29 annual-capacity and reinstatement state transitions."""

import math

from cat_treaty.ct3_models import CatLayerInput
from cat_treaty.ct5_models import (
    ABSOLUTE_CURRENCY_TOLERANCE,
    CT5CapacityState,
    CT5CapacityTransition,
    CT5LayerTerms,
    RELATIVE_TOLERANCE,
    TrancheCapacityUsage,
)


def _close(left: float, right: float) -> bool:
    return math.isclose(
        left,
        right,
        rel_tol=RELATIVE_TOLERANCE,
        abs_tol=ABSOLUTE_CURRENCY_TOLERANCE,
    )


def _non_negative_finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _validate_layer_terms(layer: CatLayerInput, terms: CT5LayerTerms) -> None:
    if not isinstance(layer, CatLayerInput):
        raise ValueError("layer must be CatLayerInput")
    if not isinstance(terms, CT5LayerTerms):
        raise ValueError("terms must be CT5LayerTerms")
    if layer.layer_id != terms.layer_id:
        raise ValueError("CT3 layer_id must match CT5 layer terms")


def calculate_capacity_limits(
    layer: CatLayerInput,
    terms: CT5LayerTerms,
) -> tuple[float, float, float]:
    """Return F25 initial, reinstatement-reserve, and maximum capacity."""

    _validate_layer_terms(layer, terms)
    share_factor = float(layer.ceded_share) * float(layer.placement_share)
    initial_capacity = float(layer.occurrence_limit) * share_factor
    initial_reserve = initial_capacity * len(terms.reinstatement_tranches)
    maximum_capacity = initial_capacity + initial_reserve
    return initial_capacity, initial_reserve, maximum_capacity


def initialize_annual_capacity(
    layer: CatLayerInput,
    terms: CT5LayerTerms,
    *,
    annual_trial_id: int,
) -> CT5CapacityState:
    """Create the annual reset state required by F25."""

    initial, reserve, _ = calculate_capacity_limits(layer, terms)
    return CT5CapacityState(
        layer_id=layer.layer_id,
        annual_trial_id=annual_trial_id,
        completed_event_count=0,
        initial_capacity=initial,
        active_capacity=initial,
        initial_reinstatement_reserve=reserve,
        remaining_reinstatement_reserve=reserve,
        cumulative_recovery=0.0,
        cumulative_reinstated=0.0,
    )


def allocate_reinstatement_tranches(
    *,
    initial_capacity: float,
    tranche_count: int,
    cumulative_used_before: float,
    amount_to_reinstate: float,
) -> tuple[TrancheCapacityUsage, ...]:
    """Apply F29 to the lowest-numbered non-exhausted tranches."""

    capacity = _non_negative_finite("initial_capacity", initial_capacity)
    used_before = _non_negative_finite(
        "cumulative_used_before", cumulative_used_before
    )
    amount = _non_negative_finite("amount_to_reinstate", amount_to_reinstate)
    if isinstance(tranche_count, bool) or not isinstance(tranche_count, int) or tranche_count < 0:
        raise ValueError("tranche_count must be a non-negative integer")
    total_reserve = capacity * tranche_count
    if used_before > total_reserve and not _close(used_before, total_reserve):
        raise ValueError("cumulative tranche use exceeds purchased reserve")
    remaining_reserve = max(0.0, total_reserve - used_before)
    if amount > remaining_reserve and not _close(amount, remaining_reserve):
        raise ValueError("amount_to_reinstate exceeds remaining reserve")
    if capacity == 0 or amount == 0:
        return ()

    remaining = amount
    usages: list[TrancheCapacityUsage] = []
    for sequence in range(1, tranche_count + 1):
        already_used = min(
            capacity,
            max(0.0, used_before - capacity * (sequence - 1)),
        )
        available = max(0.0, capacity - already_used)
        if available == 0:
            continue
        delta = min(remaining, available)
        if delta > 0:
            usages.append(
                TrancheCapacityUsage(
                    tranche_sequence=sequence,
                    capacity_before=available,
                    amount_used=delta,
                    capacity_after=available - delta,
                )
            )
            remaining -= delta
        if remaining <= ABSOLUTE_CURRENCY_TOLERANCE:
            remaining = 0.0
            break
    if not _close(remaining, 0.0):
        raise ValueError("F29 could not allocate the complete reinstatement amount")
    return tuple(usages)


def apply_annual_capacity(
    *,
    state: CT5CapacityState,
    layer: CatLayerInput,
    terms: CT5LayerTerms,
    pre_annual_capacity_recovery: float,
) -> CT5CapacityTransition:
    """Apply F26--F29 to one ordered occurrence for one layer."""

    if not isinstance(state, CT5CapacityState):
        raise ValueError("state must be CT5CapacityState")
    _validate_layer_terms(layer, terms)
    if state.layer_id != layer.layer_id:
        raise ValueError("capacity state layer_id must match CT3 layer")
    initial, reserve, _ = calculate_capacity_limits(layer, terms)
    if not _close(state.initial_capacity, initial) or not _close(
        state.initial_reinstatement_reserve, reserve
    ):
        raise ValueError("capacity state does not match frozen layer terms")

    entitlement = _non_negative_finite(
        "pre_annual_capacity_recovery", pre_annual_capacity_recovery
    )
    recovery = min(entitlement, state.active_capacity)
    shortfall = entitlement - recovery
    active_after_recovery = state.active_capacity - recovery

    restoration_required = state.initial_capacity - active_after_recovery
    reinstated = min(restoration_required, state.remaining_reinstatement_reserve)
    usages = allocate_reinstatement_tranches(
        initial_capacity=state.initial_capacity,
        tranche_count=len(terms.reinstatement_tranches),
        cumulative_used_before=state.cumulative_reinstated,
        amount_to_reinstate=reinstated,
    )

    state_after = CT5CapacityState(
        layer_id=state.layer_id,
        annual_trial_id=state.annual_trial_id,
        completed_event_count=state.completed_event_count + 1,
        initial_capacity=state.initial_capacity,
        active_capacity=active_after_recovery + reinstated,
        initial_reinstatement_reserve=state.initial_reinstatement_reserve,
        remaining_reinstatement_reserve=(
            state.remaining_reinstatement_reserve - reinstated
        ),
        cumulative_recovery=state.cumulative_recovery + recovery,
        cumulative_reinstated=state.cumulative_reinstated + reinstated,
    )
    return CT5CapacityTransition(
        state_before=state,
        pre_annual_capacity_recovery=entitlement,
        gross_contractual_recovery=recovery,
        capacity_constrained_recovery_shortfall=shortfall,
        active_capacity_after_recovery=active_after_recovery,
        amount_reinstated=reinstated,
        tranche_usages=usages,
        state_after=state_after,
    )
