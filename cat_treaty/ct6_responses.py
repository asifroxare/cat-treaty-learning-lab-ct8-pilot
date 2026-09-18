"""Authoritative CT6 success-response projection without actuarial calculation."""

from dataclasses import fields, is_dataclass
from enum import Enum

from cat_treaty.ct2_metadata import CT2_ENGINE_VERSION, CT2_SCHEMA_VERSION
from cat_treaty.ct3_metadata import CT3_ENGINE_VERSION, CT3_SCHEMA_VERSION
from cat_treaty.ct4_metadata import CT4_ENGINE_VERSION, CT4_SCHEMA_VERSION
from cat_treaty.ct4_models import HoursClauseResult
from cat_treaty.ct5_metadata import CT5_ENGINE_VERSION, CT5_SCHEMA_VERSION
from cat_treaty.ct6_hours import CT6HoursRunResult
from cat_treaty.ct6_models import (
    CT6ApiResponseInfo,
    CT6CandidateSetResponse,
    CT6CandidateWindowResponse,
    CT6IdentityResponse,
    CT6LearningFactResponse,
    CT6LearningResponse,
    CT6PostCapacityResponse,
    CT6PreCapacityResponse,
    CT6ReconciliationResponse,
    CT6RequestSummaryResponse,
    CT6SuccessResponse,
    CT6VersionsResponse,
    CT6WarningResponse,
    PostCapacityAnnualResponse,
    PostCapacityLayerAnnualResponse,
    PostCapacityLayerEventResponse,
    PostCapacityOccurrenceResponse,
    PreCapacityAnnualResponse,
    PreCapacityOccurrenceResponse,
    ResponseDetail,
    RunMode,
)
from cat_treaty.ct6_orchestration import CT6CatalogueRunResult


def project_catalogue_success(
    result: CT6CatalogueRunResult,
    *,
    request_id: str,
) -> CT6SuccessResponse:
    if not isinstance(result, CT6CatalogueRunResult):
        raise TypeError("result must be CT6CatalogueRunResult")
    return _project(result, request_id=request_id, run_mode=RunMode.CATALOGUE)


def project_hours_success(
    result: CT6HoursRunResult,
    *,
    request_id: str,
) -> CT6SuccessResponse:
    if not isinstance(result, CT6HoursRunResult):
        raise TypeError("result must be CT6HoursRunResult")
    return _project(result, request_id=request_id, run_mode=RunMode.HOURS_CLAUSE)


def _project(result, *, request_id: str, run_mode: RunMode) -> CT6SuccessResponse:
    request = result.request
    detail = request.response_detail
    ct4_rows = (
        result.ct4_result.occurrence_rows
        if run_mode is RunMode.CATALOGUE
        else result.ct4_result.selected_occurrence_rows
    )
    ct4_annual = (
        result.ct4_result.annual_rows
        if run_mode is RunMode.CATALOGUE
        else (result.ct4_result.annual_row,)
    )
    assert all(row is not None for row in ct4_annual)
    full = detail is ResponseDetail.FULL
    pre_occurrences = tuple(_pre_occurrence(row) for row in ct4_rows) if full else None
    post_occurrences = (
        tuple(_post_occurrence(row) for row in result.ct5_result.occurrence_rows)
        if full else None
    )
    candidate_windows, candidate_sets, selected_id, valid_ids, election_method = (
        _election_projection(result.ct4_result)
        if isinstance(result.ct4_result, HoursClauseResult)
        else ((), (), None, (), None)
    )
    currency = _currency(result)
    simulation_id = result.ct4_identity.simulation_id
    return CT6SuccessResponse(
        api=CT6ApiResponseInfo(
            request_id=request_id,
            client_request_id=request.client_request_id,
            run_mode=run_mode,
        ),
        request=CT6RequestSummaryResponse(
            simulation_id=simulation_id,
            reporting_currency=currency,
            trial_count=len(ct4_annual),
            occurrence_count=len(ct4_rows),
            program_id=result.ct5_result.treaty_terms.program_id,
            layer_ids=tuple(item.layer_id for item in result.ct5_result.treaty_terms.layer_terms),
            response_detail=detail,
        ),
        versions=CT6VersionsResponse(
            ct2_engine_version=CT2_ENGINE_VERSION,
            ct2_schema_version=CT2_SCHEMA_VERSION,
            ct3_engine_version=CT3_ENGINE_VERSION,
            ct3_schema_version=CT3_SCHEMA_VERSION,
            ct4_engine_version=CT4_ENGINE_VERSION,
            ct4_schema_version=CT4_SCHEMA_VERSION,
            ct5_engine_version=CT5_ENGINE_VERSION,
            ct5_schema_version=CT5_SCHEMA_VERSION,
        ),
        identity=CT6IdentityResponse(
            simulation_id=simulation_id,
            ct4_input_hash=result.ct4_identity.input_hash,
            ct4_result_hash=result.ct4_identity.result_hash,
            ct5_input_hash=result.ct5_identity.input_hash,
            ct5_result_hash=result.ct5_identity.result_hash,
        ),
        pre_capacity=CT6PreCapacityResponse(
            occurrence_rows=pre_occurrences,
            annual_rows=tuple(_pre_annual(row) for row in ct4_annual),
            tail_analytics=_analytics_payload(result.ct4_tail_analytics, full=full),
            frequency_analytics=_normalized(result.ct4_frequency_analytics),
            candidate_windows=candidate_windows,
            candidate_sets=candidate_sets,
            selected_candidate_set_id=selected_id,
            valid_candidate_set_ids=valid_ids,
            selected_election_method=election_method,
        ),
        post_capacity=CT6PostCapacityResponse(
            occurrence_rows=post_occurrences,
            annual_rows=tuple(_post_annual(row) for row in result.ct5_result.annual_rows),
            analytics=_analytics_payload(result.ct5_analytics, full=full),
        ),
        learning=CT6LearningResponse(
            facts=_learning_facts(result),
            reconciliations=_reconciliations(result),
        ),
        warnings=_warnings(result),
    )


def _pre_occurrence(row) -> PreCapacityOccurrenceResponse:
    checks = row.assessment.program_result.reconciliation_checks
    return PreCapacityOccurrenceResponse(
        annual_trial_id=row.annual_trial_id,
        occurrence_sequence=row.occurrence_sequence,
        event_id=row.event_id,
        subject_loss=row.subject_loss,
        gross_contractual_recovery_pre_annual_capacity=row.gross_contractual_recovery_pre_annual_capacity,
        insurer_net_loss_pre_annual_capacity=row.insurer_net_loss_pre_annual_capacity,
        reconciliation_passed=all(item.passed for item in checks),
    )


def _pre_annual(row) -> PreCapacityAnnualResponse:
    return PreCapacityAnnualResponse(
        annual_trial_id=row.annual_trial_id,
        subject_loss=row.subject_aep,
        gross_contractual_recovery_pre_annual_capacity=row.recovery_aep_pre_annual_capacity,
        insurer_net_loss_pre_annual_capacity=row.net_aep_pre_annual_capacity,
        maximum_occurrence_recovery_pre_annual_capacity=row.recovery_oep_pre_annual_capacity,
        reconciliation_passed=row.reconciliation_passed,
    )


def _post_occurrence(row) -> PostCapacityOccurrenceResponse:
    return PostCapacityOccurrenceResponse(
        annual_trial_id=row.annual_trial_id,
        occurrence_sequence=row.occurrence_sequence,
        event_id=row.event_id,
        subject_loss=row.subject_loss,
        gross_contractual_recovery_pre_annual_capacity=row.gross_contractual_recovery_pre_annual_capacity,
        gross_contractual_recovery=row.gross_contractual_recovery,
        capacity_constrained_recovery_shortfall=row.capacity_constrained_recovery_shortfall,
        insurer_net_subject_loss=row.insurer_net_subject_loss,
        reinstatement_premium_payable=row.reinstatement_premium_payable,
        net_cash_settlement=row.net_cash_settlement,
        reconciliation_passed=row.reconciliation_passed,
        layer_event_rows=tuple(
            PostCapacityLayerEventResponse(
                annual_trial_id=item.annual_trial_id,
                occurrence_sequence=item.occurrence_sequence,
                event_id=item.event_id,
                layer_id=item.layer_id,
                pre_annual_capacity_recovery=item.pre_annual_capacity_recovery,
                active_capacity_before=item.active_capacity_before,
                gross_contractual_recovery=item.gross_contractual_recovery,
                capacity_constrained_recovery_shortfall=item.capacity_constrained_recovery_shortfall,
                active_capacity_after_recovery=item.active_capacity_after_recovery,
                amount_reinstated=item.amount_reinstated,
                active_capacity_for_next_event=item.active_capacity_for_next_event,
                reinstatement_premium_payable=item.reinstatement_premium_payable,
            )
            for item in row.layer_rows
        ),
    )


def _post_annual(row) -> PostCapacityAnnualResponse:
    return PostCapacityAnnualResponse(
        annual_trial_id=row.annual_trial_id,
        subject_loss=row.subject_loss,
        gross_contractual_recovery=row.gross_contractual_recovery,
        capacity_constrained_recovery_shortfall=row.capacity_constrained_recovery_shortfall,
        insurer_net_subject_loss=row.insurer_net_subject_loss,
        reinstatement_premium_payable=row.reinstatement_premium_payable,
        net_cash_settlement=row.net_cash_settlement,
        maximum_occurrence_recovery=row.maximum_occurrence_recovery,
        reconciliation_passed=row.reconciliation_passed,
        layer_summaries=tuple(
            PostCapacityLayerAnnualResponse(
                annual_trial_id=item.annual_trial_id,
                layer_id=item.layer_id,
                initial_capacity=item.initial_capacity,
                initial_reinstatement_reserve=item.initial_reinstatement_reserve,
                total_recovery=item.total_recovery,
                total_reinstated=item.total_reinstated,
                final_active_capacity=item.final_active_capacity,
                final_reinstatement_reserve=item.final_reinstatement_reserve,
                realized_capacity_utilization=item.realized_capacity_utilization,
                realized_capacity_utilization_status=item.realized_capacity_utilization_status.value,
                reinstatement_reserve_utilization=item.reinstatement_reserve_utilization,
                reinstatement_reserve_utilization_status=item.reinstatement_reserve_utilization_status.value,
            )
            for item in row.layer_summaries
        ),
    )


def _election_projection(result: HoursClauseResult):
    windows = tuple(
        CT6CandidateWindowResponse(
            candidate_id=item.candidate_id,
            start=item.start,
            end=item.end,
            component_ids=item.component_ids,
            subject_loss=item.subject_loss,
            admissibility=item.admissibility.value,
            exclusion_codes=tuple(code.value for code in item.exclusion_codes),
            exclusion_reasons=item.exclusion_reasons,
            affected_ids=item.affected_ids,
            rule_reference=item.rule_reference,
        )
        for item in result.candidate_windows
    )
    sets = tuple(
        CT6CandidateSetResponse(
            candidate_set_id=item.candidate_set_id,
            window_ids=item.window_ids,
            total_subject_loss=item.total_subject_loss,
            total_contractual_recovery=item.total_contractual_recovery,
            admissibility=item.admissibility.value,
            exclusion_codes=tuple(code.value for code in item.exclusion_codes),
            exclusion_reasons=item.exclusion_reasons,
            affected_ids=item.affected_ids,
            rule_reference=item.rule_reference,
        )
        for item in result.candidate_sets
    )
    return (
        windows,
        sets,
        result.selected_candidate_set_id,
        result.valid_candidate_set_ids,
        result.selected_election_method.value,
    )


def _learning_facts(result) -> tuple[CT6LearningFactResponse, ...]:
    facts: list[CT6LearningFactResponse] = []
    ct4_rows = (
        result.ct4_result.occurrence_rows
        if hasattr(result.ct4_result, "occurrence_rows")
        else result.ct4_result.selected_occurrence_rows
    )
    for row in ct4_rows:
        assessment = row.assessment
        for item in assessment.program_input.ct2_result.explanation_facts:
            facts.append(_fact("loss_stage", item))
        for item in assessment.program_result.explanation_facts:
            facts.append(_fact("occurrence_program", item))
    for row in result.ct5_result.occurrence_rows:
        for layer in row.layer_rows:
            facts.extend((
                CT6LearningFactResponse(
                    category="annual_capacity",
                    metric_name=f"{row.event_id}:{layer.layer_id}:gross_contractual_recovery",
                    value=layer.gross_contractual_recovery,
                    meaning="Recovery after the layer's available annual capacity.",
                    driver_statement="The event used active capacity available before reinstatement for later events.",
                    trace_references=layer.trace_references,
                ),
                CT6LearningFactResponse(
                    category="reinstatement",
                    metric_name=f"{row.event_id}:{layer.layer_id}:amount_reinstated",
                    value=layer.amount_reinstated,
                    meaning="Capacity restored only after this occurrence's recovery was fixed.",
                    driver_statement="Restored capacity is available to the next ordered event, not the triggering event.",
                    trace_references=layer.trace_references,
                ),
            ))
        facts.append(CT6LearningFactResponse(
            category="settlement",
            metric_name=f"{row.event_id}:net_cash_settlement",
            value=row.net_cash_settlement,
            meaning="Cash presentation after applying the declared settlement mode.",
            driver_statement="Gross contractual recovery and reinstatement premium remain separately disclosed.",
            trace_references=row.trace_references,
        ))
    return tuple(facts)


def _fact(category: str, item) -> CT6LearningFactResponse:
    return CT6LearningFactResponse(
        category=category,
        metric_name=item.metric_name,
        value=item.value,
        meaning=item.meaning,
        driver_statement=item.driver_statement,
        trace_references=(item.trace_reference,),
    )


def _reconciliations(result) -> tuple[CT6ReconciliationResponse, ...]:
    evidence: list[CT6ReconciliationResponse] = []
    ct4_rows = (
        result.ct4_result.occurrence_rows
        if hasattr(result.ct4_result, "occurrence_rows")
        else result.ct4_result.selected_occurrence_rows
    )
    for row in ct4_rows:
        for check in row.assessment.program_input.ct2_result.reconciliation_checks:
            evidence.append(CT6ReconciliationResponse(
                scope="ct2", identifier=f"{row.event_id}:{check.check_id}",
                passed=check.passed, formula_references=(check.formula_reference,),
            ))
        for check in row.assessment.program_result.reconciliation_checks:
            evidence.append(CT6ReconciliationResponse(
                scope="ct3", identifier=f"{row.event_id}:{check.check_id}",
                passed=check.passed, formula_references=(check.formula_reference,),
            ))
    ct4_annual = (
        result.ct4_result.annual_rows
        if hasattr(result.ct4_result, "annual_rows")
        else (result.ct4_result.annual_row,)
    )
    for row in ct4_annual:
        evidence.append(CT6ReconciliationResponse(
            scope="ct4_annual", identifier=f"trial:{row.annual_trial_id}",
            passed=row.reconciliation_passed, formula_references=("F20",),
        ))
    for row in result.ct5_result.occurrence_rows:
        evidence.append(CT6ReconciliationResponse(
            scope="ct5_occurrence", identifier=row.event_id,
            passed=row.reconciliation_passed, formula_references=("F31", "F32", "F37"),
        ))
    for row in result.ct5_result.annual_rows:
        evidence.append(CT6ReconciliationResponse(
            scope="ct5_annual", identifier=f"trial:{row.annual_trial_id}",
            passed=row.reconciliation_passed, formula_references=("F33", "F34", "F35", "F36", "F37"),
        ))
    return tuple(evidence)


def _warnings(result) -> tuple[CT6WarningResponse, ...]:
    warnings: list[CT6WarningResponse] = []
    for source, analytics in (("ct4", result.ct4_tail_analytics), ("ct5", result.ct5_analytics)):
        for item in _walk(analytics):
            if type(item).__name__ == "TailWarning":
                warnings.append(CT6WarningResponse(
                    code=item.code.value,
                    message=item.message,
                    source=source,
                    return_period=item.return_period,
                ))
    ct4_rows = (
        result.ct4_result.occurrence_rows
        if hasattr(result.ct4_result, "occurrence_rows")
        else result.ct4_result.selected_occurrence_rows
    )
    for row in ct4_rows:
        for message in row.assessment.geometry.warnings:
            warnings.append(CT6WarningResponse(
                code="program_geometry_warning", message=message, source="ct3"
            ))
    unique = {}
    for item in warnings:
        key = (item.code, item.message, item.source, item.return_period)
        unique.setdefault(key, item)
    return tuple(unique.values())


def _walk(value):
    yield value
    if is_dataclass(value):
        for field in fields(value):
            yield from _walk(getattr(value, field.name))
    elif isinstance(value, (tuple, list, dict)):
        items = value.values() if isinstance(value, dict) else value
        for item in items:
            yield from _walk(item)


def _analytics_payload(value, *, full: bool) -> dict[str, object]:
    payload = _normalized(value)
    if full:
        return payload
    return _omit_presentation_arrays(payload)


def _omit_presentation_arrays(value):
    omitted = {"oep_sample", "aep_sample", "oep_curve", "aep_curve"}
    if isinstance(value, dict):
        return {
            key: _omit_presentation_arrays(item)
            for key, item in value.items()
            if key not in omitted
        }
    if isinstance(value, list):
        return [_omit_presentation_arrays(item) for item in value]
    return value


def _normalized(value):
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _normalized(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_normalized(item) for item in value]
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalized(item) for key, item in value.items()}
    return value


def _currency(result) -> str:
    terms = result.ct5_result.treaty_terms
    ct4_rows = (
        result.ct4_result.occurrence_rows
        if hasattr(result.ct4_result, "occurrence_rows")
        else result.ct4_result.selected_occurrence_rows
    )
    if ct4_rows:
        return ct4_rows[0].assessment.program_input.layers[0].currency
    layer_id = terms.layer_terms[0].layer_id
    program_layers = result.request.input.program.layers
    return next(item.currency for item in program_layers if item.layer_id == layer_id)
