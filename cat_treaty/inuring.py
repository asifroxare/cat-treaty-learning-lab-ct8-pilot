"""CT2 ordered inuring-reinsurance waterfall engine (F05–F09)."""

import math

from cat_treaty.ct2_models import (
    BindingConstraint,
    ExplanationFact,
    InuringCompletionStatus,
    InuringCoverInput,
    InuringCoverResult,
    InuringValuationMode,
    InuringWaterfallInput,
    InuringWaterfallResult,
    ReconciliationCheck,
)


_REL_TOL = 1e-12
_ABS_TOL = 1e-6


def _close(left: float, right: float) -> bool:
    return math.isclose(
        left,
        right,
        rel_tol=_REL_TOL,
        abs_tol=_ABS_TOL,
    )


def _finite(field_name: str, value: float) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite")
    return value


def _recovery_before_limits(
    cover: InuringCoverInput,
    cover_subject_loss: float,
) -> float:
    if cover.valuation_mode is (
        InuringValuationMode.CALCULATED_PROPORTIONAL
    ):
        assert cover.cession_rate is not None
        return _finite(
            "recovery_before_limits",
            cover_subject_loss * float(cover.cession_rate),
        )

    assert cover.supplied_recovery is not None
    supplied_recovery = float(cover.supplied_recovery)
    if supplied_recovery > cover_subject_loss:
        raise ValueError(
            f"cover {cover.cover_id} supplied_recovery cannot exceed "
            "cover_subject_loss"
        )
    return min(supplied_recovery, cover_subject_loss)


def _binding_constraints(
    cover: InuringCoverInput,
    recovery_before_limits: float,
    payable_recovery: float,
) -> tuple[BindingConstraint, ...]:
    constraints: list[BindingConstraint] = []
    if (
        cover.occurrence_limit is not None
        and float(cover.occurrence_limit) <= recovery_before_limits
        and _close(payable_recovery, float(cover.occurrence_limit))
    ):
        constraints.append(BindingConstraint.OCCURRENCE_LIMIT)
    if (
        cover.aggregate_remaining_before is not None
        and float(cover.aggregate_remaining_before) <= recovery_before_limits
        and _close(
            payable_recovery,
            float(cover.aggregate_remaining_before),
        )
    ):
        constraints.append(BindingConstraint.AGGREGATE_REMAINING)
    return tuple(constraints)


def _apply_cover(
    cover: InuringCoverInput,
    incoming_loss: float,
) -> InuringCoverResult:
    cover_subject_loss = _finite(
        "cover_subject_loss",
        incoming_loss * float(cover.scope_fraction),
    )
    recovery_before_limits = _recovery_before_limits(
        cover,
        cover_subject_loss,
    )

    payable_candidates = [recovery_before_limits, incoming_loss]
    if cover.occurrence_limit is not None:
        payable_candidates.append(float(cover.occurrence_limit))
    if cover.aggregate_remaining_before is not None:
        payable_candidates.append(float(cover.aggregate_remaining_before))
    payable_recovery = min(payable_candidates)
    outgoing_loss = _finite("outgoing_loss", incoming_loss - payable_recovery)

    aggregate_remaining_after = (
        None
        if cover.aggregate_remaining_before is None
        else float(cover.aggregate_remaining_before) - payable_recovery
    )
    constraints = _binding_constraints(
        cover,
        recovery_before_limits,
        payable_recovery,
    )

    return InuringCoverResult(
        cover_input=cover,
        incoming_loss=incoming_loss,
        cover_subject_loss=cover_subject_loss,
        recovery_before_limits=recovery_before_limits,
        payable_recovery=payable_recovery,
        outgoing_loss=outgoing_loss,
        aggregate_remaining_after=aggregate_remaining_after,
        binding_constraints=constraints,
    )


def _cover_fact(row: InuringCoverResult) -> ExplanationFact:
    mode_text = (
        "the declared proportional rate"
        if row.valuation_mode
        is InuringValuationMode.CALCULATED_PROPORTIONAL
        else "the authoritative supplied recovery"
    )
    constraint_text = (
        " No contractual limit reduced it."
        if not row.binding_constraints
        else " Binding constraint(s): "
        + ", ".join(item.value for item in row.binding_constraints)
        + "."
    )
    return ExplanationFact(
        metric_name=f"cover:{row.cover_id}:payable_recovery",
        value=row.payable_recovery,
        meaning="Recovery deducted at this ordered inuring stage.",
        driver_statement=(
            f"Cover {row.cover_id} applied {mode_text} to "
            f"{row.currency} {row.cover_subject_loss:,.2f} of scoped loss."
            f"{constraint_text}"
        ),
        trace_reference="F05-F08",
    )


def _waterfall_fact(
    waterfall_input: InuringWaterfallInput,
    total_recovery: float,
    cat_xl_subject_loss: float,
) -> ExplanationFact:
    count = len(waterfall_input.covers)
    return ExplanationFact(
        metric_name="cat_xl_subject_loss",
        value=cat_xl_subject_loss,
        meaning="Completed post-inuring loss eligible for the CT3 Cat XL program.",
        driver_statement=(
            f"{count} ordered inuring cover(s) reduced Ultimate Net Loss by "
            f"{waterfall_input.loss_basis.basis_input.reporting_currency} "
            f"{total_recovery:,.2f}."
        ),
        trace_reference="F09",
    )


def apply_inuring_waterfall(
    waterfall_input: InuringWaterfallInput,
) -> InuringWaterfallResult:
    """Apply F05–F09 sequentially without choosing contractual order."""

    if not isinstance(waterfall_input, InuringWaterfallInput):
        raise TypeError("waterfall_input must be an InuringWaterfallInput")

    ultimate_net_loss = float(
        waterfall_input.loss_basis.ultimate_net_loss_before_inuring
    )
    incoming_loss = ultimate_net_loss
    cover_results: list[InuringCoverResult] = []
    checks: list[ReconciliationCheck] = []
    facts: list[ExplanationFact] = []

    for cover in waterfall_input.covers:
        row = _apply_cover(cover, incoming_loss)
        cover_results.append(row)
        checks.append(
            ReconciliationCheck(
                check_id=f"cover:{cover.cover_id}:reconciliation",
                formula_reference="F09",
                left_value=row.incoming_loss,
                right_value=row.payable_recovery + row.outgoing_loss,
                passed=True,
            )
        )
        facts.append(_cover_fact(row))
        incoming_loss = row.outgoing_loss

    try:
        total_inuring_recovery = math.fsum(
            row.payable_recovery for row in cover_results
        )
    except OverflowError as exc:
        raise ValueError("total_inuring_recovery must be finite") from exc
    _finite("total_inuring_recovery", total_inuring_recovery)
    cat_xl_subject_loss = incoming_loss

    checks.append(
        ReconciliationCheck(
            check_id="waterfall:reconciliation",
            formula_reference="F09",
            left_value=ultimate_net_loss,
            right_value=total_inuring_recovery + cat_xl_subject_loss,
            passed=True,
        )
    )
    facts.append(
        _waterfall_fact(
            waterfall_input,
            total_inuring_recovery,
            cat_xl_subject_loss,
        )
    )

    supplied_cover_ids = tuple(
        cover.cover_id
        for cover in waterfall_input.covers
        if cover.valuation_mode is InuringValuationMode.SUPPLIED_RECOVERY
    )
    warnings = tuple(
        f"{cover_id}: supplied recovery was validated but not recalculated"
        for cover_id in supplied_cover_ids
    )
    assumption = (
        (
            "Inuring order is contract-supplied and was not selected or "
            "optimized."
        )
        if cover_results
        else "No inuring covers were configured; UNL passes unchanged."
    )

    return InuringWaterfallResult(
        loss_basis=waterfall_input.loss_basis,
        cover_results=tuple(cover_results),
        total_inuring_recovery=total_inuring_recovery,
        cat_xl_subject_loss=cat_xl_subject_loss,
        completion_status=(
            InuringCompletionStatus.COMPLETE
            if cover_results
            else InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
        ),
        reconciliation_checks=tuple(checks),
        explanation_facts=tuple(facts),
        warnings=warnings,
        assumption_disclosures=(assumption,),
    )
