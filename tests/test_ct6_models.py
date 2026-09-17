"""Strict CT6 wire-contract validation."""

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from cat_treaty.ct2_models import InuringCoverType, InuringValuationMode, LossComponentCategory
from cat_treaty.ct3_models import OverlapCoordination
from cat_treaty.ct5_models import ReinstatementChargeType, ReinstatementTimeBasis
from cat_treaty.ct6_models import (
    AnnualTrialDTO,
    CatalogueInputDTO,
    CatalogueRunRequest,
    CatalogueSourceMode,
    CT6IdentityResponse,
    PostCapacityOccurrenceResponse,
    InuringCoverDTO,
    LayerDTO,
    LayerTermsDTO,
    LossBasisDTO,
    LossComponentDTO,
    ProgramTermsDTO,
    ReinstatementTrancheDTO,
    SimulationHeaderDTO,
    SourceOccurrenceDTO,
    TreatyTermsDTO,
)
from cat_treaty.models import SettlementMode


def valid_request(*, source_mode=CatalogueSourceMode.SUPPLIED, seed=None) -> CatalogueRunRequest:
    component = LossComponentDTO(
        component_id="I1", category=LossComponentCategory.SALVAGE,
        label="salvage", amount=1.0, included=False,
        source_reference="source", rule_reference="F03",
    )
    basis = LossBasisDTO(
        occurrence_id="E1", reporting_currency="USD",
        source_stage_declaration="insured_loss", source_reference="source",
        initial_insured_loss=45_000_000.0, components=(component,),
    )
    cover = InuringCoverDTO(
        cover_id="QS", cover_type=InuringCoverType.QUOTA_SHARE, order=1,
        valuation_mode=InuringValuationMode.CALCULATED_PROPORTIONAL,
        scope_fraction=1.0, currency="USD", description="quota share",
        source_reference="source", rule_reference="F05", cession_rate=0.1,
    )
    occurrence = SourceOccurrenceDTO(
        annual_trial_id=1, event_id="E1", event_time=10.0, event_sequence=1,
        peril="wind", region="R1", source_reference="source", trace_reference="trace",
        loss_basis=basis, inuring_covers=(cover,),
    )
    layer = LayerDTO(
        layer_id="L1", attachment=10_000_000.0, occurrence_limit=20_000_000.0,
        ceded_share=1.0, placement_share=1.0, currency="USD",
        description="20m xs 10m", source_reference="source", rule_reference="F11",
    )
    program = ProgramTermsDTO(
        program_id="P1", layers=(layer,), intentional_gap_acknowledged=False,
        overlap_coordination=OverlapCoordination.NONE, priority_order=None,
        description="program", source_reference="source", rule_reference="CT3",
    )
    tranche = ReinstatementTrancheDTO(
        sequence=1, premium_rate=1.0,
        time_basis=ReinstatementTimeBasis.PRO_RATA_REMAINING_TERM,
        charge_type=ReinstatementChargeType.PAID,
        source_reference="source", rule_reference="F30",
    )
    layer_terms = LayerTermsDTO(
        layer_id="L1", original_layer_premium=2_000_000.0,
        premium_basis_declaration="payable placed share", reinstatement_tranches=(tranche,),
        treaty_term_start=0.0, treaty_term_end=365.0,
        settlement_mode=SettlementMode.PAID_SEPARATELY,
        source_reference="source", rule_reference="CT5",
    )
    return CatalogueRunRequest(
        api_schema_version="ct6.0",
        input=CatalogueInputDTO(
            simulation=SimulationHeaderDTO(
                simulation_id="S1", trial_count=1,
                catalogue_source_mode=source_mode, catalogue_version="v1",
                source_version="v1", simulation_seed=seed,
            ),
            trials=(AnnualTrialDTO(annual_trial_id=1, catalogue_source_id="cat", occurrences=(occurrence,)),),
            program=program,
            treaty_terms=TreatyTermsDTO(
                program_id="P1", layer_terms=(layer_terms,),
                source_reference="source", rule_reference="CT5",
            ),
        ),
    )


def test_valid_strict_catalogue_request_is_frozen() -> None:
    request = valid_request()
    assert request.input.simulation.simulation_seed is None
    with pytest.raises(ValidationError):
        request.response_detail = "summary"  # type: ignore[misc]


def test_generated_requires_seed_and_supplied_forbids_seed() -> None:
    assert valid_request(source_mode=CatalogueSourceMode.GENERATED, seed=42).input.simulation.simulation_seed == 42
    with pytest.raises(ValidationError, match="generated requires a seed"):
        valid_request(source_mode=CatalogueSourceMode.GENERATED, seed=None)
    with pytest.raises(ValidationError, match="supplied requires null seed"):
        valid_request(source_mode=CatalogueSourceMode.SUPPLIED, seed=42)


def test_unknown_fields_and_numeric_strings_are_rejected() -> None:
    payload = valid_request().model_dump(mode="json")
    payload["unknown"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CatalogueRunRequest.model_validate(payload)
    payload.pop("unknown")
    payload["input"]["simulation"]["trial_count"] = "1"
    with pytest.raises(ValidationError):
        CatalogueRunRequest.model_validate(payload)


def test_non_finite_and_boolean_numbers_are_rejected() -> None:
    payload = valid_request().model_dump(mode="python")
    payload["input"]["trials"][0]["occurrences"][0]["loss_basis"]["initial_insured_loss"] = float("nan")
    with pytest.raises(ValidationError, match="NaN"):
        CatalogueRunRequest.model_validate(payload)
    payload = valid_request().model_dump(mode="python")
    payload["input"]["simulation"]["trial_count"] = True
    with pytest.raises(ValidationError):
        CatalogueRunRequest.model_validate(payload)


def test_exact_program_and_layer_term_mapping_is_required() -> None:
    payload = valid_request().model_dump(mode="python")
    payload["input"]["treaty_terms"]["program_id"] = "OTHER"
    with pytest.raises(ValidationError, match="map exactly"):
        CatalogueRunRequest.model_validate(payload)


def test_identity_response_requires_lowercase_sha256() -> None:
    digest = "a" * 64
    identity = CT6IdentityResponse(
        simulation_id="S1", ct4_input_hash=digest, ct4_result_hash=digest,
        ct5_input_hash=digest, ct5_result_hash=digest,
    )
    assert identity.ct5_result_hash == digest
    with pytest.raises(ValidationError):
        CT6IdentityResponse(
            simulation_id="S1", ct4_input_hash="A" * 64, ct4_result_hash=digest,
            ct5_input_hash=digest, ct5_result_hash=digest,
        )


def test_post_capacity_response_keeps_exact_three_way_fields_and_negative_cash() -> None:
    row = PostCapacityOccurrenceResponse(
        annual_trial_id=1, occurrence_sequence=1, event_id="E1",
        subject_loss=20.0, gross_contractual_recovery_pre_annual_capacity=15.0,
        gross_contractual_recovery=10.0,
        capacity_constrained_recovery_shortfall=5.0,
        insurer_net_subject_loss=10.0, reinstatement_premium_payable=12.0,
        net_cash_settlement=-2.0, reconciliation_passed=True,
        layer_event_rows=(),
    )
    assert row.gross_contractual_recovery == 10.0
    assert row.reinstatement_premium_payable == 12.0
    assert row.net_cash_settlement == -2.0
    assert "recovery" not in type(row).model_fields
    assert "net" not in type(row).model_fields
