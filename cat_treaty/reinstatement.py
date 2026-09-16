"""CT5 F30 reinstatement-premium calculation."""

import math
from numbers import Real

from cat_treaty.ct5_models import (
    CT5CapacityTransition,
    CT5LayerTerms,
    ReinstatementPremiumResult,
    ReinstatementTimeBasis,
    TrancheAllocation,
)


def _finite(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def calculate_reinstatement_time_factor(
    *,
    event_time: float,
    treaty_term_start: float,
    treaty_term_end: float,
    time_basis: ReinstatementTimeBasis,
) -> float:
    """Return the declared F30 time factor after fail-fast term validation."""

    event = _finite("event_time", event_time)
    start = _finite("treaty_term_start", treaty_term_start)
    end = _finite("treaty_term_end", treaty_term_end)
    if end <= start:
        raise ValueError("treaty_term_end must exceed treaty_term_start")
    if not start <= event < end:
        raise ValueError("event_time must lie in the inclusive-start/exclusive-end treaty term")
    if not isinstance(time_basis, ReinstatementTimeBasis):
        raise ValueError("time_basis must be a supported ReinstatementTimeBasis")
    if time_basis is ReinstatementTimeBasis.FULL_TIME:
        return 1.0
    return (end - event) / (end - start)


def calculate_reinstatement_premium(
    *,
    transition: CT5CapacityTransition,
    terms: CT5LayerTerms,
    event_time: float,
) -> ReinstatementPremiumResult:
    """Price each F29 usage under its own tranche terms and apply F30."""

    if not isinstance(transition, CT5CapacityTransition):
        raise ValueError("transition must be CT5CapacityTransition")
    if not isinstance(terms, CT5LayerTerms):
        raise ValueError("terms must be CT5LayerTerms")
    if transition.state_before.layer_id != terms.layer_id:
        raise ValueError("capacity transition layer_id must match CT5 layer terms")

    event = _finite("event_time", event_time)
    # Validate the event once even when no reinstatement is used.
    calculate_reinstatement_time_factor(
        event_time=event,
        treaty_term_start=terms.treaty_term_start,
        treaty_term_end=terms.treaty_term_end,
        time_basis=ReinstatementTimeBasis.FULL_TIME,
    )
    term_by_sequence = {
        item.sequence: item for item in terms.reinstatement_tranches
    }
    priced: list[TrancheAllocation] = []
    initial_capacity = transition.state_before.initial_capacity
    for usage in transition.tranche_usages:
        tranche = term_by_sequence.get(usage.tranche_sequence)
        if tranche is None:
            raise ValueError("F29 usage references an undeclared tranche")
        if initial_capacity <= 0:
            raise ValueError("positive tranche usage requires positive initial capacity")
        time_factor = calculate_reinstatement_time_factor(
            event_time=event,
            treaty_term_start=terms.treaty_term_start,
            treaty_term_end=terms.treaty_term_end,
            time_basis=tranche.time_basis,
        )
        premium = (
            float(terms.original_layer_premium)
            * float(tranche.premium_rate)
            * (float(usage.amount_used) / float(initial_capacity))
            * time_factor
        )
        priced.append(
            TrancheAllocation(
                tranche_sequence=usage.tranche_sequence,
                capacity_before=usage.capacity_before,
                amount_used=usage.amount_used,
                capacity_after=usage.capacity_after,
                premium_rate=tranche.premium_rate,
                time_basis=tranche.time_basis,
                time_factor=time_factor,
                reinstatement_premium_payable=premium,
                rule_reference=tranche.rule_reference,
            )
        )

    allocations = tuple(priced)
    total = math.fsum(item.reinstatement_premium_payable for item in allocations)
    return ReinstatementPremiumResult(
        layer_id=terms.layer_id,
        event_time=event,
        original_layer_premium=terms.original_layer_premium,
        initial_capacity=initial_capacity,
        tranche_allocations=allocations,
        reinstatement_premium_payable=total,
    )

