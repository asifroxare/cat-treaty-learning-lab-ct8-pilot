"""Conversion-only CT6 adapter tests."""

import ast
from pathlib import Path

from cat_treaty.ct2_models import InuringCoverInput, LossBasisInput
from cat_treaty.ct3_models import CatLayerInput
from cat_treaty.ct5_models import CT5TreatyTerms
from cat_treaty.ct4_models import HoursElectionMethod
from cat_treaty.ct6_adapters import adapt_catalogue_request, adapt_hours_request
from cat_treaty.ct6_models import HoursComponentDTO, HoursInputDTO, HoursRunRequest, HoursTermsDTO
from tests.test_ct6_models import valid_request


def valid_hours_request(
    *,
    components: tuple[HoursComponentDTO, ...] | None = None,
    selected_method: HoursElectionMethod = HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
    manual_candidate_set_id: str | None = None,
) -> HoursRunRequest:
    catalogue = valid_request()
    source = catalogue.input.trials[0].occurrences[0]
    selected_components = components or (
        HoursComponentDTO(
            component_id="C1", subject_loss=20_000_000.0, timestamp=10.0,
            peril="wind", region="R1", causal_event_id="storm",
            source_reference="source",
        ),
        HoursComponentDTO(
            component_id="C2", subject_loss=20_000_000.0, timestamp=100.0,
            peril="wind", region="R1", causal_event_id="storm",
            source_reference="source",
        ),
    )
    return HoursRunRequest(
        api_schema_version="ct6.0",
        input=HoursInputDTO(
            scenario_id="H1", source_version="v1", components=selected_components,
            terms=HoursTermsDTO(
                treaty_term_start=0.0, treaty_term_end=365.0, hours_duration=72.0,
                permitted_perils=("wind",), permitted_regions=("R1",),
                causal_link_required=True,
                authorized_election_methods=(
                    HoursElectionMethod.EARLIEST_VALID_WINDOW,
                    HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
                    HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY,
                    HoursElectionMethod.MANUAL,
                ),
                selected_election_method=selected_method,
                manual_candidate_set_id=manual_candidate_set_id,
                rule_reference="CT4-hours",
            ),
            program_source=source, program=catalogue.input.program,
            treaty_terms=catalogue.input.treaty_terms, source_reference="source",
        ),
    )


def test_catalogue_adapter_preserves_authoritative_inputs_exactly() -> None:
    request = valid_request()
    adapted = adapt_catalogue_request(request)
    event = adapted.trials[0].occurrences[0]

    assert isinstance(event.loss_basis, LossBasisInput)
    assert isinstance(event.inuring_covers[0], InuringCoverInput)
    assert isinstance(adapted.layers[0], CatLayerInput)
    assert isinstance(adapted.treaty_terms, CT5TreatyTerms)
    assert event.loss_basis.initial_insured_loss == 45_000_000.0
    assert event.inuring_covers[0].cession_rate == 0.1
    assert adapted.layers[0].occurrence_limit == 20_000_000.0
    assert adapted.treaty_terms.layer_terms[0].original_layer_premium == 2_000_000.0


def test_adaptation_does_not_mutate_wire_request() -> None:
    request = valid_request()
    before = request.model_dump(mode="python")
    adapt_catalogue_request(request)
    assert request.model_dump(mode="python") == before


def test_adapter_imports_no_calculation_or_identity_engines() -> None:
    source = Path("cat_treaty/ct6_adapters.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_modules = {
        "cat_treaty.loss_basis", "cat_treaty.inuring", "cat_treaty.program",
        "cat_treaty.simulation", "cat_treaty.tail", "cat_treaty.frequency",
        "cat_treaty.annual_capacity", "cat_treaty.reinstatement",
        "cat_treaty.ct5_simulation", "cat_treaty.ct5_analytics",
        "cat_treaty.ct4_metadata", "cat_treaty.ct5_metadata",
    }
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not (imported & forbidden_modules)


def test_hours_adapter_requires_and_preserves_disclosed_program_source() -> None:
    catalogue = valid_request()
    request = valid_hours_request(components=(HoursComponentDTO(
        component_id="C1", subject_loss=20_000_000.0, timestamp=10.0,
        peril="wind", region="R1", causal_event_id="storm",
        source_reference="source",
    ),))
    adapted = adapt_hours_request(request)
    assert adapted.program_source.loss_basis == adapt_catalogue_request(catalogue).trials[0].occurrences[0].loss_basis
    assert adapted.components[0].subject_loss == 20_000_000.0
    assert adapted.terms.selected_election_method is HoursElectionMethod.MAXIMUM_SUBJECT_LOSS
