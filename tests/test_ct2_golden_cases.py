"""Consolidated CT2 golden-case acceptance and milestone traceability."""

from dataclasses import replace

import pytest

from cat_treaty.ct2_models import (
    BindingConstraint,
    InuringCompletionStatus,
    InuringCoverInput,
    InuringCoverType,
    InuringValuationMode,
    InuringWaterfallInput,
    LossBasisInput,
    LossComponent,
    LossComponentCategory,
)
from cat_treaty.inuring import apply_inuring_waterfall
from cat_treaty.loss_basis import build_loss_basis


def loss_basis(
    amount: float = 1_000.0,
    components: tuple[LossComponent, ...] = (),
):
    return build_loss_basis(
        LossBasisInput(
            occurrence_id="GOLDEN-OCC",
            reporting_currency="USD",
            source_stage_declaration="insured_loss_after_policy_terms",
            source_reference="golden-case",
            initial_insured_loss=amount,
            components=components,
        )
    )


def quota(order: int = 1, rate: float = 0.4, **changes: object):
    values: dict[str, object] = {
        "cover_id": f"QS-{order}",
        "cover_type": InuringCoverType.QUOTA_SHARE,
        "order": order,
        "valuation_mode": InuringValuationMode.CALCULATED_PROPORTIONAL,
        "scope_fraction": 1.0,
        "cession_rate": rate,
        "currency": "USD",
        "description": "Golden quota share",
        "source_reference": "contract:qs",
        "rule_reference": "F05-F09",
    }
    values.update(changes)
    return InuringCoverInput(**values)


def supplied(order: int = 1, recovery: float = 250.0, **changes: object):
    values: dict[str, object] = {
        "cover_id": f"FAC-{order}",
        "cover_type": InuringCoverType.FACULTATIVE,
        "order": order,
        "valuation_mode": InuringValuationMode.SUPPLIED_RECOVERY,
        "scope_fraction": 1.0,
        "supplied_recovery": recovery,
        "recovery_source_id": f"REC-{order}",
        "currency": "USD",
        "description": "Golden supplied recovery",
        "source_reference": "upstream:fac",
        "rule_reference": "F05-F09",
    }
    values.update(changes)
    return InuringCoverInput(**values)


def waterfall(*covers: InuringCoverInput, basis=None):
    selected_basis = loss_basis() if basis is None else basis
    return apply_inuring_waterfall(
        InuringWaterfallInput(
            loss_basis=selected_basis,
            covers=tuple(covers),
        )
    )


def test_ct0_to_ct2_golden_case_register_has_no_gaps_or_collisions() -> None:
    owners = {
        **{f"G{number:02d}": "CT1" for number in range(1, 6)},
        "G06": "CT2",
        **{f"G{number:02d}": "later" for number in range(7, 14)},
        **{f"G{number:02d}": "CT1" for number in range(14, 17)},
        **{f"G{number:02d}": "CT2" for number in range(17, 26)},
    }

    assert set(owners) == {f"G{number:02d}" for number in range(1, 26)}
    assert {case_id for case_id, owner in owners.items() if owner == "CT2"} == {
        "G06",
        *{f"G{number:02d}" for number in range(17, 26)},
    }


def test_g06_and_g19_quota_share_recovery_precedes_cat_xl() -> None:
    result = waterfall(quota(rate=0.4))

    assert result.cover_results[0].payable_recovery == 400.0
    assert result.cat_xl_subject_loss == 600.0


def test_g17_unl_additions_deductions_and_exclusion_visibility() -> None:
    components = (
        LossComponent(
            component_id="lae",
            category=LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE,
            label="LAE",
            amount=100.0,
            included=True,
            source_reference="scenario",
            rule_reference="F03",
        ),
        LossComponent(
            component_id="salvage",
            category=LossComponentCategory.SALVAGE,
            label="Salvage",
            amount=40.0,
            included=True,
            source_reference="scenario",
            rule_reference="F03",
        ),
        LossComponent(
            component_id="excluded-cost",
            category=LossComponentCategory.OTHER_INCLUDED_COST,
            label="Excluded cost",
            amount=500.0,
            included=False,
            source_reference="scenario",
            rule_reference="F03",
        ),
    )
    result = loss_basis(components=components)

    assert result.included_additions == 100.0
    assert result.applied_deductions == 40.0
    assert result.ultimate_net_loss_before_inuring == 1_060.0
    assert result.basis_input.components[2].applied_amount == 0.0


def test_g18_no_cover_identity_and_completion_status() -> None:
    result = waterfall()

    assert result.total_inuring_recovery == 0.0
    assert result.cat_xl_subject_loss == 1_000.0
    assert result.completion_status is (
        InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
    )


def test_g20_reversing_declared_order_changes_result_without_optimization() -> None:
    supplied_first = waterfall(supplied(recovery=300.0), quota(2, rate=0.5))
    quota_first = waterfall(quota(rate=0.5), supplied(2, recovery=300.0))

    assert supplied_first.cat_xl_subject_loss == 350.0
    assert quota_first.cat_xl_subject_loss == 200.0
    assert supplied_first.cover_results[0].cover_type is InuringCoverType.FACULTATIVE
    assert quota_first.cover_results[0].cover_type is InuringCoverType.QUOTA_SHARE


def test_g21_binding_occurrence_and_aggregate_limits_are_named() -> None:
    result = waterfall(
        quota(
            rate=0.8,
            occurrence_limit=300.0,
            aggregate_remaining_before=300.0,
        )
    )
    row = result.cover_results[0]

    assert row.payable_recovery == 300.0
    assert row.aggregate_remaining_after == 0.0
    assert row.binding_constraints == (
        BindingConstraint.OCCURRENCE_LIMIT,
        BindingConstraint.AGGREGATE_REMAINING,
    )


def test_g22_authoritative_supplied_recovery_is_preserved() -> None:
    result = waterfall(supplied(recovery=250.0))

    assert result.cover_results[0].recovery_before_limits == 250.0
    assert result.cover_results[0].payable_recovery == 250.0
    assert result.warnings


def test_g23_zero_scope_is_visible_and_nonzero_recovery_is_rejected() -> None:
    valid = waterfall(
        supplied(recovery=0.0, scope_fraction=0.0)
    ).cover_results[0]

    assert valid.cover_subject_loss == 0.0
    assert valid.payable_recovery == 0.0
    assert valid.outgoing_loss == 1_000.0

    invalid = InuringWaterfallInput(
        loss_basis=loss_basis(),
        covers=(supplied(recovery=1.0, scope_fraction=0.0),),
    )
    with pytest.raises(ValueError, match="cover_subject_loss"):
        apply_inuring_waterfall(invalid)


def test_g24_duplicate_recovery_source_fails_before_completed_output() -> None:
    first = supplied()
    duplicate = replace(first, cover_id="FAC-2", order=2)

    with pytest.raises(ValueError, match="recovery_source_id"):
        InuringWaterfallInput(
            loss_basis=loss_basis(),
            covers=(first, duplicate),
        )


def test_g25_negative_unl_attempt_fails_instead_of_flooring() -> None:
    exclusion = LossComponent(
        component_id="exclusion",
        category=LossComponentCategory.CONTRACT_EXCLUSION,
        label="Exclusion",
        amount=1_001.0,
        included=True,
        source_reference="scenario",
        rule_reference="F03",
    )

    with pytest.raises(ValueError, match="deductions exceed"):
        loss_basis(components=(exclusion,))
