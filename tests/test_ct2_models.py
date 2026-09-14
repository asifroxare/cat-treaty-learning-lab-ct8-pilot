"""Validation tests for immutable CT2 domain models."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct2_models import (
    BindingConstraint,
    ExplanationFact,
    InuringCompletionStatus,
    InuringCoverInput,
    InuringCoverResult,
    InuringCoverType,
    InuringValuationMode,
    InuringWaterfallInput,
    InuringWaterfallResult,
    LossBasisInput,
    LossBasisResult,
    LossComponent,
    LossComponentCategory,
    ReconciliationCheck,
)


def component(
    component_id: str = "lae",
    *,
    category: LossComponentCategory = (
        LossComponentCategory.LOSS_ADJUSTMENT_EXPENSE
    ),
    amount: float = 100.0,
    included: bool = True,
) -> LossComponent:
    return LossComponent(
        component_id=component_id,
        category=category,
        label=component_id,
        amount=amount,
        included=included,
        source_reference="scenario",
        rule_reference="F03",
    )


BASE_INPUT = LossBasisInput(
    occurrence_id="OCC-001",
    reporting_currency="USD",
    source_stage_declaration="insured_loss_after_policy_terms",
    source_reference="catalogue:1",
    initial_insured_loss=1_000.0,
    ground_up_loss=1_200.0,
    components=(
        component(),
        component(
            "salvage",
            category=LossComponentCategory.SALVAGE,
            amount=50.0,
        ),
    ),
)

BASE_BASIS = LossBasisResult(
    basis_input=BASE_INPUT,
    included_additions=100.0,
    applied_deductions=50.0,
    ultimate_net_loss_before_inuring=1_050.0,
    reconciliation_passed=True,
)


def supplied_cover(**changes: object) -> InuringCoverInput:
    values: dict[str, object] = {
        "cover_id": "FAC-1",
        "cover_type": InuringCoverType.FACULTATIVE,
        "order": 1,
        "valuation_mode": InuringValuationMode.SUPPLIED_RECOVERY,
        "scope_fraction": 0.5,
        "currency": "USD",
        "description": "Supplied facultative recovery",
        "source_reference": "fac-engine:1",
        "rule_reference": "F06",
        "supplied_recovery": 100.0,
        "recovery_source_id": "REC-1",
    }
    values.update(changes)
    return InuringCoverInput(**values)


BASE_ROW = InuringCoverResult(
    cover_input=supplied_cover(),
    incoming_loss=1_050.0,
    cover_subject_loss=525.0,
    recovery_before_limits=100.0,
    payable_recovery=100.0,
    outgoing_loss=950.0,
    aggregate_remaining_after=None,
    binding_constraints=(),
)


BASE_CHECK = ReconciliationCheck(
    check_id="waterfall-total",
    formula_reference="F09",
    left_value=1_050.0,
    right_value=1_050.0,
    passed=True,
)


BASE_FACT = ExplanationFact(
    metric_name="cat_xl_subject_loss",
    value=950.0,
    meaning="Loss reaching Cat XL",
    driver_statement="One supplied recovery reduced the UNL by USD 100.",
    trace_reference="F09",
)


def test_ct2_enum_literals_are_frozen() -> None:
    assert LossComponentCategory.CONTRACT_EXCLUSION.value == "contract_exclusion"
    assert InuringCoverType.PER_RISK_XL.value == "per_risk_xl"
    assert (
        InuringValuationMode.CALCULATED_PROPORTIONAL.value
        == "calculated_proportional"
    )
    assert InuringCompletionStatus.COMPLETE.value == "complete"
    assert BindingConstraint.AGGREGATE_REMAINING.value == "aggregate_remaining"


def test_loss_component_exclusion_changes_effect_not_validation() -> None:
    excluded = component(included=False)

    assert excluded.amount == 100.0
    assert excluded.applied_amount == 0.0

    with pytest.raises(ValueError, match="non-negative"):
        component(amount=-1.0, included=False)


@pytest.mark.parametrize("invalid", [math.nan, math.inf, -1.0, True, "100"])
def test_loss_component_rejects_invalid_amount(invalid: object) -> None:
    with pytest.raises(ValueError):
        component(amount=invalid)  # type: ignore[arg-type]


def test_loss_basis_input_is_immutable_and_requires_unique_components() -> None:
    with pytest.raises(FrozenInstanceError):
        BASE_INPUT.initial_insured_loss = 2.0  # type: ignore[misc]

    with pytest.raises(ValueError, match="unique"):
        replace(BASE_INPUT, components=(component(), component()))


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    [
        ("occurrence_id", " "),
        ("reporting_currency", ""),
        ("source_stage_declaration", ""),
        ("source_reference", ""),
        ("initial_insured_loss", -1.0),
        ("initial_insured_loss", math.nan),
        ("ground_up_loss", -1.0),
        ("components", []),
    ],
)
def test_loss_basis_input_rejects_invalid_values(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(ValueError):
        replace(BASE_INPUT, **{field_name: invalid})


def test_loss_basis_result_enforces_f03_f04() -> None:
    assert BASE_BASIS.ultimate_net_loss_before_inuring == 1_050.0

    for changes in (
        {"included_additions": 99.0},
        {"applied_deductions": 49.0},
        {"ultimate_net_loss_before_inuring": 1_049.0},
        {"reconciliation_passed": False},
    ):
        with pytest.raises(ValueError):
            replace(BASE_BASIS, **changes)


def test_negative_unl_attempt_is_rejected_not_floored() -> None:
    excessive = LossBasisInput(
        occurrence_id="OCC-NEG",
        reporting_currency="USD",
        source_stage_declaration="insured_loss_after_policy_terms",
        source_reference="scenario",
        initial_insured_loss=100.0,
        components=(
            component(
                "deduction",
                category=LossComponentCategory.CONTRACT_EXCLUSION,
                amount=101.0,
            ),
        ),
    )

    with pytest.raises(ValueError, match="deductions exceed"):
        LossBasisResult(
            basis_input=excessive,
            included_additions=0.0,
            applied_deductions=101.0,
            ultimate_net_loss_before_inuring=0.0,
            reconciliation_passed=True,
        )


def test_calculated_quota_share_model_is_valid() -> None:
    cover = InuringCoverInput(
        cover_id="QS-1",
        cover_type=InuringCoverType.QUOTA_SHARE,
        order=1,
        valuation_mode=InuringValuationMode.CALCULATED_PROPORTIONAL,
        scope_fraction=1.0,
        cession_rate=0.4,
        currency="USD",
        description="40 percent quota share",
        source_reference="contract:qs",
        rule_reference="F05-F08",
    )

    assert cover.cession_rate == 0.4
    assert cover.supplied_recovery is None


@pytest.mark.parametrize(
    "changes",
    [
        {"cession_rate": None},
        {"cession_rate": -0.1},
        {"cession_rate": 1.1},
        {"supplied_recovery": 1.0},
        {"recovery_source_id": "REC"},
        {"cover_type": InuringCoverType.SURPLUS_SHARE},
    ],
)
def test_calculated_mode_rejects_invalid_or_misleading_inputs(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "cover_id": "QS-1",
        "cover_type": InuringCoverType.QUOTA_SHARE,
        "order": 1,
        "valuation_mode": InuringValuationMode.CALCULATED_PROPORTIONAL,
        "scope_fraction": 1.0,
        "cession_rate": 0.4,
        "currency": "USD",
        "description": "Quota share",
        "source_reference": "contract:qs",
        "rule_reference": "F05-F08",
    }
    values.update(changes)
    with pytest.raises(ValueError):
        InuringCoverInput(**values)


def test_supplied_mode_accepts_all_nonproportional_cover_types() -> None:
    for cover_type in (
        InuringCoverType.SURPLUS_SHARE,
        InuringCoverType.FACULTATIVE,
        InuringCoverType.PER_RISK_XL,
        InuringCoverType.OTHER,
    ):
        assert supplied_cover(cover_type=cover_type).cover_type is cover_type


def test_waterfall_input_accepts_explicit_contiguous_order() -> None:
    inputs = InuringWaterfallInput(
        loss_basis=BASE_BASIS,
        covers=(
            supplied_cover(),
            supplied_cover(
                cover_id="FAC-2",
                order=2,
                recovery_source_id="REC-2",
            ),
        ),
    )

    assert tuple(item.order for item in inputs.covers) == (1, 2)


@pytest.mark.parametrize(
    ("covers", "message"),
    [
        ((supplied_cover(order=2),), "contiguous"),
        (
            (
                supplied_cover(),
                supplied_cover(order=2, recovery_source_id="REC-2"),
            ),
            "cover_id",
        ),
        (
            (
                supplied_cover(),
                supplied_cover(cover_id="FAC-2", order=2),
            ),
            "recovery_source_id",
        ),
        ((supplied_cover(currency="EUR"),), "reporting_currency"),
    ],
)
def test_waterfall_input_rejects_collection_contract_violations(
    covers: tuple[InuringCoverInput, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        InuringWaterfallInput(loss_basis=BASE_BASIS, covers=covers)


def test_waterfall_input_is_immutable() -> None:
    inputs = InuringWaterfallInput(loss_basis=BASE_BASIS)

    with pytest.raises(FrozenInstanceError):
        inputs.covers = (supplied_cover(),)  # type: ignore[misc]


@pytest.mark.parametrize(
    "changes",
    [
        {"supplied_recovery": None},
        {"supplied_recovery": -1.0},
        {"recovery_source_id": None},
        {"recovery_source_id": " "},
        {"cession_rate": 0.2},
        {"scope_fraction": -0.1},
        {"scope_fraction": 1.1},
        {"occurrence_limit": 0.0},
        {"aggregate_remaining_before": -1.0},
        {"order": 0},
        {"order": True},
    ],
)
def test_supplied_mode_rejects_invalid_values(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        supplied_cover(**changes)


def test_cover_result_accepts_and_reconciles_aggregate_state() -> None:
    row = replace(
        BASE_ROW,
        cover_input=replace(
            BASE_ROW.cover_input,
            aggregate_remaining_before=100.0,
        ),
        aggregate_remaining_after=0.0,
        binding_constraints=(BindingConstraint.AGGREGATE_REMAINING,),
    )

    assert row.aggregate_remaining_after == 0.0


@pytest.mark.parametrize(
    "changes",
    [
        {"cover_subject_loss": 1_051.0},
        {"recovery_before_limits": 526.0},
        {"payable_recovery": 101.0},
        {"outgoing_loss": 949.0},
        {"aggregate_remaining_after": 10.0},
        {"binding_constraints": (BindingConstraint.OCCURRENCE_LIMIT,)},
        {"binding_constraints": []},
    ],
)
def test_cover_result_rejects_invalid_reconciliation(
    changes: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        replace(BASE_ROW, **changes)


def test_reduced_recovery_requires_named_binding_constraint() -> None:
    with pytest.raises(ValueError, match="binding constraint"):
        replace(
            BASE_ROW,
            recovery_before_limits=200.0,
            payable_recovery=100.0,
        )


def test_occurrence_limit_can_bind_recovery() -> None:
    row = replace(
        BASE_ROW,
        recovery_before_limits=200.0,
        cover_input=replace(BASE_ROW.cover_input, occurrence_limit=100.0),
        binding_constraints=(BindingConstraint.OCCURRENCE_LIMIT,),
    )

    assert row.payable_recovery == 100.0


def test_reconciliation_check_matches_numeric_values() -> None:
    with pytest.raises(ValueError, match="passed"):
        replace(BASE_CHECK, right_value=1_049.0)

    failed = ReconciliationCheck(
        check_id="failed-check",
        formula_reference="F09",
        left_value=1.0,
        right_value=2.0,
        passed=False,
    )
    assert failed.passed is False


def test_completed_waterfall_with_one_cover_is_valid_and_immutable() -> None:
    result = InuringWaterfallResult(
        loss_basis=BASE_BASIS,
        cover_results=(BASE_ROW,),
        total_inuring_recovery=100.0,
        cat_xl_subject_loss=950.0,
        completion_status=InuringCompletionStatus.COMPLETE,
        reconciliation_checks=(BASE_CHECK,),
        explanation_facts=(BASE_FACT,),
        assumption_disclosures=("Order is contract-supplied.",),
    )

    assert result.cat_xl_subject_loss == 950.0
    with pytest.raises(FrozenInstanceError):
        result.cat_xl_subject_loss = 1.0  # type: ignore[misc]


def test_no_cover_completion_requires_unl_as_subject_loss() -> None:
    result = InuringWaterfallResult(
        loss_basis=BASE_BASIS,
        cover_results=(),
        total_inuring_recovery=0.0,
        cat_xl_subject_loss=1_050.0,
        completion_status=(
            InuringCompletionStatus.COMPLETE_NO_INURING_COVERS
        ),
        reconciliation_checks=(BASE_CHECK,),
        explanation_facts=(),
    )

    assert result.cat_xl_subject_loss == 1_050.0


@pytest.mark.parametrize(
    "changes",
    [
        {"total_inuring_recovery": 99.0},
        {"cat_xl_subject_loss": 949.0},
        {"completion_status": InuringCompletionStatus.COMPLETE_NO_INURING_COVERS},
        {"reconciliation_checks": ()},
        {"reconciliation_checks": (replace(BASE_CHECK, left_value=1.0,
                                               right_value=2.0, passed=False),)},
        {
            "cover_results": (
                replace(
                    BASE_ROW,
                    cover_input=replace(BASE_ROW.cover_input, currency="EUR"),
                ),
            )
        },
    ],
)
def test_completed_waterfall_rejects_invalid_state(
    changes: dict[str, object],
) -> None:
    values: dict[str, object] = {
        "loss_basis": BASE_BASIS,
        "cover_results": (BASE_ROW,),
        "total_inuring_recovery": 100.0,
        "cat_xl_subject_loss": 950.0,
        "completion_status": InuringCompletionStatus.COMPLETE,
        "reconciliation_checks": (BASE_CHECK,),
        "explanation_facts": (BASE_FACT,),
    }
    values.update(changes)
    with pytest.raises(ValueError):
        InuringWaterfallResult(**values)


def test_two_cover_waterfall_must_be_contiguous_and_sequential() -> None:
    second = replace(
        BASE_ROW,
        cover_input=replace(
            BASE_ROW.cover_input,
            cover_id="FAC-2",
            order=2,
            recovery_source_id="REC-2",
        ),
        incoming_loss=950.0,
        cover_subject_loss=475.0,
        recovery_before_limits=50.0,
        payable_recovery=50.0,
        outgoing_loss=900.0,
    )
    check = replace(BASE_CHECK, right_value=1_050.0)

    result = InuringWaterfallResult(
        loss_basis=BASE_BASIS,
        cover_results=(BASE_ROW, second),
        total_inuring_recovery=150.0,
        cat_xl_subject_loss=900.0,
        completion_status=InuringCompletionStatus.COMPLETE,
        reconciliation_checks=(check,),
        explanation_facts=(),
    )
    assert len(result.cover_results) == 2

    with pytest.raises(ValueError, match="contiguous"):
        replace(
            result,
            cover_results=(
                BASE_ROW,
                replace(
                    second,
                    cover_input=replace(second.cover_input, order=3),
                ),
            ),
        )
    with pytest.raises(ValueError, match="sequential"):
        replace(result, cover_results=(BASE_ROW, replace(second, incoming_loss=951.0,
                                                          outgoing_loss=901.0)))
