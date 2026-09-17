"""CT6 catalogue CT2--CT5 orchestration acceptance."""

import pytest

from cat_treaty.ct6_orchestration import CT6CatalogueRunResult, run_catalogue
from tests.test_ct6_models import valid_request


def test_catalogue_runs_ct2_through_ct5_with_both_capacity_views() -> None:
    result = run_catalogue(valid_request())

    assert isinstance(result, CT6CatalogueRunResult)
    assert result.ct4_result.occurrence_rows[0].subject_loss == 40_500_000.0
    assert result.ct4_result.occurrence_rows[0].gross_contractual_recovery_pre_annual_capacity == 20_000_000.0
    row = result.ct5_result.occurrence_rows[0]
    assert row.gross_contractual_recovery_pre_annual_capacity == 20_000_000.0
    assert row.gross_contractual_recovery == 20_000_000.0
    assert row.capacity_constrained_recovery_shortfall == 0.0
    assert row.reinstatement_premium_payable > 0.0


def test_catalogue_builds_ct4_and_ct5_identities_bound_together() -> None:
    result = run_catalogue(valid_request())
    assert result.ct5_identity.simulation_id == result.ct4_identity.simulation_id
    assert result.ct5_identity.ct4_input_hash == result.ct4_identity.input_hash
    assert result.ct5_identity.ct4_result_hash == result.ct4_identity.result_hash
    for digest in (
        result.ct4_identity.input_hash,
        result.ct4_identity.result_hash,
        result.ct5_identity.input_hash,
        result.ct5_identity.result_hash,
    ):
        assert len(digest) == 64


def test_identical_catalogue_request_is_deterministic() -> None:
    first = run_catalogue(valid_request())
    second = run_catalogue(valid_request())
    assert first.ct4_result == second.ct4_result
    assert first.ct5_result == second.ct5_result
    assert first.ct4_identity == second.ct4_identity
    assert first.ct5_identity == second.ct5_identity


def test_allowed_component_permutation_preserves_all_identities() -> None:
    request = valid_request()
    occurrence = request.input.trials[0].occurrences[0]
    extra = occurrence.loss_basis.components[0].model_copy(
        update={"component_id": "I2", "label": "other excluded"}
    )
    first_occurrence = occurrence.model_copy(
        update={"loss_basis": occurrence.loss_basis.model_copy(
            update={"components": occurrence.loss_basis.components + (extra,)}
        )}
    )
    second_occurrence = first_occurrence.model_copy(
        update={"loss_basis": first_occurrence.loss_basis.model_copy(
            update={"components": tuple(reversed(first_occurrence.loss_basis.components))}
        )}
    )
    trial = request.input.trials[0]
    first = request.model_copy(update={"input": request.input.model_copy(
        update={"trials": (trial.model_copy(update={"occurrences": (first_occurrence,)}),)}
    )})
    second = request.model_copy(update={"input": request.input.model_copy(
        update={"trials": (trial.model_copy(update={"occurrences": (second_occurrence,)}),)}
    )})

    first_result = run_catalogue(first)
    second_result = run_catalogue(second)
    assert first_result.ct4_identity == second_result.ct4_identity
    assert first_result.ct5_identity == second_result.ct5_identity


def test_blocked_geometry_fails_before_ct4_or_ct5_result() -> None:
    request = valid_request()
    layer = request.input.program.layers[0]
    second_layer = layer.model_copy(update={"layer_id": "L2", "attachment": 20_000_000.0})
    program = request.input.program.model_copy(
        update={"layers": (layer, second_layer), "intentional_gap_acknowledged": False}
    )
    layer_terms = request.input.treaty_terms.layer_terms[0]
    second_terms = layer_terms.model_copy(update={"layer_id": "L2"})
    terms = request.input.treaty_terms.model_copy(
        update={"layer_terms": (layer_terms, second_terms)}
    )
    blocked = request.model_copy(update={"input": request.input.model_copy(
        update={"program": program, "treaty_terms": terms}
    )})
    with pytest.raises(ValueError, match="preflight failed"):
        run_catalogue(blocked)


def test_all_empty_catalogue_uses_declared_program_without_inventing_events() -> None:
    request = valid_request()
    trial = request.input.trials[0].model_copy(update={"occurrences": ()})
    empty = request.model_copy(update={"input": request.input.model_copy(
        update={"trials": (trial,)}
    )})
    result = run_catalogue(empty)
    assert result.ct4_result.occurrence_rows == ()
    assert result.ct5_result.occurrence_rows == ()
    assert result.ct5_result.annual_rows[0].event_rows == ()
    assert result.ct5_result.annual_rows[0].layer_summaries[0].total_recovery == 0.0


def test_catalogue_orchestrator_rejects_wrong_type() -> None:
    with pytest.raises(TypeError, match="CatalogueRunRequest"):
        run_catalogue(object())  # type: ignore[arg-type]
