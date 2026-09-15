"""Catalogue-defined application, preflight, ordering and F17-F20 tests."""

from dataclasses import FrozenInstanceError, replace

import pytest

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import InuringWaterfallInput
from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.ct4_models import (
    CT4AnnualTrialInput,
    CT4CatalogueResult,
    CT4OccurrenceInput,
    OccurrenceDefinitionMode,
    PreflightIssueCode,
)
from cat_treaty.simulation import (
    CT4PreflightError,
    apply_catalogue_simulation,
    catalogue_preflight_issues,
)
from tests.test_ct3_models import layer
from tests.test_ct3_program import program_at_loss
from tests.test_ct4_models import hours_scenario, simulation


def event(
    event_id: str,
    loss: float,
    *,
    trial_id: int = 1,
    event_time: float = 1.0,
    event_sequence: int = 1,
    **program_changes: object,
) -> CT4OccurrenceInput:
    base_program = program_at_loss(loss, **program_changes)
    basis_input = replace(
        base_program.ct2_result.loss_basis.basis_input,
        occurrence_id=event_id,
    )
    basis = replace(base_program.ct2_result.loss_basis, basis_input=basis_input)
    ct2_result = replace(base_program.ct2_result, loss_basis=basis)
    ct2_metadata = build_ct2_run_metadata(
        waterfall_input=InuringWaterfallInput(loss_basis=basis),
        source_version=base_program.ct2_metadata.source_version,
        engine_version=base_program.ct2_metadata.engine_version,
        schema_version=base_program.ct2_metadata.schema_version,
    )
    event_program = replace(
        base_program,
        ct2_result=ct2_result,
        ct2_metadata=ct2_metadata,
    )
    return CT4OccurrenceInput(
        annual_trial_id=trial_id,
        event_id=event_id,
        event_time=event_time,
        event_sequence=event_sequence,
        peril="hurricane",
        region="coastal",
        program_input=event_program,
        source_reference=f"catalogue:{event_id}",
        trace_reference=f"trace:{event_id}",
    )


def catalogue(*trials: CT4AnnualTrialInput):
    return simulation(
        trial_count=len(trials),
        trials=trials,
    )


def test_catalogue_application_preserves_empty_trials_and_denominator() -> None:
    request = catalogue(
        CT4AnnualTrialInput(1, "trial-1", (event("E1", 45_000_000.0),)),
        CT4AnnualTrialInput(2, "trial-2", ()),
        CT4AnnualTrialInput(3, "trial-3", ()),
    )

    result = apply_catalogue_simulation(request)

    assert tuple(item.annual_trial_id for item in result.annual_rows) == (1, 2, 3)
    assert result.simulation_input.trial_count == 3
    assert result.annual_rows[1].occurrence_rows == ()
    assert (
        result.annual_rows[1].subject_oep,
        result.annual_rows[1].recovery_oep_pre_annual_capacity,
        result.annual_rows[1].net_oep_pre_annual_capacity,
        result.annual_rows[1].subject_aep,
        result.annual_rows[1].recovery_aep_pre_annual_capacity,
        result.annual_rows[1].net_aep_pre_annual_capacity,
    ) == (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    assert result.annual_rows[1].common_oep_driver_event_id is None


def test_events_use_frozen_chronological_order_not_input_order() -> None:
    later = event("LATER", 45_000_000.0, event_time=20.0, event_sequence=1)
    earlier = event("EARLIER", 5_000_000.0, event_time=10.0, event_sequence=2)
    request = catalogue(CT4AnnualTrialInput(1, "trial-1", (later, earlier)))

    result = apply_catalogue_simulation(request)

    assert tuple(item.event_id for item in result.occurrence_rows) == ("EARLIER", "LATER")
    assert tuple(item.occurrence_sequence for item in result.occurrence_rows) == (1, 2)


def test_order_ties_are_resolved_by_sequence_then_event_id() -> None:
    events = (
        event("Z", 1.0, event_time=10.0, event_sequence=2),
        event("B", 1.0, event_time=10.0, event_sequence=1),
        event("A", 1.0, event_time=10.0, event_sequence=1),
    )
    result = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", events))
    )
    assert tuple(item.event_id for item in result.occurrence_rows) == ("A", "B", "Z")


def test_input_permutation_produces_identical_ledgers() -> None:
    first = event("E1", 5_000_000.0, event_time=1.0)
    second = event("E2", 45_000_000.0, event_time=2.0)
    forward = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", (first, second)))
    )
    reverse = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", (second, first)))
    )
    assert forward.occurrence_rows == reverse.occurrence_rows
    assert forward.annual_rows == reverse.annual_rows


def test_f17_f18_f20_annual_ledger_reconciles() -> None:
    request = catalogue(
        CT4AnnualTrialInput(
            1,
            "trial-1",
            (
                event("SMALL", 5_000_000.0, event_time=1.0),
                event("LARGE", 45_000_000.0, event_time=2.0),
            ),
        )
    )
    annual = apply_catalogue_simulation(request).annual_rows[0]

    assert (annual.subject_oep, annual.recovery_oep_pre_annual_capacity, annual.net_oep_pre_annual_capacity) == (
        45_000_000.0,
        35_000_000.0,
        10_000_000.0,
    )
    assert (annual.subject_aep, annual.recovery_aep_pre_annual_capacity, annual.net_aep_pre_annual_capacity) == (
        50_000_000.0,
        35_000_000.0,
        15_000_000.0,
    )
    assert annual.common_oep_driver_event_id == "LARGE"
    assert annual.reconciliation_passed is True


def test_oep_plateau_still_uses_largest_subject_as_common_driver() -> None:
    rows = (
        event("LOWER", 60_000_000.0, event_time=1.0),
        event("HIGHER", 80_000_000.0, event_time=2.0),
    )
    annual = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", rows))
    ).annual_rows[0]
    assert annual.recovery_oep_pre_annual_capacity == 50_000_000.0
    assert annual.common_oep_driver_event_id == "HIGHER"


def test_ledger_uses_exact_pre_annual_capacity_recovery_and_source_version() -> None:
    result = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", (event("E1", 45_000_000.0),)))
    )
    row = result.occurrence_rows[0]
    assert row.gross_contractual_recovery_pre_annual_capacity == 35_000_000.0
    assert row.assessment.metadata.source_version == result.simulation_input.source_version
    assert row.source_event_ids == ("E1",)
    assert row.elected_candidate_id is None


def test_preflight_reports_every_blocked_event_before_application() -> None:
    overlapping = (
        layer("L1", attachment=0.0, occurrence_limit=20.0),
        layer("L2", attachment=10.0, occurrence_limit=20.0),
    )
    blocked_1 = event("BLOCK-1", 25.0, layers=overlapping)
    blocked_2 = event("BLOCK-2", 25.0, event_time=2.0, layers=overlapping)
    request = catalogue(
        CT4AnnualTrialInput(1, "trial-1", (blocked_2, blocked_1)),
        CT4AnnualTrialInput(2, "trial-2", ()),
    )

    issues = catalogue_preflight_issues(request)
    assert tuple(item.event_id for item in issues) == ("BLOCK-1", "BLOCK-2")
    assert all(item.code is PreflightIssueCode.BLOCKED_PROGRAM_GEOMETRY for item in issues)
    assert all("uncoordinated_overlap" in item.message for item in issues)
    with pytest.raises(CT4PreflightError) as error:
        apply_catalogue_simulation(request)
    assert error.value.issues == issues


def test_eligible_priority_overlap_passes_preflight() -> None:
    overlapping = (
        layer("L1", attachment=0.0, occurrence_limit=20.0),
        layer("L2", attachment=10.0, occurrence_limit=20.0),
    )
    eligible = event(
        "E1",
        25.0,
        layers=overlapping,
        overlap_coordination=OverlapCoordination.PRIORITY,
        priority_order=("L1", "L2"),
    )
    request = catalogue(CT4AnnualTrialInput(1, "trial-1", (eligible,)))
    assert catalogue_preflight_issues(request) == ()
    assert apply_catalogue_simulation(request).occurrence_rows[0].subject_loss == 25.0


def test_catalogue_runner_rejects_hours_mode_with_structured_issue() -> None:
    request = simulation(
        trial_count=1,
        trials=(CT4AnnualTrialInput(1, "hours", ()),),
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        hours_clause_scenario=hours_scenario(),
    )
    issues = catalogue_preflight_issues(request)
    assert len(issues) == 1
    assert issues[0].code is PreflightIssueCode.UNSUPPORTED_OCCURRENCE_MODE
    with pytest.raises(CT4PreflightError):
        apply_catalogue_simulation(request)


def test_preflight_requires_canonical_simulation_input() -> None:
    with pytest.raises(TypeError, match="CT4SimulationInput"):
        catalogue_preflight_issues({})  # type: ignore[arg-type]


def test_catalogue_result_is_immutable_and_flattened() -> None:
    result = apply_catalogue_simulation(
        catalogue(CT4AnnualTrialInput(1, "trial-1", (event("E1", 1.0),)))
    )
    assert isinstance(result, CT4CatalogueResult)
    assert result.occurrence_rows == result.annual_rows[0].occurrence_rows
    with pytest.raises(FrozenInstanceError):
        result.preflight_passed = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="ordered annual-ledger"):
        replace(result, occurrence_rows=())
