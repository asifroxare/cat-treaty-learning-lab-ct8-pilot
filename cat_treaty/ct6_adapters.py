"""Conversion-only CT6 wire-to-domain adapters.

This module constructs immutable domain inputs. It deliberately imports no
loss, recovery, capacity, premium, analytics, or hashing engine.
"""

from dataclasses import dataclass

from cat_treaty.ct2_models import InuringCoverInput, LossBasisInput, LossComponent
from cat_treaty.ct3_models import CatLayerInput
from cat_treaty.ct4_models import HoursClauseTerms, HoursLossComponent, NumericalToleranceProfile, TailConfiguration
from cat_treaty.ct5_models import CT5LayerTerms, CT5TreatyTerms, ReinstatementTranche
from cat_treaty.ct6_models import CatalogueRunRequest, HoursRunRequest, SourceOccurrenceDTO


@dataclass(frozen=True, slots=True)
class AdaptedSourceOccurrence:
    annual_trial_id: int
    event_id: str
    event_time: float
    event_sequence: int
    peril: str
    region: str
    source_reference: str
    trace_reference: str
    loss_basis: LossBasisInput
    inuring_covers: tuple[InuringCoverInput, ...]


@dataclass(frozen=True, slots=True)
class AdaptedAnnualTrial:
    annual_trial_id: int
    catalogue_source_id: str
    occurrences: tuple[AdaptedSourceOccurrence, ...]


@dataclass(frozen=True, slots=True)
class AdaptedCatalogueRequest:
    request: CatalogueRunRequest
    trials: tuple[AdaptedAnnualTrial, ...]
    layers: tuple[CatLayerInput, ...]
    treaty_terms: CT5TreatyTerms
    tail_configuration: TailConfiguration
    tolerance_profile: NumericalToleranceProfile


@dataclass(frozen=True, slots=True)
class AdaptedHoursRequest:
    request: HoursRunRequest
    components: tuple[HoursLossComponent, ...]
    terms: HoursClauseTerms
    program_source: AdaptedSourceOccurrence
    layers: tuple[CatLayerInput, ...]
    treaty_terms: CT5TreatyTerms
    tail_configuration: TailConfiguration
    tolerance_profile: NumericalToleranceProfile


def adapt_catalogue_request(request: CatalogueRunRequest) -> AdaptedCatalogueRequest:
    if not isinstance(request, CatalogueRunRequest):
        raise TypeError("request must be CatalogueRunRequest")
    return AdaptedCatalogueRequest(
        request=request,
        trials=tuple(
            AdaptedAnnualTrial(
                annual_trial_id=trial.annual_trial_id,
                catalogue_source_id=trial.catalogue_source_id,
                occurrences=tuple(adapt_source_occurrence(item) for item in trial.occurrences),
            )
            for trial in request.input.trials
        ),
        layers=_adapt_layers(request.input.program.layers),
        treaty_terms=_adapt_treaty_terms(request.input.treaty_terms),
        tail_configuration=_adapt_tail(request.input.simulation.tail_configuration),
        tolerance_profile=_adapt_tolerance(request.input.simulation.tolerance_profile),
    )


def adapt_hours_request(request: HoursRunRequest) -> AdaptedHoursRequest:
    if not isinstance(request, HoursRunRequest):
        raise TypeError("request must be HoursRunRequest")
    item = request.input
    return AdaptedHoursRequest(
        request=request,
        components=tuple(
            HoursLossComponent(
                component_id=value.component_id,
                subject_loss=value.subject_loss,
                timestamp=value.timestamp,
                peril=value.peril,
                region=value.region,
                causal_event_id=value.causal_event_id,
                source_reference=value.source_reference,
            )
            for value in item.components
        ),
        terms=HoursClauseTerms(
            treaty_term_start=item.terms.treaty_term_start,
            treaty_term_end=item.terms.treaty_term_end,
            hours_duration=item.terms.hours_duration,
            permitted_perils=item.terms.permitted_perils,
            permitted_regions=item.terms.permitted_regions,
            causal_link_required=item.terms.causal_link_required,
            authorized_election_methods=item.terms.authorized_election_methods,
            selected_election_method=item.terms.selected_election_method,
            manual_candidate_set_id=item.terms.manual_candidate_set_id,
            rule_reference=item.terms.rule_reference,
        ),
        program_source=adapt_source_occurrence(item.program_source),
        layers=_adapt_layers(item.program.layers),
        treaty_terms=_adapt_treaty_terms(item.treaty_terms),
        tail_configuration=_adapt_tail(item.tail_configuration),
        tolerance_profile=_adapt_tolerance(item.tolerance_profile),
    )


def adapt_source_occurrence(item: SourceOccurrenceDTO) -> AdaptedSourceOccurrence:
    if not isinstance(item, SourceOccurrenceDTO):
        raise TypeError("item must be SourceOccurrenceDTO")
    basis = item.loss_basis
    return AdaptedSourceOccurrence(
        annual_trial_id=item.annual_trial_id,
        event_id=item.event_id,
        event_time=item.event_time,
        event_sequence=item.event_sequence,
        peril=item.peril,
        region=item.region,
        source_reference=item.source_reference,
        trace_reference=item.trace_reference,
        loss_basis=LossBasisInput(
            occurrence_id=basis.occurrence_id,
            reporting_currency=basis.reporting_currency,
            source_stage_declaration=basis.source_stage_declaration,
            source_reference=basis.source_reference,
            initial_insured_loss=basis.initial_insured_loss,
            components=tuple(
                LossComponent(
                    component_id=value.component_id,
                    category=value.category,
                    label=value.label,
                    amount=value.amount,
                    included=value.included,
                    source_reference=value.source_reference,
                    rule_reference=value.rule_reference,
                )
                for value in basis.components
            ),
            ground_up_loss=basis.ground_up_loss,
        ),
        inuring_covers=tuple(
            InuringCoverInput(**value.model_dump()) for value in item.inuring_covers
        ),
    )


def _adapt_layers(values) -> tuple[CatLayerInput, ...]:
    return tuple(CatLayerInput(**item.model_dump()) for item in values)


def _adapt_treaty_terms(value) -> CT5TreatyTerms:
    return CT5TreatyTerms(
        program_id=value.program_id,
        layer_terms=tuple(
            CT5LayerTerms(
                layer_id=item.layer_id,
                original_layer_premium=item.original_layer_premium,
                premium_basis_declaration=item.premium_basis_declaration,
                reinstatement_tranches=tuple(
                    ReinstatementTranche(**tranche.model_dump())
                    for tranche in item.reinstatement_tranches
                ),
                treaty_term_start=item.treaty_term_start,
                treaty_term_end=item.treaty_term_end,
                settlement_mode=item.settlement_mode,
                source_reference=item.source_reference,
                rule_reference=item.rule_reference,
                capacity_basis=item.capacity_basis,
            )
            for item in value.layer_terms
        ),
        source_reference=value.source_reference,
        rule_reference=value.rule_reference,
    )


def _adapt_tail(value) -> TailConfiguration:
    return TailConfiguration(
        probability_levels=value.probability_levels,
        tvar_levels=value.tvar_levels,
        return_periods=value.return_periods,
    )


def _adapt_tolerance(value) -> NumericalToleranceProfile:
    return NumericalToleranceProfile(
        relative_tolerance=value.relative_tolerance,
        absolute_currency_tolerance=value.absolute_currency_tolerance,
    )

