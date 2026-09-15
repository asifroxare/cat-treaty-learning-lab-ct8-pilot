"""CT4 catalogue-defined occurrence application and F17-F20 ledgers."""

from collections.abc import Iterable
import math

from cat_treaty.ct3_models import ProgramEligibilityStatus
from cat_treaty.ct4_models import (
    CT4AnnualLedgerRow,
    CT4CatalogueResult,
    CT4OccurrenceInput,
    CT4OccurrenceLedgerRow,
    CT4PreflightIssue,
    CT4SimulationInput,
    OccurrenceDefinitionMode,
    PreflightIssueCode,
)
from cat_treaty.geometry import analyze_program_geometry
from cat_treaty.program import evaluate_cat_xl_program


class CT4PreflightError(ValueError):
    """Raised with immutable evidence when a run fails before calculation."""

    def __init__(self, issues: tuple[CT4PreflightIssue, ...]) -> None:
        if not issues:
            raise ValueError("CT4PreflightError requires at least one issue")
        self.issues = issues
        super().__init__(
            "CT4 catalogue preflight failed: "
            + "; ".join(item.message for item in issues)
        )


def catalogue_preflight_issues(
    simulation_input: CT4SimulationInput,
) -> tuple[CT4PreflightIssue, ...]:
    """Return all deterministic catalogue-level blockers without calculating loss."""

    if not isinstance(simulation_input, CT4SimulationInput):
        raise TypeError("simulation_input must be CT4SimulationInput")
    if simulation_input.occurrence_definition_mode is not OccurrenceDefinitionMode.CATALOGUE_DEFINED:
        return (
            CT4PreflightIssue(
                code=PreflightIssueCode.UNSUPPORTED_OCCURRENCE_MODE,
                annual_trial_id=None,
                event_id=None,
                message="catalogue application supports catalogue_defined mode only",
                trace_reference="CT4-section-7",
            ),
        )

    issues: list[CT4PreflightIssue] = []
    for trial in simulation_input.trials:
        for occurrence in _ordered_occurrences(trial.occurrences):
            geometry = analyze_program_geometry(occurrence.program_input)
            if geometry.eligibility_status is ProgramEligibilityStatus.BLOCKED:
                codes = ", ".join(item.code.value for item in geometry.blocking_issues)
                issues.append(
                    CT4PreflightIssue(
                        code=PreflightIssueCode.BLOCKED_PROGRAM_GEOMETRY,
                        annual_trial_id=trial.annual_trial_id,
                        event_id=occurrence.event_id,
                        message=f"event {occurrence.event_id} has blocked CT3 geometry: {codes}",
                        trace_reference=occurrence.trace_reference,
                    )
                )
    return tuple(issues)


def apply_catalogue_simulation(
    simulation_input: CT4SimulationInput,
) -> CT4CatalogueResult:
    """Preflight and apply one fixed CT3 program to every catalogue occurrence."""

    issues = catalogue_preflight_issues(simulation_input)
    if issues:
        raise CT4PreflightError(issues)

    annual_rows: list[CT4AnnualLedgerRow] = []
    occurrence_rows: list[CT4OccurrenceLedgerRow] = []
    for trial in simulation_input.trials:
        rows = tuple(
            _evaluate_occurrence(
                occurrence,
                occurrence_sequence=sequence,
                source_version=simulation_input.source_version,
            )
            for sequence, occurrence in enumerate(
                _ordered_occurrences(trial.occurrences),
                start=1,
            )
        )
        annual = _annual_ledger(trial.annual_trial_id, rows)
        annual_rows.append(annual)
        occurrence_rows.extend(rows)

    return CT4CatalogueResult(
        simulation_input=simulation_input,
        occurrence_rows=tuple(occurrence_rows),
        annual_rows=tuple(annual_rows),
        preflight_passed=True,
    )


def _ordered_occurrences(
    occurrences: Iterable[CT4OccurrenceInput],
) -> tuple[CT4OccurrenceInput, ...]:
    return tuple(
        sorted(
            occurrences,
            key=lambda item: (item.event_time, item.event_sequence, item.event_id),
        )
    )


def _evaluate_occurrence(
    occurrence: CT4OccurrenceInput,
    *,
    occurrence_sequence: int,
    source_version: str,
) -> CT4OccurrenceLedgerRow:
    assessment = evaluate_cat_xl_program(
        occurrence.program_input,
        source_version=source_version,
    )
    if assessment.program_result is None:
        # Preflight used the same geometry function, so this is a defensive gate.
        raise RuntimeError("CT3 eligibility changed after CT4 preflight")
    result = assessment.program_result
    return CT4OccurrenceLedgerRow(
        annual_trial_id=occurrence.annual_trial_id,
        occurrence_sequence=occurrence_sequence,
        event_id=occurrence.event_id,
        source_event_ids=(occurrence.event_id,),
        occurrence_definition_mode=OccurrenceDefinitionMode.CATALOGUE_DEFINED,
        elected_candidate_id=None,
        assessment=assessment,
        subject_loss=float(occurrence.program_input.ct2_result.cat_xl_subject_loss),
        gross_contractual_recovery_pre_annual_capacity=float(
            result.total_gross_contractual_recovery
        ),
        insurer_net_loss_pre_annual_capacity=float(result.insurer_net_loss),
        trace_references=(occurrence.trace_reference, "F17", "F18", "F20"),
    )


def _annual_ledger(
    annual_trial_id: int,
    rows: tuple[CT4OccurrenceLedgerRow, ...],
) -> CT4AnnualLedgerRow:
    subject_oep = max((item.subject_loss for item in rows), default=0.0)
    recovery_oep = max(
        (item.gross_contractual_recovery_pre_annual_capacity for item in rows),
        default=0.0,
    )
    net_oep = max(
        (item.insurer_net_loss_pre_annual_capacity for item in rows),
        default=0.0,
    )
    subject_aep = math.fsum(item.subject_loss for item in rows)
    recovery_aep = math.fsum(
        item.gross_contractual_recovery_pre_annual_capacity for item in rows
    )
    net_aep = math.fsum(item.insurer_net_loss_pre_annual_capacity for item in rows)
    driver = (
        min(rows, key=lambda item: (-item.subject_loss, item.occurrence_sequence, item.event_id))
        if rows
        else None
    )
    tolerance = dict(rel_tol=1e-12, abs_tol=1e-6)
    return CT4AnnualLedgerRow(
        annual_trial_id=annual_trial_id,
        occurrence_rows=rows,
        subject_oep=subject_oep,
        recovery_oep_pre_annual_capacity=recovery_oep,
        net_oep_pre_annual_capacity=net_oep,
        subject_aep=subject_aep,
        recovery_aep_pre_annual_capacity=recovery_aep,
        net_aep_pre_annual_capacity=net_aep,
        common_oep_driver_event_id=driver.event_id if driver else None,
        reconciliation_passed=math.isclose(
            subject_aep,
            recovery_aep + net_aep,
            **tolerance,
        ),
    )
