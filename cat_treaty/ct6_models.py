"""Strict CT6 wire contracts; no actuarial calculations live here."""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr, field_validator, model_validator

from cat_treaty.ct2_models import InuringCoverType, InuringValuationMode, LossComponentCategory
from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.ct4_models import HoursElectionMethod
from cat_treaty.ct5_models import ReinstatementChargeType, ReinstatementTimeBasis
from cat_treaty.models import CapacityBasis, SettlementMode


CT6_API_VERSION = "ct6.0.0"
CT6_SCHEMA_VERSION = "ct6.0"
NonNegativeFloat = Annotated[StrictFloat, Field(ge=0, allow_inf_nan=False)]
PositiveFloat = Annotated[StrictFloat, Field(gt=0, allow_inf_nan=False)]
Fraction = Annotated[StrictFloat, Field(ge=0, le=1, allow_inf_nan=False)]
PositiveInt = Annotated[StrictInt, Field(ge=1)]
NonNegativeInt = Annotated[StrictInt, Field(ge=0)]


class CatalogueSourceMode(str, Enum):
    GENERATED = "generated"
    SUPPLIED = "supplied"


class ResponseDetail(str, Enum):
    FULL = "full"
    SUMMARY = "summary"


class RunMode(str, Enum):
    CATALOGUE = "catalogue"
    HOURS_CLAUSE = "hours_clause"


class StrictWireModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)

    @field_validator("*", mode="before")
    @classmethod
    def reject_non_finite_numbers(cls, value: object) -> object:
        if isinstance(value, float) and value != value:
            raise ValueError("NaN is not permitted")
        if isinstance(value, float) and value in (float("inf"), float("-inf")):
            raise ValueError("infinity is not permitted")
        return value


class LossComponentDTO(StrictWireModel):
    component_id: StrictStr
    category: LossComponentCategory
    label: StrictStr
    amount: NonNegativeFloat
    included: StrictBool
    source_reference: StrictStr
    rule_reference: StrictStr

    @field_validator("component_id", "label", "source_reference", "rule_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value


class LossBasisDTO(StrictWireModel):
    occurrence_id: StrictStr
    reporting_currency: StrictStr
    source_stage_declaration: StrictStr
    source_reference: StrictStr
    initial_insured_loss: NonNegativeFloat
    components: tuple[LossComponentDTO, ...] = ()
    ground_up_loss: NonNegativeFloat | None = None

    @field_validator("occurrence_id", "reporting_currency", "source_stage_declaration", "source_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value

    @model_validator(mode="after")
    def unique_components(self) -> "LossBasisDTO":
        ids = tuple(item.component_id for item in self.components)
        if len(ids) != len(set(ids)):
            raise ValueError("component_id values must be unique")
        return self


class InuringCoverDTO(StrictWireModel):
    cover_id: StrictStr
    cover_type: InuringCoverType
    order: PositiveInt
    valuation_mode: InuringValuationMode
    scope_fraction: Fraction
    currency: StrictStr
    description: StrictStr
    source_reference: StrictStr
    rule_reference: StrictStr
    cession_rate: Fraction | None = None
    occurrence_limit: PositiveFloat | None = None
    aggregate_remaining_before: NonNegativeFloat | None = None
    supplied_recovery: NonNegativeFloat | None = None
    recovery_source_id: StrictStr | None = None

    @field_validator("cover_id", "currency", "description", "source_reference", "rule_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value

    @model_validator(mode="after")
    def valuation_shape(self) -> "InuringCoverDTO":
        if self.valuation_mode is InuringValuationMode.CALCULATED_PROPORTIONAL:
            if self.cover_type is not InuringCoverType.QUOTA_SHARE or self.cession_rate is None:
                raise ValueError("calculated_proportional requires quota_share and cession_rate")
            if self.supplied_recovery is not None or self.recovery_source_id is not None:
                raise ValueError("calculated_proportional forbids supplied recovery fields")
        else:
            if self.cession_rate is not None or self.supplied_recovery is None:
                raise ValueError("supplied_recovery mode requires supplied_recovery and forbids cession_rate")
            if self.recovery_source_id is None or not self.recovery_source_id.strip():
                raise ValueError("supplied_recovery mode requires recovery_source_id")
        return self


class SourceOccurrenceDTO(StrictWireModel):
    annual_trial_id: PositiveInt
    event_id: StrictStr
    event_time: NonNegativeFloat
    event_sequence: PositiveInt
    peril: StrictStr
    region: StrictStr
    source_reference: StrictStr
    trace_reference: StrictStr
    loss_basis: LossBasisDTO
    inuring_covers: tuple[InuringCoverDTO, ...] = ()

    @field_validator("event_id", "peril", "region", "source_reference", "trace_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value

    @model_validator(mode="after")
    def occurrence_contract(self) -> "SourceOccurrenceDTO":
        if self.event_id != self.loss_basis.occurrence_id:
            raise ValueError("event_id must match loss_basis occurrence_id")
        orders = tuple(item.order for item in self.inuring_covers)
        if orders != tuple(range(1, len(orders) + 1)):
            raise ValueError("inuring cover order must be contiguous from one")
        ids = tuple(item.cover_id for item in self.inuring_covers)
        if len(ids) != len(set(ids)):
            raise ValueError("cover_id values must be unique")
        if any(item.currency != self.loss_basis.reporting_currency for item in self.inuring_covers):
            raise ValueError("inuring currency must match reporting_currency")
        return self


class AnnualTrialDTO(StrictWireModel):
    annual_trial_id: PositiveInt
    catalogue_source_id: StrictStr
    occurrences: tuple[SourceOccurrenceDTO, ...] = ()

    @model_validator(mode="after")
    def trial_contract(self) -> "AnnualTrialDTO":
        if not self.catalogue_source_id.strip():
            raise ValueError("catalogue_source_id must be non-empty")
        if any(item.annual_trial_id != self.annual_trial_id for item in self.occurrences):
            raise ValueError("occurrence annual_trial_id must match trial")
        ids = tuple(item.event_id for item in self.occurrences)
        if len(ids) != len(set(ids)):
            raise ValueError("event_id values must be unique within a trial")
        sequences = tuple(item.event_sequence for item in self.occurrences)
        if len(sequences) != len(set(sequences)):
            raise ValueError("event_sequence values must be unique within a trial")
        return self


class TailConfigurationDTO(StrictWireModel):
    probability_levels: tuple[Fraction, ...] = (0.95, 0.99, 0.995)
    tvar_levels: tuple[Fraction, ...] = (0.99,)
    return_periods: tuple[PositiveFloat, ...] = (2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0)

    @model_validator(mode="after")
    def valid_levels(self) -> "TailConfigurationDTO":
        for values in (self.probability_levels, self.tvar_levels, self.return_periods):
            if not values or len(values) != len(set(values)):
                raise ValueError("tail configuration values must be non-empty and unique")
        if any(value <= 0 or value >= 1 for value in self.probability_levels + self.tvar_levels):
            raise ValueError("probability levels must lie in (0, 1)")
        if any(value <= 1 for value in self.return_periods):
            raise ValueError("return periods must exceed one")
        return self


class ToleranceProfileDTO(StrictWireModel):
    relative_tolerance: Literal[1e-12] = 1e-12
    absolute_currency_tolerance: Literal[1e-6] = 1e-6


class SimulationHeaderDTO(StrictWireModel):
    simulation_id: StrictStr
    trial_count: Annotated[StrictInt, Field(ge=1, le=10_000)]
    catalogue_source_mode: CatalogueSourceMode
    catalogue_version: StrictStr
    source_version: StrictStr
    simulation_seed: NonNegativeInt | None
    tail_configuration: TailConfigurationDTO = TailConfigurationDTO()
    tolerance_profile: ToleranceProfileDTO = ToleranceProfileDTO()

    @model_validator(mode="after")
    def provenance_contract(self) -> "SimulationHeaderDTO":
        for value in (self.simulation_id, self.catalogue_version, self.source_version):
            if not value.strip():
                raise ValueError("simulation identifiers and versions must be non-empty")
        generated = self.catalogue_source_mode is CatalogueSourceMode.GENERATED
        if generated != (self.simulation_seed is not None):
            raise ValueError("generated requires a seed; supplied requires null seed")
        return self


class LayerDTO(StrictWireModel):
    layer_id: StrictStr
    attachment: NonNegativeFloat
    occurrence_limit: PositiveFloat
    ceded_share: Fraction
    placement_share: Fraction
    currency: StrictStr
    description: StrictStr
    source_reference: StrictStr
    rule_reference: StrictStr

    @field_validator("layer_id", "currency", "description", "source_reference", "rule_reference")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must be non-empty")
        return value


class ProgramTermsDTO(StrictWireModel):
    program_id: StrictStr
    layers: tuple[LayerDTO, ...]
    intentional_gap_acknowledged: StrictBool
    overlap_coordination: OverlapCoordination
    priority_order: tuple[StrictStr, ...] | None
    description: StrictStr
    source_reference: StrictStr
    rule_reference: StrictStr

    @model_validator(mode="after")
    def program_shape(self) -> "ProgramTermsDTO":
        if not 1 <= len(self.layers) <= 4:
            raise ValueError("program requires one to four layers")
        ids = tuple(item.layer_id for item in self.layers)
        if len(ids) != len(set(ids)):
            raise ValueError("layer_id values must be unique")
        if self.priority_order is not None and set(self.priority_order) != set(ids):
            raise ValueError("priority_order must contain every layer exactly once")
        return self


class ReinstatementTrancheDTO(StrictWireModel):
    sequence: PositiveInt
    premium_rate: NonNegativeFloat
    time_basis: ReinstatementTimeBasis
    charge_type: ReinstatementChargeType
    source_reference: StrictStr
    rule_reference: StrictStr

    @model_validator(mode="after")
    def charge_contract(self) -> "ReinstatementTrancheDTO":
        if self.charge_type is ReinstatementChargeType.FREE and self.premium_rate != 0:
            raise ValueError("free tranche requires zero premium_rate")
        if self.charge_type is ReinstatementChargeType.PAID and self.premium_rate <= 0:
            raise ValueError("paid tranche requires positive premium_rate")
        return self


class LayerTermsDTO(StrictWireModel):
    layer_id: StrictStr
    original_layer_premium: NonNegativeFloat
    premium_basis_declaration: StrictStr
    reinstatement_tranches: tuple[ReinstatementTrancheDTO, ...] = ()
    treaty_term_start: NonNegativeFloat
    treaty_term_end: PositiveFloat
    settlement_mode: SettlementMode
    source_reference: StrictStr
    rule_reference: StrictStr
    capacity_basis: CapacityBasis = CapacityBasis.PAYABLE_PLACED_SHARE

    @model_validator(mode="after")
    def term_contract(self) -> "LayerTermsDTO":
        if self.treaty_term_end <= self.treaty_term_start:
            raise ValueError("treaty_term_end must exceed treaty_term_start")
        sequences = tuple(item.sequence for item in self.reinstatement_tranches)
        if sequences != tuple(range(1, len(sequences) + 1)):
            raise ValueError("tranche sequences must be contiguous from one")
        return self


class TreatyTermsDTO(StrictWireModel):
    program_id: StrictStr
    layer_terms: tuple[LayerTermsDTO, ...]
    source_reference: StrictStr
    rule_reference: StrictStr

    @model_validator(mode="after")
    def treaty_shape(self) -> "TreatyTermsDTO":
        if not 1 <= len(self.layer_terms) <= 4:
            raise ValueError("treaty requires one to four layer records")
        ids = tuple(item.layer_id for item in self.layer_terms)
        if len(ids) != len(set(ids)):
            raise ValueError("layer term IDs must be unique")
        if len({item.settlement_mode for item in self.layer_terms}) != 1:
            raise ValueError("settlement_mode must be simulation-wide")
        return self


class CatalogueInputDTO(StrictWireModel):
    simulation: SimulationHeaderDTO
    trials: tuple[AnnualTrialDTO, ...]
    program: ProgramTermsDTO
    treaty_terms: TreatyTermsDTO

    @model_validator(mode="after")
    def catalogue_contract(self) -> "CatalogueInputDTO":
        ids = tuple(item.annual_trial_id for item in self.trials)
        if ids != tuple(range(1, self.simulation.trial_count + 1)):
            raise ValueError("trial IDs must be contiguous through trial_count")
        occurrence_count = sum(len(item.occurrences) for item in self.trials)
        if occurrence_count > 100_000:
            raise ValueError("total occurrences cannot exceed 100000")
        event_ids = tuple(item.event_id for trial in self.trials for item in trial.occurrences)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("event_id values must be simulation-wide unique")
        layer_ids = {item.layer_id for item in self.program.layers}
        if self.treaty_terms.program_id != self.program.program_id or {item.layer_id for item in self.treaty_terms.layer_terms} != layer_ids:
            raise ValueError("program and CT5 treaty terms must map exactly")
        currencies = {item.loss_basis.reporting_currency for trial in self.trials for item in trial.occurrences}
        if currencies and (len(currencies) != 1 or currencies != {item.currency for item in self.program.layers}):
            raise ValueError("occurrence and layer currencies must match")
        return self


class HoursComponentDTO(StrictWireModel):
    component_id: StrictStr
    subject_loss: NonNegativeFloat
    timestamp: NonNegativeFloat
    peril: StrictStr
    region: StrictStr
    causal_event_id: StrictStr
    source_reference: StrictStr


class HoursTermsDTO(StrictWireModel):
    treaty_term_start: NonNegativeFloat
    treaty_term_end: PositiveFloat
    hours_duration: PositiveFloat
    permitted_perils: tuple[StrictStr, ...]
    permitted_regions: tuple[StrictStr, ...]
    causal_link_required: StrictBool
    authorized_election_methods: tuple[HoursElectionMethod, ...]
    selected_election_method: HoursElectionMethod
    manual_candidate_set_id: StrictStr | None
    rule_reference: StrictStr

    @model_validator(mode="after")
    def hours_contract(self) -> "HoursTermsDTO":
        if self.treaty_term_end <= self.treaty_term_start:
            raise ValueError("treaty term end must exceed start")
        if self.selected_election_method not in self.authorized_election_methods:
            raise ValueError("selected election method must be authorized")
        manual = self.selected_election_method is HoursElectionMethod.MANUAL
        if manual != (self.manual_candidate_set_id is not None):
            raise ValueError("manual candidate ID is required only for manual election")
        return self


class HoursInputDTO(StrictWireModel):
    scenario_id: StrictStr
    source_version: StrictStr
    components: tuple[HoursComponentDTO, ...]
    terms: HoursTermsDTO
    program_source: SourceOccurrenceDTO
    program: ProgramTermsDTO
    treaty_terms: TreatyTermsDTO
    tail_configuration: TailConfigurationDTO = TailConfigurationDTO()
    tolerance_profile: ToleranceProfileDTO = ToleranceProfileDTO()
    source_reference: StrictStr

    @model_validator(mode="after")
    def scenario_contract(self) -> "HoursInputDTO":
        if not 1 <= len(self.components) <= 12:
            raise ValueError("hours-clause teaching requires one to twelve components")
        ids = tuple(item.component_id for item in self.components)
        if len(ids) != len(set(ids)):
            raise ValueError("component IDs must be unique")
        if self.program_source.annual_trial_id != 1:
            raise ValueError("hours program source must use annual_trial_id one")
        layer_ids = {item.layer_id for item in self.program.layers}
        if self.treaty_terms.program_id != self.program.program_id or {item.layer_id for item in self.treaty_terms.layer_terms} != layer_ids:
            raise ValueError("program and CT5 treaty terms must map exactly")
        if {item.currency for item in self.program.layers} != {self.program_source.loss_basis.reporting_currency}:
            raise ValueError("program source and layer currencies must match")
        return self


class CatalogueRunRequest(StrictWireModel):
    api_schema_version: Literal["ct6.0"]
    client_request_id: StrictStr | None = None
    response_detail: ResponseDetail = ResponseDetail.FULL
    input: CatalogueInputDTO


class HoursRunRequest(StrictWireModel):
    api_schema_version: Literal["ct6.0"]
    client_request_id: StrictStr | None = None
    response_detail: ResponseDetail = ResponseDetail.FULL
    input: HoursInputDTO


class CT6IdentityResponse(StrictWireModel):
    simulation_id: StrictStr
    ct4_input_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    ct4_result_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    ct5_input_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    ct5_result_hash: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]


class CT6ApiResponseInfo(StrictWireModel):
    request_id: StrictStr
    client_request_id: StrictStr | None
    api_version: Literal["ct6.0.0"] = CT6_API_VERSION
    api_schema_version: Literal["ct6.0"] = CT6_SCHEMA_VERSION
    completion_status: Literal["complete"] = "complete"
    run_mode: RunMode


class CT6RequestSummaryResponse(StrictWireModel):
    simulation_id: StrictStr
    reporting_currency: StrictStr
    trial_count: PositiveInt
    occurrence_count: NonNegativeInt
    program_id: StrictStr
    layer_ids: tuple[StrictStr, ...]
    response_detail: ResponseDetail


class CT6VersionsResponse(StrictWireModel):
    ct2_engine_version: StrictStr
    ct2_schema_version: StrictStr
    ct3_engine_version: StrictStr
    ct3_schema_version: StrictStr
    ct4_engine_version: StrictStr
    ct4_schema_version: StrictStr
    ct5_engine_version: StrictStr
    ct5_schema_version: StrictStr
    ct6_api_version: Literal["ct6.0.0"] = CT6_API_VERSION
    ct6_schema_version: Literal["ct6.0"] = CT6_SCHEMA_VERSION


class PreCapacityOccurrenceResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    occurrence_sequence: PositiveInt
    event_id: StrictStr
    subject_loss: NonNegativeFloat
    gross_contractual_recovery_pre_annual_capacity: NonNegativeFloat
    insurer_net_loss_pre_annual_capacity: NonNegativeFloat
    reconciliation_passed: StrictBool


class PreCapacityAnnualResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    subject_loss: NonNegativeFloat
    gross_contractual_recovery_pre_annual_capacity: NonNegativeFloat
    insurer_net_loss_pre_annual_capacity: NonNegativeFloat
    maximum_occurrence_recovery_pre_annual_capacity: NonNegativeFloat
    reconciliation_passed: StrictBool


class PostCapacityLayerEventResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    occurrence_sequence: PositiveInt
    event_id: StrictStr
    layer_id: StrictStr
    pre_annual_capacity_recovery: NonNegativeFloat
    active_capacity_before: NonNegativeFloat
    gross_contractual_recovery: NonNegativeFloat
    capacity_constrained_recovery_shortfall: NonNegativeFloat
    active_capacity_after_recovery: NonNegativeFloat
    amount_reinstated: NonNegativeFloat
    active_capacity_for_next_event: NonNegativeFloat
    reinstatement_premium_payable: NonNegativeFloat


class PostCapacityOccurrenceResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    occurrence_sequence: PositiveInt
    event_id: StrictStr
    subject_loss: NonNegativeFloat
    gross_contractual_recovery_pre_annual_capacity: NonNegativeFloat
    gross_contractual_recovery: NonNegativeFloat
    capacity_constrained_recovery_shortfall: NonNegativeFloat
    insurer_net_subject_loss: NonNegativeFloat
    reinstatement_premium_payable: NonNegativeFloat
    net_cash_settlement: StrictFloat
    reconciliation_passed: StrictBool
    layer_event_rows: tuple[PostCapacityLayerEventResponse, ...]


class PostCapacityLayerAnnualResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    layer_id: StrictStr
    initial_capacity: NonNegativeFloat
    initial_reinstatement_reserve: NonNegativeFloat
    total_recovery: NonNegativeFloat
    total_reinstated: NonNegativeFloat
    final_active_capacity: NonNegativeFloat
    final_reinstatement_reserve: NonNegativeFloat
    realized_capacity_utilization: Fraction | None
    realized_capacity_utilization_status: StrictStr
    reinstatement_reserve_utilization: Fraction | None
    reinstatement_reserve_utilization_status: StrictStr


class PostCapacityAnnualResponse(StrictWireModel):
    annual_trial_id: PositiveInt
    subject_loss: NonNegativeFloat
    gross_contractual_recovery: NonNegativeFloat
    capacity_constrained_recovery_shortfall: NonNegativeFloat
    insurer_net_subject_loss: NonNegativeFloat
    reinstatement_premium_payable: NonNegativeFloat
    net_cash_settlement: StrictFloat
    maximum_occurrence_recovery: NonNegativeFloat
    reconciliation_passed: StrictBool
    layer_summaries: tuple[PostCapacityLayerAnnualResponse, ...]


class CT6ErrorItem(StrictWireModel):
    path: StrictStr
    code: StrictStr
    message: StrictStr
    rule_reference: StrictStr


class CT6ProblemResponse(StrictWireModel):
    type: StrictStr
    title: StrictStr
    status: StrictInt
    code: StrictStr
    detail: StrictStr
    instance: StrictStr
    request_id: StrictStr
    errors: tuple[CT6ErrorItem, ...] = ()


class CT6WarningResponse(StrictWireModel):
    code: StrictStr
    message: StrictStr
    source: StrictStr
    return_period: StrictFloat | None = None


class CT6ReconciliationResponse(StrictWireModel):
    scope: StrictStr
    identifier: StrictStr
    passed: StrictBool
    formula_references: tuple[StrictStr, ...]


class CT6LearningFactResponse(StrictWireModel):
    category: StrictStr
    metric_name: StrictStr
    value: StrictFloat | None
    meaning: StrictStr
    driver_statement: StrictStr
    trace_references: tuple[StrictStr, ...]


class CT6CandidateWindowResponse(StrictWireModel):
    candidate_id: StrictStr
    start: StrictFloat
    end: StrictFloat
    component_ids: tuple[StrictStr, ...]
    subject_loss: NonNegativeFloat
    admissibility: StrictStr
    exclusion_codes: tuple[StrictStr, ...]
    exclusion_reasons: tuple[StrictStr, ...]
    affected_ids: tuple[StrictStr, ...]
    rule_reference: StrictStr


class CT6CandidateSetResponse(StrictWireModel):
    candidate_set_id: StrictStr
    window_ids: tuple[StrictStr, ...]
    total_subject_loss: NonNegativeFloat
    total_contractual_recovery: NonNegativeFloat | None
    admissibility: StrictStr
    exclusion_codes: tuple[StrictStr, ...]
    exclusion_reasons: tuple[StrictStr, ...]
    affected_ids: tuple[StrictStr, ...]
    rule_reference: StrictStr


class CT6PreCapacityResponse(StrictWireModel):
    occurrence_rows: tuple[PreCapacityOccurrenceResponse, ...] | None
    annual_rows: tuple[PreCapacityAnnualResponse, ...]
    tail_analytics: dict[str, object]
    frequency_analytics: dict[str, object]
    candidate_windows: tuple[CT6CandidateWindowResponse, ...] = ()
    candidate_sets: tuple[CT6CandidateSetResponse, ...] = ()
    selected_candidate_set_id: StrictStr | None = None
    valid_candidate_set_ids: tuple[StrictStr, ...] = ()
    selected_election_method: StrictStr | None = None


class CT6PostCapacityResponse(StrictWireModel):
    occurrence_rows: tuple[PostCapacityOccurrenceResponse, ...] | None
    annual_rows: tuple[PostCapacityAnnualResponse, ...]
    analytics: dict[str, object]


class CT6LearningResponse(StrictWireModel):
    facts: tuple[CT6LearningFactResponse, ...]
    reconciliations: tuple[CT6ReconciliationResponse, ...]


class CT6SuccessResponse(StrictWireModel):
    api: CT6ApiResponseInfo
    request: CT6RequestSummaryResponse
    versions: CT6VersionsResponse
    identity: CT6IdentityResponse
    pre_capacity: CT6PreCapacityResponse
    post_capacity: CT6PostCapacityResponse
    learning: CT6LearningResponse
    warnings: tuple[CT6WarningResponse, ...]
