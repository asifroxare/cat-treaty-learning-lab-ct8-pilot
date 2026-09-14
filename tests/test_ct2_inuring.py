"""F05–F09 ordered inuring-reinsurance waterfall tests."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cat_treaty.ct2_models import (
    BindingConstraint,
    InuringCompletionStatus,
    InuringCoverInput,
    InuringCoverType,
    InuringValuationMode,
    InuringWaterfallInput,
    LossBasisInput,
)
from cat_treaty.inuring import apply_inuring_waterfall
from cat_treaty.loss_basis import build_loss_basis


LOSS_BASIS = build_loss_basis(
    LossBasisInput(
        occurrence_id="OCC-001",
        reporting_currency="USD",
        source_stage_declaration="insured_loss_after_policy_terms",
        source_reference="catalogue:EVT-001",
        initial_insured_loss=1_000.0,
    )
)


def quota_share(
    *,
    cover_id: str = "QS-1",
    order: int = 1,
    scope_fraction: float = 1.0,
    cession_rate: float = 0.4,
    occurrence_limit: float | None = None,
    aggregate_remaining_before: float | None = None,
) -> InuringCoverInput:
    return InuringCoverInput(
        cover_id=cover_id,
        cover_type=InuringCoverType.QUOTA_SHARE,
        order=order,
        valuation_mode=InuringValuationMode.CALCULATED_PROPORTIONAL,
        scope_fraction=scope_fraction,
        cession_rate=cession_rate,
        occurrence_limit=occurrence_limit,
        aggregate_remaining_before=aggregate_remaining_before,
        currency="USD",
        description="Declared aggregate quota share",
        source_reference=f"contract:{cover_id}",
        rule_reference="F05-F08",
    )


def supplied(
    *,
    cover_id: str = "FAC-1",
    order: int = 1,
    scope_fraction: float = 1.0,
    supplied_recovery: float = 250.0,
    recovery_source_id: str = "REC-1",
    occurrence_limit: float | None = None,
    aggregate_remaining_before: float | None = None,
    cover_type: InuringCoverType = InuringCoverType.FACULTATIVE,
) -> InuringCoverInput:
    return InuringCoverInput(
        cover_id=cover_id,
        cover_type=cover_type,
        order=order,
        valuation_mode=InuringValuationMode.SUPPLIED_RECOVERY,
        scope_fraction=scope_fraction,
        supplied_recovery=supplied_recovery,
        recovery_source_id=recovery_source_id,
        occurrence_limit=occurrence_limit,
        aggregate_remaining_before=aggregate_remaining_before,
        currency="USD",
        description="Authoritative supplied recovery",
        source_reference=f"upstream:{recovery_source_id}",
        rule_reference="F05-F08",
    )


def run(*covers: InuringCoverInput):
    return apply_inuring_waterfall(
        InuringWaterfallInput(loss_basis=LOSS_BASIS, covers=tuple(covers))
    )


def test_g18_no_inuring_covers_preserves_unl() -> None:
    result = run()

    assert result.completion_status is (
        InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
    )
    assert result.cover_results == ()
    assert result.total_inuring_recovery == 0.0
    assert result.cat_xl_subject_loss == 1_000.0
    assert len(result.reconciliation_checks) == 1
    assert result.reconciliation_checks[0].passed is True
    assert result.assumption_disclosures == (
        "No inuring covers were configured; UNL passes unchanged.",
    )


def test_g06_g19_quota_share_inures_before_cat_xl() -> None:
    result = run(quota_share(cession_rate=0.4))
    row = result.cover_results[0]

    assert row.incoming_loss == 1_000.0
    assert row.cover_subject_loss == 1_000.0
    assert row.recovery_before_limits == 400.0
    assert row.payable_recovery == 400.0
    assert row.outgoing_loss == 600.0
    assert result.total_inuring_recovery == 400.0
    assert result.cat_xl_subject_loss == 600.0
    assert result.completion_status is InuringCompletionStatus.COMPLETE


def test_f05_scope_fraction_applies_before_cession_rate() -> None:
    result = run(quota_share(scope_fraction=0.5, cession_rate=0.4))
    row = result.cover_results[0]

    assert row.cover_subject_loss == 500.0
    assert row.recovery_before_limits == 200.0
    assert row.payable_recovery == 200.0
    assert row.outgoing_loss == 800.0


def test_g22_supplied_recovery_is_preserved() -> None:
    result = run(supplied(supplied_recovery=250.0))
    row = result.cover_results[0]

    assert row.recovery_before_limits == 250.0
    assert row.payable_recovery == 250.0
    assert row.outgoing_loss == 750.0
    assert result.warnings == (
        "FAC-1: supplied recovery was validated but not recalculated",
    )


def test_g23_zero_scope_and_zero_supplied_recovery_remain_visible() -> None:
    result = run(
        supplied(scope_fraction=0.0, supplied_recovery=0.0)
    )
    row = result.cover_results[0]

    assert row.cover_subject_loss == 0.0
    assert row.recovery_before_limits == 0.0
    assert row.payable_recovery == 0.0
    assert row.outgoing_loss == 1_000.0
    assert result.cat_xl_subject_loss == 1_000.0


def test_g23_nonzero_supplied_recovery_with_zero_scope_is_rejected() -> None:
    waterfall_input = InuringWaterfallInput(
        loss_basis=LOSS_BASIS,
        covers=(supplied(scope_fraction=0.0, supplied_recovery=1.0),),
    )

    with pytest.raises(ValueError, match="cover_subject_loss"):
        apply_inuring_waterfall(waterfall_input)


def test_supplied_recovery_cannot_exceed_partial_scope() -> None:
    waterfall_input = InuringWaterfallInput(
        loss_basis=LOSS_BASIS,
        covers=(supplied(scope_fraction=0.2, supplied_recovery=201.0),),
    )

    with pytest.raises(ValueError, match="cover_subject_loss"):
        apply_inuring_waterfall(waterfall_input)


def test_supplied_recovery_above_scope_is_strictly_rejected() -> None:
    waterfall_input = InuringWaterfallInput(
        loss_basis=LOSS_BASIS,
        covers=(
            supplied(
                scope_fraction=0.2,
                supplied_recovery=200.0000001,
            ),
        ),
    )

    with pytest.raises(ValueError, match="cover_subject_loss"):
        apply_inuring_waterfall(waterfall_input)


def test_g21_occurrence_limit_is_named_when_binding() -> None:
    result = run(
        quota_share(cession_rate=0.8, occurrence_limit=300.0)
    )
    row = result.cover_results[0]

    assert row.recovery_before_limits == 800.0
    assert row.payable_recovery == 300.0
    assert row.binding_constraints == (BindingConstraint.OCCURRENCE_LIMIT,)
    assert row.outgoing_loss == 700.0


def test_g21_aggregate_limit_and_after_state_are_named() -> None:
    result = run(
        quota_share(
            cession_rate=0.8,
            aggregate_remaining_before=250.0,
        )
    )
    row = result.cover_results[0]

    assert row.payable_recovery == 250.0
    assert row.aggregate_remaining_before == 250.0
    assert row.aggregate_remaining_after == 0.0
    assert row.binding_constraints == (
        BindingConstraint.AGGREGATE_REMAINING,
    )


def test_both_equal_limits_are_disclosed_as_binding() -> None:
    result = run(
        quota_share(
            cession_rate=0.8,
            occurrence_limit=300.0,
            aggregate_remaining_before=300.0,
        )
    )

    assert result.cover_results[0].binding_constraints == (
        BindingConstraint.OCCURRENCE_LIMIT,
        BindingConstraint.AGGREGATE_REMAINING,
    )


def test_zero_aggregate_is_distinct_from_unbounded() -> None:
    bounded = run(
        quota_share(aggregate_remaining_before=0.0)
    ).cover_results[0]
    unbounded = run(quota_share()).cover_results[0]

    assert bounded.payable_recovery == 0.0
    assert bounded.aggregate_remaining_after == 0.0
    assert bounded.binding_constraints == (
        BindingConstraint.AGGREGATE_REMAINING,
    )
    assert unbounded.payable_recovery == 400.0
    assert unbounded.aggregate_remaining_after is None
    assert unbounded.binding_constraints == ()


def test_nonbinding_limits_are_retained_without_binding_labels() -> None:
    result = run(
        quota_share(
            occurrence_limit=500.0,
            aggregate_remaining_before=600.0,
        )
    )
    row = result.cover_results[0]

    assert row.payable_recovery == 400.0
    assert row.aggregate_remaining_after == 200.0
    assert row.binding_constraints == ()


def test_f08_multiple_covers_consume_sequential_outgoing_loss() -> None:
    result = run(
        quota_share(cession_rate=0.4),
        supplied(
            cover_id="FAC-2",
            order=2,
            supplied_recovery=100.0,
            recovery_source_id="REC-2",
        ),
    )

    first, second = result.cover_results
    assert first.outgoing_loss == 600.0
    assert second.incoming_loss == 600.0
    assert second.outgoing_loss == 500.0
    assert result.total_inuring_recovery == 500.0
    assert result.cat_xl_subject_loss == 500.0


def test_g20_order_is_respected_and_can_change_result() -> None:
    facultative_first = run(
        supplied(supplied_recovery=300.0),
        quota_share(cover_id="QS-2", order=2, cession_rate=0.5),
    )
    quota_first = run(
        quota_share(cover_id="QS-1", cession_rate=0.5),
        supplied(
            cover_id="FAC-2",
            order=2,
            supplied_recovery=300.0,
            recovery_source_id="REC-2",
        ),
    )

    assert facultative_first.cat_xl_subject_loss == 350.0
    assert quota_first.cat_xl_subject_loss == 200.0
    assert all(
        "not selected or optimized" in disclosure
        for disclosure in quota_first.assumption_disclosures
    )


def test_g24_duplicate_source_is_rejected_before_engine_execution() -> None:
    with pytest.raises(ValueError, match="recovery_source_id"):
        InuringWaterfallInput(
            loss_basis=LOSS_BASIS,
            covers=(
                supplied(),
                supplied(cover_id="FAC-2", order=2),
            ),
        )


def test_every_row_and_total_have_passed_f09_checks() -> None:
    result = run(
        quota_share(cession_rate=0.4),
        supplied(
            cover_id="FAC-2",
            order=2,
            supplied_recovery=100.0,
            recovery_source_id="REC-2",
        ),
    )

    assert len(result.reconciliation_checks) == 3
    assert all(check.formula_reference == "F09" for check in result.reconciliation_checks)
    assert all(check.passed for check in result.reconciliation_checks)
    assert (
        result.loss_basis.ultimate_net_loss_before_inuring
        == result.total_inuring_recovery + result.cat_xl_subject_loss
    )


def test_explanation_facts_are_deterministic_and_traceable() -> None:
    inputs = (
        quota_share(cession_rate=0.4),
        supplied(
            cover_id="FAC-2",
            order=2,
            supplied_recovery=100.0,
            recovery_source_id="REC-2",
        ),
    )

    first = run(*inputs)
    second = run(*inputs)

    assert first.explanation_facts == second.explanation_facts
    assert len(first.explanation_facts) == 3
    assert first.explanation_facts[-1].trace_reference == "F09"
    assert first.explanation_facts[-1].value == first.cat_xl_subject_loss


def test_complete_result_and_rows_are_immutable_and_inputs_unchanged() -> None:
    cover = quota_share()
    result = run(cover)

    assert cover.cession_rate == 0.4
    with pytest.raises(FrozenInstanceError):
        result.cat_xl_subject_loss = 0.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.cover_results[0].outgoing_loss = 0.0  # type: ignore[misc]


def test_invalid_engine_input_type_is_rejected() -> None:
    for invalid in (None, True, (), LOSS_BASIS):
        with pytest.raises(TypeError, match="InuringWaterfallInput"):
            apply_inuring_waterfall(invalid)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "cover_type",
    [
        InuringCoverType.SURPLUS_SHARE,
        InuringCoverType.FACULTATIVE,
        InuringCoverType.PER_RISK_XL,
        InuringCoverType.OTHER,
    ],
)
def test_all_nonproportional_types_use_supplied_recovery(
    cover_type: InuringCoverType,
) -> None:
    result = run(supplied(cover_type=cover_type))

    assert result.cover_results[0].cover_type is cover_type
    assert result.cover_results[0].payable_recovery == 250.0
