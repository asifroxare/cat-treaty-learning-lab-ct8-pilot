"""Bounded CT4 hours-clause candidate generation, validity and election."""

from dataclasses import replace
import itertools
import math

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import (
    InuringCompletionStatus,
    InuringWaterfallInput,
    InuringWaterfallResult,
    LossBasisInput,
    LossBasisResult,
    ReconciliationCheck,
)
from cat_treaty.ct3_models import ProgramEligibilityStatus
from cat_treaty.ct4_models import (
    CandidateAdmissibility,
    CT4OccurrenceLedgerRow,
    HoursCandidateSet,
    HoursCandidateWindow,
    HoursClauseResult,
    HoursClauseScenario,
    HoursElectionIssue,
    HoursElectionIssueCode,
    HoursElectionMethod,
    HoursElectionStatus,
    HoursExclusionCode,
    HoursLossComponent,
    OccurrenceDefinitionMode,
)
from cat_treaty.geometry import analyze_program_geometry
from cat_treaty.program import evaluate_cat_xl_program
from cat_treaty.simulation import build_annual_ledger


def evaluate_hours_clause_scenario(
    scenario: HoursClauseScenario,
    *,
    source_version: str,
) -> HoursClauseResult:
    """Generate all candidates, determine validity, then apply authorized election."""

    if not isinstance(scenario, HoursClauseScenario):
        raise TypeError("scenario must be HoursClauseScenario")
    if not isinstance(source_version, str) or not source_version.strip():
        raise ValueError("source_version must be a non-empty string")
    geometry = analyze_program_geometry(scenario.program_terms_source)
    if geometry.eligibility_status is ProgramEligibilityStatus.BLOCKED:
        codes = tuple(item.code.value for item in geometry.blocking_issues)
        return _blocked(
            scenario,
            (),
            (),
            HoursElectionIssue(
                HoursElectionIssueCode.PROGRAM_GEOMETRY_BLOCKED,
                None,
                "hours-clause program geometry is blocked: " + ", ".join(codes),
                codes,
                "CT3-geometry",
            ),
        )

    windows = generate_candidate_windows(scenario)
    assessments = {
        window.candidate_id: _assessment_for_window(scenario, window, source_version)
        for window in windows
        if window.admissibility is CandidateAdmissibility.VALID
    }
    candidate_sets = generate_candidate_sets(windows, assessments)
    valid = tuple(
        item for item in candidate_sets
        if item.admissibility is CandidateAdmissibility.VALID
    )
    if not valid:
        return _blocked(
            scenario,
            windows,
            candidate_sets,
            HoursElectionIssue(
                HoursElectionIssueCode.NO_VALID_CANDIDATE_SET,
                None,
                "no valid non-overlapping candidate set is available for election",
                tuple(item.candidate_id for item in windows),
                "CT4-section-8",
            ),
        )

    selected = _elect(scenario, valid, windows)
    if selected is None:
        manual_id = scenario.terms.manual_candidate_set_id
        return _blocked(
            scenario,
            windows,
            candidate_sets,
            HoursElectionIssue(
                HoursElectionIssueCode.MANUAL_SELECTION_INVALID,
                manual_id,
                "manual election must identify one complete valid generated candidate set",
                (manual_id,) if manual_id else (),
                "CT4-section-9",
            ),
        )

    by_window = {item.candidate_id: item for item in windows}
    rows = tuple(
        _ledger_row(
            scenario=scenario,
            window=by_window[window_id],
            assessment=assessments[window_id],
            sequence=sequence,
            selected_set_id=selected.candidate_set_id,
        )
        for sequence, window_id in enumerate(
            sorted(
                selected.window_ids,
                key=lambda item: _window_key(by_window[item]),
            ),
            start=1,
        )
    )
    return HoursClauseResult(
        scenario=scenario,
        candidate_windows=windows,
        candidate_sets=candidate_sets,
        election_status=HoursElectionStatus.SELECTED,
        selected_election_method=scenario.terms.selected_election_method,
        selected_candidate_set_id=selected.candidate_set_id,
        valid_candidate_set_ids=tuple(item.candidate_set_id for item in valid),
        selected_occurrence_rows=rows,
        annual_row=build_annual_ledger(1, rows),
        election_issues=(),
        tie_break_facts=_tie_break_facts(scenario.terms.selected_election_method),
    )


def generate_candidate_windows(
    scenario: HoursClauseScenario,
) -> tuple[HoursCandidateWindow, ...]:
    """Generate one inclusive-start/exclusive-end window per component anchor."""

    if not isinstance(scenario, HoursClauseScenario):
        raise TypeError("scenario must be HoursClauseScenario")
    ordered = tuple(sorted(scenario.components, key=lambda item: (item.timestamp, item.component_id)))
    result: list[HoursCandidateWindow] = []
    for position, anchor in enumerate(ordered, start=1):
        start = float(anchor.timestamp)
        end = start + float(scenario.terms.hours_duration)
        members = tuple(
            item for item in ordered
            if start <= float(item.timestamp) < end
        )
        codes, reasons, affected = _window_exclusions(scenario, members)
        result.append(
            HoursCandidateWindow(
                candidate_id=f"W{position:03d}",
                start=start,
                end=end,
                component_ids=tuple(item.component_id for item in members),
                subject_loss=math.fsum(float(item.subject_loss) for item in members),
                admissibility=(
                    CandidateAdmissibility.EXCLUDED if codes else CandidateAdmissibility.VALID
                ),
                exclusion_codes=codes,
                exclusion_reasons=reasons,
                affected_ids=affected,
                rule_reference="CT4-section-8",
            )
        )
    return tuple(result)


def generate_candidate_sets(
    windows: tuple[HoursCandidateWindow, ...],
    assessments: dict[str, object],
) -> tuple[HoursCandidateSet, ...]:
    """Generate every non-empty subset; 12 windows bound the universe at 4,095."""

    if not isinstance(windows, tuple) or not all(isinstance(item, HoursCandidateWindow) for item in windows):
        raise TypeError("windows must contain HoursCandidateWindow values")
    if len(windows) > 12:
        raise ValueError("candidate windows are bounded at twelve")
    results: list[HoursCandidateSet] = []
    for mask in range(1, 1 << len(windows)):
        selected = tuple(windows[index] for index in range(len(windows)) if mask & (1 << index))
        codes: list[HoursExclusionCode] = []
        reasons: list[str] = []
        affected: list[str] = []
        for window in selected:
            for code, reason in zip(window.exclusion_codes, window.exclusion_reasons, strict=True):
                _append_exclusion(codes, reasons, code, reason)
            affected.extend(item for item in window.affected_ids if item not in affected)
        component_ids = tuple(component for window in selected for component in window.component_ids)
        if len(component_ids) != len(set(component_ids)):
            _append_exclusion(
                codes,
                reasons,
                HoursExclusionCode.DUPLICATE_COMPONENT,
                "A loss component appears in more than one elected window.",
            )
            affected.extend(
                item for item in component_ids
                if component_ids.count(item) > 1 and item not in affected
            )
        if _windows_overlap(selected):
            _append_exclusion(
                codes,
                reasons,
                HoursExclusionCode.OVERLAPPING_WINDOWS,
                "The proposed candidate set contains overlapping hours windows.",
            )
            affected.extend(
                item.candidate_id for item in selected
                if item.candidate_id not in affected
            )
        valid = not codes
        total_recovery = None
        if all(item.candidate_id in assessments for item in selected):
            total_recovery = math.fsum(
                assessments[item.candidate_id].program_result.total_gross_contractual_recovery  # type: ignore[union-attr]
                for item in selected
            )
        results.append(
            HoursCandidateSet(
                candidate_set_id=f"SET-{mask:03X}",
                window_ids=tuple(item.candidate_id for item in selected),
                total_subject_loss=math.fsum(item.subject_loss for item in selected),
                total_contractual_recovery=total_recovery,
                admissibility=CandidateAdmissibility.VALID if valid else CandidateAdmissibility.EXCLUDED,
                exclusion_codes=tuple(codes),
                exclusion_reasons=tuple(reasons),
                affected_ids=tuple(affected),
                rule_reference="CT4-section-8",
            )
        )
    return tuple(results)


def _window_exclusions(
    scenario: HoursClauseScenario,
    members: tuple[HoursLossComponent, ...],
) -> tuple[tuple[HoursExclusionCode, ...], tuple[str, ...], tuple[str, ...]]:
    codes: list[HoursExclusionCode] = []
    reasons: list[str] = []
    affected: list[str] = []
    terms = scenario.terms
    outside = tuple(
        item.component_id for item in members
        if not (terms.treaty_term_start <= item.timestamp < terms.treaty_term_end)
    )
    peril = tuple(item.component_id for item in members if item.peril not in terms.permitted_perils)
    region = tuple(item.component_id for item in members if item.region not in terms.permitted_regions)
    causes = {item.causal_event_id for item in members}
    causal = tuple(item.component_id for item in members) if terms.causal_link_required and len(causes) > 1 else ()
    for ids, code, reason in (
        (outside, HoursExclusionCode.OUTSIDE_TREATY_TERM, "Component lies outside the treaty term."),
        (peril, HoursExclusionCode.PERIL_OR_CAUSE_MISMATCH, "Component peril is not contractually permitted."),
        (region, HoursExclusionCode.GEOGRAPHIC_MISMATCH, "Component region is not contractually permitted."),
        (causal, HoursExclusionCode.CAUSAL_LINK_FAILURE, "Components do not satisfy the declared causal-link rule."),
    ):
        if ids:
            codes.append(code)
            reasons.append(reason)
            affected.extend(item for item in ids if item not in affected)
    return tuple(codes), tuple(reasons), tuple(affected)


def _assessment_for_window(scenario: HoursClauseScenario, window: HoursCandidateWindow, source_version: str):
    request = _program_for_subject(
        scenario,
        occurrence_id=f"{scenario.scenario_id}:{window.candidate_id}",
        subject_loss=window.subject_loss,
        source_version=source_version,
    )
    assessment = evaluate_cat_xl_program(request, source_version=source_version)
    if assessment.program_result is None:
        raise RuntimeError("eligible hours-clause geometry became blocked")
    return assessment


def _program_for_subject(
    scenario: HoursClauseScenario,
    *,
    occurrence_id: str,
    subject_loss: float,
    source_version: str,
):
    template = scenario.program_terms_source
    template_basis = template.ct2_result.loss_basis.basis_input
    basis_input = LossBasisInput(
        occurrence_id=occurrence_id,
        reporting_currency=template_basis.reporting_currency,
        source_stage_declaration="cat_xl_subject_loss_hours_clause_teaching",
        source_reference=scenario.source_reference,
        initial_insured_loss=subject_loss,
    )
    basis = LossBasisResult(basis_input, 0.0, 0.0, subject_loss, True)
    check = ReconciliationCheck("F09-hours", "F09", subject_loss, subject_loss, True)
    result = InuringWaterfallResult(
        loss_basis=basis,
        cover_results=(),
        total_inuring_recovery=0.0,
        cat_xl_subject_loss=subject_loss,
        completion_status=InuringCompletionStatus.COMPLETE_NO_INURING_COVERS,
        reconciliation_checks=(check,),
        explanation_facts=(),
    )
    waterfall_input = InuringWaterfallInput(loss_basis=basis)
    metadata = build_ct2_run_metadata(
        waterfall_input=waterfall_input,
        source_version=source_version,
        engine_version=template.ct2_metadata.engine_version,
        schema_version=template.ct2_metadata.schema_version,
    )
    return replace(template, ct2_result=result, ct2_metadata=metadata)


def _windows_overlap(windows: tuple[HoursCandidateWindow, ...]) -> bool:
    ordered = sorted(windows, key=_window_key)
    return any(left.end > right.start for left, right in itertools.pairwise(ordered))


def _append_exclusion(codes, reasons, code, reason) -> None:
    if code not in codes:
        codes.append(code)
        reasons.append(reason)


def _window_key(window: HoursCandidateWindow) -> tuple[float, float, str]:
    return (window.start, window.end, window.candidate_id)


def _set_key(candidate: HoursCandidateSet, by_window: dict[str, HoursCandidateWindow]):
    return tuple(_window_key(by_window[item]) for item in candidate.window_ids)


def _elect(scenario, valid, windows):
    method = scenario.terms.selected_election_method
    by_window = {item.candidate_id: item for item in windows}
    earliest = lambda item: _set_key(item, by_window)
    if method is HoursElectionMethod.MANUAL:
        return next(
            (item for item in valid if item.candidate_set_id == scenario.terms.manual_candidate_set_id),
            None,
        )
    if method is HoursElectionMethod.EARLIEST_VALID_WINDOW:
        return min(valid, key=earliest)
    if method is HoursElectionMethod.MAXIMUM_SUBJECT_LOSS:
        maximum = max(item.total_subject_loss for item in valid)
        return min((item for item in valid if item.total_subject_loss == maximum), key=earliest)
    maximum_recovery = max(float(item.total_contractual_recovery) for item in valid)
    recovery_ties = tuple(item for item in valid if item.total_contractual_recovery == maximum_recovery)
    maximum_subject = max(item.total_subject_loss for item in recovery_ties)
    return min((item for item in recovery_ties if item.total_subject_loss == maximum_subject), key=earliest)


def _ledger_row(*, scenario, window, assessment, sequence, selected_set_id):
    result = assessment.program_result
    return CT4OccurrenceLedgerRow(
        annual_trial_id=1,
        occurrence_sequence=sequence,
        event_id=assessment.program_input.ct2_result.loss_basis.basis_input.occurrence_id,
        source_event_ids=window.component_ids,
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        elected_candidate_id=selected_set_id,
        assessment=assessment,
        subject_loss=window.subject_loss,
        gross_contractual_recovery_pre_annual_capacity=result.total_gross_contractual_recovery,
        insurer_net_loss_pre_annual_capacity=result.insurer_net_loss,
        trace_references=(scenario.source_reference, window.rule_reference, "F17", "F18", "F20"),
    )


def _tie_break_facts(method: HoursElectionMethod) -> tuple[str, ...]:
    if method is HoursElectionMethod.EARLIEST_VALID_WINDOW:
        return ("Valid sets ordered by window start, end and candidate ID.",)
    if method is HoursElectionMethod.MAXIMUM_SUBJECT_LOSS:
        return ("Maximum valid subject loss selected; earliest valid set resolves ties.",)
    if method is HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY:
        return ("Maximum valid contractual recovery selected; subject loss then earliest valid set resolve ties.",)
    return ("Manual ID matched one complete valid generated candidate set.",)


def _blocked(scenario, windows, sets, issue):
    return HoursClauseResult(
        scenario=scenario,
        candidate_windows=windows,
        candidate_sets=sets,
        election_status=HoursElectionStatus.BLOCKED,
        selected_election_method=scenario.terms.selected_election_method,
        selected_candidate_set_id=None,
        valid_candidate_set_ids=tuple(
            item.candidate_set_id for item in sets
            if item.admissibility is CandidateAdmissibility.VALID
        ),
        selected_occurrence_rows=(),
        annual_row=None,
        election_issues=(issue,),
        tie_break_facts=(),
    )
