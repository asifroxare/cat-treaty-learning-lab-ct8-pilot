"""Validation tests for immutable CT4 catalogue and analytics contracts."""

from dataclasses import FrozenInstanceError, replace
import math

import pytest

from cat_treaty.ct2_metadata import build_ct2_run_metadata
from cat_treaty.ct2_models import InuringWaterfallInput
from cat_treaty.ct4_models import (
    CandidateAdmissibility,
    CT4AnnualTrialInput,
    CT4OccurrenceInput,
    CT4OccurrenceLedgerRow,
    CT4AnnualLedgerRow,
    CT4RunIdentity,
    CT4SimulationInput,
    HoursCandidateSet,
    HoursCandidateWindow,
    HoursClauseScenario,
    HoursClauseTerms,
    HoursElectionMethod,
    HoursExclusionCode,
    HoursLossComponent,
    MetricPerspective,
    NumericalToleranceProfile,
    OccurrenceDefinitionMode,
    PerspectiveAnalytics,
    RatioStatus,
    TailConfiguration,
    TailEstimate,
    TailWarning,
    TailWarningCode,
)
from cat_treaty.program import evaluate_cat_xl_program
from tests.test_ct3_models import program


def occurrence(**changes: object) -> CT4OccurrenceInput:
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "event_id": "OCC-CT3",
        "event_time": 42.0,
        "event_sequence": 1,
        "peril": "hurricane",
        "region": "coastal",
        "program_input": program(),
        "source_reference": "catalogue:event",
        "trace_reference": "CT4-entry",
    }
    values.update(changes)
    return CT4OccurrenceInput(**values)


def program_for_event(event_id: str, **changes: object):
    base = program()
    basis_input = replace(
        base.ct2_result.loss_basis.basis_input,
        occurrence_id=event_id,
    )
    basis = replace(base.ct2_result.loss_basis, basis_input=basis_input)
    result = replace(base.ct2_result, loss_basis=basis)
    metadata = build_ct2_run_metadata(
        waterfall_input=InuringWaterfallInput(loss_basis=basis),
        source_version=base.ct2_metadata.source_version,
        engine_version=base.ct2_metadata.engine_version,
        schema_version=base.ct2_metadata.schema_version,
    )
    values: dict[str, object] = {
        "ct2_result": result,
        "ct2_metadata": metadata,
    }
    values.update(changes)
    return replace(base, **values)


def trial(
    annual_trial_id: int = 1,
    occurrences: tuple[CT4OccurrenceInput, ...] | None = None,
) -> CT4AnnualTrialInput:
    selected = () if occurrences is None else occurrences
    return CT4AnnualTrialInput(
        annual_trial_id=annual_trial_id,
        catalogue_source_id=f"trial-{annual_trial_id}",
        occurrences=selected,
    )


def hours_terms(**changes: object) -> HoursClauseTerms:
    values: dict[str, object] = {
        "treaty_term_start": 0.0,
        "treaty_term_end": 8_760.0,
        "hours_duration": 72.0,
        "permitted_perils": ("hurricane",),
        "permitted_regions": ("coastal",),
        "causal_link_required": True,
        "authorized_election_methods": (
            HoursElectionMethod.EARLIEST_VALID_WINDOW,
            HoursElectionMethod.MAXIMUM_SUBJECT_LOSS,
        ),
        "selected_election_method": HoursElectionMethod.EARLIEST_VALID_WINDOW,
        "manual_candidate_set_id": None,
        "rule_reference": "hours-clause",
    }
    values.update(changes)
    return HoursClauseTerms(**values)


COMPONENTS = (
    HoursLossComponent(
        component_id="C1",
        subject_loss=10.0,
        timestamp=100.0,
        peril="hurricane",
        region="coastal",
        causal_event_id="CAUSE-1",
        source_reference="loss:C1",
    ),
    HoursLossComponent(
        component_id="C2",
        subject_loss=20.0,
        timestamp=150.0,
        peril="hurricane",
        region="coastal",
        causal_event_id="CAUSE-1",
        source_reference="loss:C2",
    ),
)


def hours_scenario(**changes: object) -> HoursClauseScenario:
    values: dict[str, object] = {
        "scenario_id": "HOURS-1",
        "components": COMPONENTS,
        "terms": hours_terms(),
        "program_terms_source": program(),
        "source_reference": "teaching:hours",
    }
    values.update(changes)
    return HoursClauseScenario(**values)


def simulation(**changes: object) -> CT4SimulationInput:
    base_occurrence = occurrence()
    values: dict[str, object] = {
        "simulation_id": "SIM-1",
        "trial_count": 2,
        "trials": (trial(1, (base_occurrence,)), trial(2)),
        "catalogue_version": "catalogue-v1",
        "source_version": "ct4-source-v1",
        "simulation_seed": 42,
        "occurrence_definition_mode": OccurrenceDefinitionMode.CATALOGUE_DEFINED,
        "tail_configuration": TailConfiguration(),
        "tolerance_profile": NumericalToleranceProfile(),
    }
    values.update(changes)
    return CT4SimulationInput(**values)


def test_ct4_enum_literals_are_frozen() -> None:
    assert OccurrenceDefinitionMode.CATALOGUE_DEFINED.value == "catalogue_defined"
    assert HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY.value == "maximum_contractual_recovery"
    assert HoursExclusionCode.OVERLAPPING_WINDOWS.value == "overlapping_windows"
    assert MetricPerspective.RECOVERY_PRE_ANNUAL_CAPACITY.value == "recovery_pre_annual_capacity"
    assert TailWarningCode.RETURN_PERIOD_EXCEEDS_SAMPLE.value == "return_period_exceeds_sample"


def test_tolerance_profile_is_immutable_and_positive() -> None:
    profile = NumericalToleranceProfile()
    with pytest.raises(FrozenInstanceError):
        profile.relative_tolerance = 1.0  # type: ignore[misc]
    for changes in (
        {"relative_tolerance": 0.0},
        {"absolute_currency_tolerance": -1.0},
        {"relative_tolerance": math.nan},
    ):
        with pytest.raises(ValueError):
            replace(profile, **changes)


def test_tail_configuration_defaults_are_frozen() -> None:
    config = TailConfiguration()
    assert config.probability_levels == (0.95, 0.99, 0.995)
    assert config.tvar_levels == (0.99,)
    assert config.return_periods == (2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0)


@pytest.mark.parametrize(
    "changes",
    [
        {"probability_levels": ()},
        {"probability_levels": (0.95, 0.95)},
        {"probability_levels": (0.0,)},
        {"probability_levels": (1.0,)},
        {"tvar_levels": (math.nan,)},
        {"return_periods": (1.0,)},
        {"return_periods": (10.0, 10.0)},
    ],
)
def test_tail_configuration_rejects_invalid_values(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        replace(TailConfiguration(), **changes)


def test_occurrence_requires_event_level_ct3_input_and_matching_identity() -> None:
    event = occurrence()
    assert event.program_input.ct2_result.cat_xl_subject_loss == 45_000_000.0
    with pytest.raises(ValueError, match="occurrence ID"):
        occurrence(event_id="OTHER")
    with pytest.raises(ValueError, match="CT3ProgramInput"):
        occurrence(program_input=45_000_000.0)


@pytest.mark.parametrize(
    "changes",
    [
        {"annual_trial_id": 0},
        {"event_id": ""},
        {"event_time": -1.0},
        {"event_time": math.inf},
        {"event_sequence": True},
        {"peril": " "},
        {"region": ""},
    ],
)
def test_occurrence_rejects_invalid_event_fields(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        occurrence(**changes)


def test_trial_accepts_explicit_empty_year() -> None:
    empty = trial()
    assert empty.occurrences == ()


def test_trial_requires_matching_trial_ids_and_unique_events() -> None:
    with pytest.raises(ValueError, match="match"):
        trial(2, (occurrence(annual_trial_id=1),))
    event = occurrence()
    with pytest.raises(ValueError, match="unique"):
        trial(1, (event, event))


def test_catalogue_simulation_includes_contiguous_empty_trials() -> None:
    request = simulation()
    assert request.trial_count == 2
    assert request.trials[1].occurrences == ()
    with pytest.raises(FrozenInstanceError):
        request.trial_count = 3  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"trial_count": 0}, "positive"),
        ({"trials": (trial(1),)}, "contiguous"),
        ({"trials": (trial(2), trial(1))}, "contiguous"),
        ({"simulation_seed": -1}, "simulation_seed"),
        ({"simulation_seed": True}, "simulation_seed"),
        ({"occurrence_definition_mode": "catalogue_defined"}, "supported"),
        ({"hours_clause_scenario": hours_scenario()}, "forbids"),
    ],
)
def test_simulation_rejects_invalid_population(changes: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        simulation(**changes)


def test_simulation_rejects_duplicate_event_ids_across_trials() -> None:
    first = occurrence(annual_trial_id=1)
    second = occurrence(annual_trial_id=2)
    with pytest.raises(ValueError, match="unique"):
        simulation(trials=(trial(1, (first,)), trial(2, (second,))))


def test_simulation_requires_one_fixed_program_term_fingerprint() -> None:
    second_program = program_for_event("OCC-2")
    second = occurrence(
        annual_trial_id=2,
        event_id="OCC-2",
        program_input=second_program,
    )
    valid = simulation(
        trials=(trial(1, (occurrence(),)), trial(2, (second,)))
    )
    assert len(valid.trials[1].occurrences) == 1

    changed_program = replace(
        second_program,
        layers=(
            replace(second_program.layers[0], ceded_share=0.9),
            second_program.layers[1],
        ),
    )
    changed = replace(second, program_input=changed_program)
    with pytest.raises(ValueError, match="fixed program-term fingerprint"):
        simulation(
            trials=(trial(1, (occurrence(),)), trial(2, (changed,)))
        )


def test_hours_terms_enforce_authorization_and_manual_selection() -> None:
    manual = hours_terms(
        authorized_election_methods=(HoursElectionMethod.MANUAL,),
        selected_election_method=HoursElectionMethod.MANUAL,
        manual_candidate_set_id="SET-1",
    )
    assert manual.manual_candidate_set_id == "SET-1"
    with pytest.raises(ValueError, match="authorized"):
        hours_terms(selected_election_method=HoursElectionMethod.MAXIMUM_CONTRACTUAL_RECOVERY)
    with pytest.raises(ValueError, match="manual_candidate_set_id"):
        hours_terms(
            authorized_election_methods=(HoursElectionMethod.MANUAL,),
            selected_election_method=HoursElectionMethod.MANUAL,
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"treaty_term_end": 0.0},
        {"hours_duration": 0.0},
        {"permitted_perils": ()},
        {"permitted_regions": ("coastal", "coastal")},
        {"causal_link_required": 1},
        {"authorized_election_methods": ()},
    ],
)
def test_hours_terms_reject_invalid_contract(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        hours_terms(**changes)


def test_hours_component_requires_complete_timestamped_attributes() -> None:
    with pytest.raises(ValueError):
        replace(COMPONENTS[0], timestamp=math.nan)
    with pytest.raises(ValueError):
        replace(COMPONENTS[0], causal_event_id="")
    with pytest.raises(ValueError):
        replace(COMPONENTS[0], subject_loss=-1.0)


def test_hours_scenario_is_bounded_to_twelve_unique_components() -> None:
    assert len(hours_scenario().components) == 2
    with pytest.raises(ValueError, match="one to twelve"):
        hours_scenario(components=())
    thirteen = tuple(
        replace(COMPONENTS[0], component_id=f"C{index}")
        for index in range(13)
    )
    with pytest.raises(ValueError, match="one to twelve"):
        hours_scenario(components=thirteen)
    with pytest.raises(ValueError, match="unique"):
        hours_scenario(components=(COMPONENTS[0], COMPONENTS[0]))


def test_hours_mode_requires_exactly_one_empty_catalogue_trial() -> None:
    request = simulation(
        trial_count=1,
        trials=(trial(1),),
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        hours_clause_scenario=hours_scenario(),
    )
    assert request.hours_clause_scenario is not None
    with pytest.raises(ValueError, match="trial_count = 1"):
        simulation(
            occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
            hours_clause_scenario=hours_scenario(),
        )
    with pytest.raises(ValueError, match="cannot mix"):
        simulation(
            trial_count=1,
            trials=(trial(1, (occurrence(),)),),
            occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
            hours_clause_scenario=hours_scenario(),
        )


def test_valid_and_excluded_candidate_windows_require_matching_evidence() -> None:
    valid = HoursCandidateWindow(
        "W1", 100.0, 172.0, ("C1", "C2"), 30.0,
        CandidateAdmissibility.VALID, (), (), (), "hours-clause",
    )
    excluded = replace(
        valid,
        candidate_id="W2",
        admissibility=CandidateAdmissibility.EXCLUDED,
        exclusion_codes=(HoursExclusionCode.CAUSAL_LINK_FAILURE,),
        exclusion_reasons=("Components do not share the required cause.",),
        affected_ids=("C2",),
    )
    assert excluded.exclusion_codes == (HoursExclusionCode.CAUSAL_LINK_FAILURE,)
    with pytest.raises(ValueError, match="admissibility"):
        replace(valid, admissibility=CandidateAdmissibility.EXCLUDED)
    with pytest.raises(ValueError, match="admissibility"):
        replace(excluded, admissibility=CandidateAdmissibility.VALID)


def test_valid_candidate_set_requires_recovery_and_excluded_set_requires_reasons() -> None:
    valid = HoursCandidateSet(
        "SET-1", ("W1",), 30.0, 20.0,
        CandidateAdmissibility.VALID, (), (),
    )
    assert valid.total_contractual_recovery == 20.0
    with pytest.raises(ValueError, match="requires contractual recovery"):
        replace(valid, total_contractual_recovery=None)
    with pytest.raises(ValueError, match="evidence"):
        replace(valid, admissibility=CandidateAdmissibility.EXCLUDED)


def test_tail_warning_record_preserves_each_applicable_code() -> None:
    warnings = tuple(
        TailWarning(code, 200.0, 0.5, code.value)
        for code in TailWarningCode
    )
    estimate = TailEstimate(level=200.0, value=50.0, warnings=warnings)
    assert tuple(item.code for item in estimate.warnings) == tuple(TailWarningCode)


def test_perspective_analytics_reconciles_mean_std_and_cv() -> None:
    standard_deviation = math.sqrt(8.0 / 3.0)
    analytics = PerspectiveAnalytics(
        perspective=MetricPerspective.SUBJECT,
        annual_average_loss=2.0,
        population_standard_deviation=standard_deviation,
        coefficient_of_variation=standard_deviation / 2.0,
        coefficient_status=RatioStatus.APPLICABLE,
        oep_sample=(0.0, 2.0, 3.0),
        aep_sample=(0.0, 2.0, 4.0),
        var_estimates=(TailEstimate(0.95, 4.0),),
        tvar_estimates=(TailEstimate(0.99, 4.0),),
        return_period_estimates=(TailEstimate(10.0, 4.0),),
    )
    assert analytics.annual_average_loss == 2.0
    for changes in (
        {"annual_average_loss": 2.1},
        {"population_standard_deviation": 1.0},
        {"coefficient_of_variation": 0.5},
    ):
        with pytest.raises(ValueError):
            replace(analytics, **changes)


def test_zero_mean_analytics_uses_null_cv_convention() -> None:
    analytics = PerspectiveAnalytics(
        MetricPerspective.RECOVERY_PRE_ANNUAL_CAPACITY,
        0.0,
        0.0,
        None,
        RatioStatus.NOT_APPLICABLE_ZERO_MEAN,
        (0.0, 0.0),
        (0.0, 0.0),
        (),
        (),
        (),
    )
    assert analytics.coefficient_of_variation is None
    with pytest.raises(ValueError, match="zero mean"):
        replace(analytics, coefficient_of_variation=0.0)


def test_run_identity_requires_sha256_hashes() -> None:
    identity = CT4RunIdentity("SIM-1", "a" * 64, "b" * 64, "ct4.0.0", "ct4.0")
    assert identity.input_hash == "a" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        replace(identity, result_hash="ABC")


def occurrence_row(**changes: object) -> CT4OccurrenceLedgerRow:
    assessment = evaluate_cat_xl_program(program(), source_version="ct4-model-test")
    values: dict[str, object] = {
        "annual_trial_id": 1,
        "occurrence_sequence": 1,
        "event_id": "OCC-CT3",
        "source_event_ids": ("OCC-CT3",),
        "occurrence_definition_mode": OccurrenceDefinitionMode.CATALOGUE_DEFINED,
        "elected_candidate_id": None,
        "assessment": assessment,
        "subject_loss": 45_000_000.0,
        "gross_contractual_recovery_pre_annual_capacity": 35_000_000.0,
        "insurer_net_loss_pre_annual_capacity": 10_000_000.0,
        "trace_references": ("F17", "F18", "F20"),
    }
    values.update(changes)
    return CT4OccurrenceLedgerRow(**values)


def test_occurrence_ledger_enforces_pre_capacity_identity_and_reconciliation() -> None:
    row = occurrence_row()
    assert row.gross_contractual_recovery_pre_annual_capacity == 35_000_000.0
    with pytest.raises(FrozenInstanceError):
        row.subject_loss = 0.0  # type: ignore[misc]
    for changes in (
        {"subject_loss": 44_000_000.0},
        {"gross_contractual_recovery_pre_annual_capacity": 34_000_000.0},
        {"insurer_net_loss_pre_annual_capacity": 9_000_000.0},
        {"elected_candidate_id": "W1"},
    ):
        with pytest.raises(ValueError):
            occurrence_row(**changes)


def test_hours_occurrence_ledger_requires_elected_candidate_id() -> None:
    with pytest.raises(ValueError, match="elected_candidate_id"):
        occurrence_row(
            occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        )
    row = occurrence_row(
        occurrence_definition_mode=OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING,
        elected_candidate_id="SET-1",
    )
    assert row.elected_candidate_id == "SET-1"


def test_annual_ledger_enforces_f17_f18_f20_and_common_driver() -> None:
    row = occurrence_row()
    annual = CT4AnnualLedgerRow(
        annual_trial_id=1,
        occurrence_rows=(row,),
        subject_oep=45_000_000.0,
        recovery_oep_pre_annual_capacity=35_000_000.0,
        net_oep_pre_annual_capacity=10_000_000.0,
        subject_aep=45_000_000.0,
        recovery_aep_pre_annual_capacity=35_000_000.0,
        net_aep_pre_annual_capacity=10_000_000.0,
        common_oep_driver_event_id="OCC-CT3",
        reconciliation_passed=True,
    )
    assert annual.common_oep_driver_event_id == "OCC-CT3"
    for changes in (
        {"subject_oep": 44_000_000.0},
        {"recovery_aep_pre_annual_capacity": 34_000_000.0},
        {"common_oep_driver_event_id": "OTHER"},
        {"reconciliation_passed": False},
    ):
        with pytest.raises(ValueError):
            replace(annual, **changes)


def test_empty_annual_ledger_has_six_zeros_and_null_driver() -> None:
    annual = CT4AnnualLedgerRow(
        1, (), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, None, True
    )
    assert annual.occurrence_rows == ()
    with pytest.raises(ValueError, match="null OEP driver"):
        replace(annual, common_oep_driver_event_id="OCC")
