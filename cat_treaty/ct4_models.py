"""Immutable CT4 catalogue, hours-clause, and analytics domain contracts."""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real
import re

from cat_treaty.ct3_models import CT3AssessmentResult, CT3ProgramInput


_SHA256 = re.compile(r"[0-9a-f]{64}")


class OccurrenceDefinitionMode(str, Enum):
    CATALOGUE_DEFINED = "catalogue_defined"
    HOURS_CLAUSE_TEACHING = "hours_clause_teaching"


class HoursElectionMethod(str, Enum):
    EARLIEST_VALID_WINDOW = "earliest_valid_window"
    MAXIMUM_SUBJECT_LOSS = "maximum_subject_loss"
    MAXIMUM_CONTRACTUAL_RECOVERY = "maximum_contractual_recovery"
    MANUAL = "manual"


class CandidateAdmissibility(str, Enum):
    VALID = "valid"
    EXCLUDED = "excluded"


class HoursExclusionCode(str, Enum):
    OUTSIDE_HOURS_DURATION = "outside_hours_duration"
    OUTSIDE_TREATY_TERM = "outside_treaty_term"
    PERIL_OR_CAUSE_MISMATCH = "peril_or_cause_mismatch"
    GEOGRAPHIC_MISMATCH = "geographic_mismatch"
    CAUSAL_LINK_FAILURE = "causal_link_failure"
    DUPLICATE_COMPONENT = "duplicate_component"
    OVERLAPPING_WINDOWS = "overlapping_windows"
    MANUAL_SELECTION_INVALID = "manual_selection_invalid"


class HoursElectionStatus(str, Enum):
    SELECTED = "selected"
    BLOCKED = "blocked"


class HoursElectionIssueCode(str, Enum):
    MANUAL_SELECTION_INVALID = "manual_selection_invalid"
    NO_VALID_CANDIDATE_SET = "no_valid_candidate_set"
    PROGRAM_GEOMETRY_BLOCKED = "program_geometry_blocked"


class MetricPerspective(str, Enum):
    SUBJECT = "subject"
    RECOVERY_PRE_ANNUAL_CAPACITY = "recovery_pre_annual_capacity"
    INSURER_NET_PRE_ANNUAL_CAPACITY = "insurer_net_pre_annual_capacity"


class TailWarningCode(str, Enum):
    LIMITED_TAIL_CREDIBILITY = "limited_tail_credibility"
    SEVERE_TAIL_CREDIBILITY_WARNING = "severe_tail_credibility_warning"
    RETURN_PERIOD_EXCEEDS_SAMPLE = "return_period_exceeds_sample"


class RatioStatus(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE_ZERO_MEAN = "not_applicable_zero_mean"
    NOT_APPLICABLE_NO_OCCURRENCES = "not_applicable_no_occurrences"


class PreflightIssueCode(str, Enum):
    UNSUPPORTED_OCCURRENCE_MODE = "unsupported_occurrence_mode"
    BLOCKED_PROGRAM_GEOMETRY = "blocked_program_geometry"


def _nonblank(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _finite(name: str, value: object, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if result < 0 or (positive and result <= 0):
        qualifier = "greater than zero" if positive else "non-negative"
        raise ValueError(f"{name} must be {qualifier}")
    return result


def _positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _enum(name: str, value: object, enum_type: type[Enum]) -> None:
    if not isinstance(value, enum_type):
        raise ValueError(f"{name} must be a supported {enum_type.__name__}")


def _strings(name: str, values: object, *, allow_empty: bool = True) -> None:
    if (
        not isinstance(values, tuple)
        or (not allow_empty and not values)
        or not all(isinstance(item, str) and item.strip() for item in values)
    ):
        raise ValueError(f"{name} must contain non-empty strings")


def _unique(name: str, values: tuple[object, ...]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{name} values must be unique")


def _program_terms(program: CT3ProgramInput) -> tuple[object, ...]:
    layers = tuple(
        sorted(
            (
                layer.layer_id,
                float(layer.attachment),
                float(layer.occurrence_limit),
                float(layer.ceded_share),
                float(layer.placement_share),
                layer.currency,
            )
            for layer in program.layers
        )
    )
    return (
        program.program_id,
        layers,
        program.intentional_gap_acknowledged,
        program.overlap_coordination.value,
        program.priority_order,
    )


@dataclass(frozen=True, slots=True)
class NumericalToleranceProfile:
    relative_tolerance: float = 1e-12
    absolute_currency_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        _finite("relative_tolerance", self.relative_tolerance, positive=True)
        _finite(
            "absolute_currency_tolerance",
            self.absolute_currency_tolerance,
            positive=True,
        )


@dataclass(frozen=True, slots=True)
class TailConfiguration:
    probability_levels: tuple[float, ...] = (0.95, 0.99, 0.995)
    tvar_levels: tuple[float, ...] = (0.99,)
    return_periods: tuple[float, ...] = (2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0)

    def __post_init__(self) -> None:
        for name, values in (
            ("probability_levels", self.probability_levels),
            ("tvar_levels", self.tvar_levels),
            ("return_periods", self.return_periods),
        ):
            if not isinstance(values, tuple) or not values:
                raise ValueError(f"{name} must be a non-empty tuple")
            _unique(name, values)
        for value in self.probability_levels + self.tvar_levels:
            number = _finite("probability level", value, positive=True)
            if number >= 1:
                raise ValueError("probability levels must lie in (0, 1)")
        for value in self.return_periods:
            if _finite("return period", value, positive=True) <= 1:
                raise ValueError("return periods must be greater than one")


@dataclass(frozen=True, slots=True)
class CT4OccurrenceInput:
    annual_trial_id: int
    event_id: str
    event_time: float
    event_sequence: int
    peril: str
    region: str
    program_input: CT3ProgramInput
    source_reference: str
    trace_reference: str

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _nonblank("event_id", self.event_id)
        _finite("event_time", self.event_time)
        _positive_int("event_sequence", self.event_sequence)
        for name in ("peril", "region", "source_reference", "trace_reference"):
            _nonblank(name, getattr(self, name))
        if not isinstance(self.program_input, CT3ProgramInput):
            raise ValueError("program_input must be CT3ProgramInput")
        occurrence_id = self.program_input.ct2_result.loss_basis.basis_input.occurrence_id
        if self.event_id != occurrence_id:
            raise ValueError("event_id must match the CT2 occurrence ID")


@dataclass(frozen=True, slots=True)
class CT4AnnualTrialInput:
    annual_trial_id: int
    catalogue_source_id: str
    occurrences: tuple[CT4OccurrenceInput, ...] = ()

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _nonblank("catalogue_source_id", self.catalogue_source_id)
        if not isinstance(self.occurrences, tuple) or not all(
            isinstance(item, CT4OccurrenceInput) for item in self.occurrences
        ):
            raise ValueError("occurrences must contain CT4OccurrenceInput values")
        if any(item.annual_trial_id != self.annual_trial_id for item in self.occurrences):
            raise ValueError("occurrence annual_trial_id must match its trial")
        ids = tuple(item.event_id for item in self.occurrences)
        _unique("event_id", ids)


@dataclass(frozen=True, slots=True)
class HoursLossComponent:
    component_id: str
    subject_loss: float
    timestamp: float
    peril: str
    region: str
    causal_event_id: str
    source_reference: str

    def __post_init__(self) -> None:
        _nonblank("component_id", self.component_id)
        _finite("subject_loss", self.subject_loss)
        _finite("timestamp", self.timestamp)
        for name in ("peril", "region", "causal_event_id", "source_reference"):
            _nonblank(name, getattr(self, name))


@dataclass(frozen=True, slots=True)
class HoursClauseTerms:
    treaty_term_start: float
    treaty_term_end: float
    hours_duration: float
    permitted_perils: tuple[str, ...]
    permitted_regions: tuple[str, ...]
    causal_link_required: bool
    authorized_election_methods: tuple[HoursElectionMethod, ...]
    selected_election_method: HoursElectionMethod
    manual_candidate_set_id: str | None
    rule_reference: str

    def __post_init__(self) -> None:
        start = _finite("treaty_term_start", self.treaty_term_start)
        end = _finite("treaty_term_end", self.treaty_term_end, positive=True)
        if end <= start:
            raise ValueError("treaty term end must exceed start")
        _finite("hours_duration", self.hours_duration, positive=True)
        _strings("permitted_perils", self.permitted_perils, allow_empty=False)
        _strings("permitted_regions", self.permitted_regions, allow_empty=False)
        _unique("permitted_perils", self.permitted_perils)
        _unique("permitted_regions", self.permitted_regions)
        if not isinstance(self.causal_link_required, bool):
            raise ValueError("causal_link_required must be boolean")
        if not isinstance(self.authorized_election_methods, tuple) or not self.authorized_election_methods or not all(
            isinstance(item, HoursElectionMethod) for item in self.authorized_election_methods
        ):
            raise ValueError("authorized_election_methods must contain supported methods")
        _unique("authorized_election_methods", self.authorized_election_methods)
        _enum("selected_election_method", self.selected_election_method, HoursElectionMethod)
        if self.selected_election_method not in self.authorized_election_methods:
            raise ValueError("selected election method is not contractually authorized")
        if self.selected_election_method is HoursElectionMethod.MANUAL:
            _nonblank("manual_candidate_set_id", self.manual_candidate_set_id)
        elif self.manual_candidate_set_id is not None:
            raise ValueError("manual_candidate_set_id requires manual election")
        _nonblank("rule_reference", self.rule_reference)


@dataclass(frozen=True, slots=True)
class HoursClauseScenario:
    scenario_id: str
    components: tuple[HoursLossComponent, ...]
    terms: HoursClauseTerms
    program_terms_source: CT3ProgramInput
    source_reference: str

    def __post_init__(self) -> None:
        _nonblank("scenario_id", self.scenario_id)
        if not isinstance(self.components, tuple) or not all(
            isinstance(item, HoursLossComponent) for item in self.components
        ):
            raise ValueError("components must contain HoursLossComponent values")
        if not 1 <= len(self.components) <= 12:
            raise ValueError("hours-clause teaching requires one to twelve components")
        _unique("component_id", tuple(item.component_id for item in self.components))
        if not isinstance(self.terms, HoursClauseTerms):
            raise ValueError("terms must be HoursClauseTerms")
        if not isinstance(self.program_terms_source, CT3ProgramInput):
            raise ValueError("program_terms_source must be CT3ProgramInput")
        currency = self.program_terms_source.ct2_result.loss_basis.basis_input.reporting_currency
        if any(layer.currency != currency for layer in self.program_terms_source.layers):
            raise ValueError("program terms currency must be consistent")
        _nonblank("source_reference", self.source_reference)


@dataclass(frozen=True, slots=True)
class CT4SimulationInput:
    simulation_id: str
    trial_count: int
    trials: tuple[CT4AnnualTrialInput, ...]
    catalogue_version: str
    source_version: str
    simulation_seed: int | None
    occurrence_definition_mode: OccurrenceDefinitionMode
    tail_configuration: TailConfiguration
    tolerance_profile: NumericalToleranceProfile
    hours_clause_scenario: HoursClauseScenario | None = None
    description: str = "CT4 simulation"
    source_reference: str = "CT4"
    rule_reference: str = "CT4-v1.1"

    def __post_init__(self) -> None:
        _nonblank("simulation_id", self.simulation_id)
        _positive_int("trial_count", self.trial_count)
        if not isinstance(self.trials, tuple) or not all(
            isinstance(item, CT4AnnualTrialInput) for item in self.trials
        ):
            raise ValueError("trials must contain CT4AnnualTrialInput values")
        trial_ids = tuple(item.annual_trial_id for item in self.trials)
        if trial_ids != tuple(range(1, self.trial_count + 1)):
            raise ValueError("trial IDs must be contiguous from 1 through trial_count")
        for name in ("catalogue_version", "source_version", "description", "source_reference", "rule_reference"):
            _nonblank(name, getattr(self, name))
        if self.simulation_seed is not None and (
            isinstance(self.simulation_seed, bool)
            or not isinstance(self.simulation_seed, int)
            or self.simulation_seed < 0
        ):
            raise ValueError("simulation_seed must be a non-negative integer or null")
        _enum("occurrence_definition_mode", self.occurrence_definition_mode, OccurrenceDefinitionMode)
        if not isinstance(self.tail_configuration, TailConfiguration):
            raise ValueError("tail_configuration must be TailConfiguration")
        if not isinstance(self.tolerance_profile, NumericalToleranceProfile):
            raise ValueError("tolerance_profile must be NumericalToleranceProfile")
        self._validate_mode()
        self._validate_occurrence_population()

    def _validate_mode(self) -> None:
        if self.occurrence_definition_mode is OccurrenceDefinitionMode.CATALOGUE_DEFINED:
            if self.hours_clause_scenario is not None:
                raise ValueError("catalogue mode forbids hours_clause_scenario")
        else:
            if self.trial_count != 1:
                raise ValueError("hours-clause teaching requires trial_count = 1")
            if not isinstance(self.hours_clause_scenario, HoursClauseScenario):
                raise ValueError("hours-clause teaching requires hours_clause_scenario")
            if any(trial.occurrences for trial in self.trials):
                raise ValueError("hours-clause teaching cannot mix catalogue occurrences")

    def _validate_occurrence_population(self) -> None:
        occurrences = tuple(item for trial in self.trials for item in trial.occurrences)
        event_ids = tuple(item.event_id for item in occurrences)
        _unique("event_id", event_ids)
        if occurrences:
            signature = _program_terms(occurrences[0].program_input)
            if any(_program_terms(item.program_input) != signature for item in occurrences[1:]):
                raise ValueError("every occurrence must use one fixed program-term fingerprint")


@dataclass(frozen=True, slots=True)
class CT4OccurrenceLedgerRow:
    annual_trial_id: int
    occurrence_sequence: int
    event_id: str
    source_event_ids: tuple[str, ...]
    occurrence_definition_mode: OccurrenceDefinitionMode
    elected_candidate_id: str | None
    assessment: CT3AssessmentResult
    subject_loss: float
    gross_contractual_recovery_pre_annual_capacity: float
    insurer_net_loss_pre_annual_capacity: float
    trace_references: tuple[str, ...]

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        _positive_int("occurrence_sequence", self.occurrence_sequence)
        _nonblank("event_id", self.event_id)
        _strings("source_event_ids", self.source_event_ids, allow_empty=False)
        _unique("source_event_ids", self.source_event_ids)
        _enum("occurrence_definition_mode", self.occurrence_definition_mode, OccurrenceDefinitionMode)
        if self.occurrence_definition_mode is OccurrenceDefinitionMode.HOURS_CLAUSE_TEACHING:
            _nonblank("elected_candidate_id", self.elected_candidate_id)
        elif self.elected_candidate_id is not None:
            raise ValueError("catalogue-defined occurrence forbids elected_candidate_id")
        if not isinstance(self.assessment, CT3AssessmentResult) or self.assessment.program_result is None:
            raise ValueError("occurrence ledger requires an eligible completed CT3 assessment")
        result = self.assessment.program_result
        basis = result.program_input.ct2_result.loss_basis.basis_input
        if self.event_id != basis.occurrence_id:
            raise ValueError("event_id must match completed CT3 occurrence")
        subject = _finite("subject_loss", self.subject_loss)
        recovery = _finite(
            "gross_contractual_recovery_pre_annual_capacity",
            self.gross_contractual_recovery_pre_annual_capacity,
        )
        net = _finite(
            "insurer_net_loss_pre_annual_capacity",
            self.insurer_net_loss_pre_annual_capacity,
        )
        if not math.isclose(subject, result.program_input.ct2_result.cat_xl_subject_loss, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("subject_loss does not match CT3 result")
        if not math.isclose(recovery, result.total_gross_contractual_recovery, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("pre-annual-capacity recovery does not match CT3 result")
        if not math.isclose(net, result.insurer_net_loss, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("insurer net loss does not match CT3 result")
        if not math.isclose(subject, recovery + net, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("occurrence subject, recovery and net do not reconcile")
        _strings("trace_references", self.trace_references, allow_empty=False)


@dataclass(frozen=True, slots=True)
class CT4AnnualLedgerRow:
    annual_trial_id: int
    occurrence_rows: tuple[CT4OccurrenceLedgerRow, ...]
    subject_oep: float
    recovery_oep_pre_annual_capacity: float
    net_oep_pre_annual_capacity: float
    subject_aep: float
    recovery_aep_pre_annual_capacity: float
    net_aep_pre_annual_capacity: float
    common_oep_driver_event_id: str | None
    reconciliation_passed: bool

    def __post_init__(self) -> None:
        _positive_int("annual_trial_id", self.annual_trial_id)
        if not isinstance(self.occurrence_rows, tuple) or not all(
            isinstance(item, CT4OccurrenceLedgerRow) for item in self.occurrence_rows
        ):
            raise ValueError("occurrence_rows must contain CT4OccurrenceLedgerRow values")
        if any(item.annual_trial_id != self.annual_trial_id for item in self.occurrence_rows):
            raise ValueError("occurrence row trial IDs must match annual trial")
        sequences = tuple(item.occurrence_sequence for item in self.occurrence_rows)
        if sequences != tuple(range(1, len(sequences) + 1)):
            raise ValueError("occurrence ledger sequence must be contiguous from 1")
        values = tuple(
            _finite(name, getattr(self, name))
            for name in (
                "subject_oep",
                "recovery_oep_pre_annual_capacity",
                "net_oep_pre_annual_capacity",
                "subject_aep",
                "recovery_aep_pre_annual_capacity",
                "net_aep_pre_annual_capacity",
            )
        )
        subject_oep, recovery_oep, net_oep, subject_aep, recovery_aep, net_aep = values
        expected_subject_oep = max((item.subject_loss for item in self.occurrence_rows), default=0.0)
        expected_recovery_oep = max((item.gross_contractual_recovery_pre_annual_capacity for item in self.occurrence_rows), default=0.0)
        expected_net_oep = max((item.insurer_net_loss_pre_annual_capacity for item in self.occurrence_rows), default=0.0)
        expected_subject_aep = math.fsum(item.subject_loss for item in self.occurrence_rows)
        expected_recovery_aep = math.fsum(item.gross_contractual_recovery_pre_annual_capacity for item in self.occurrence_rows)
        expected_net_aep = math.fsum(item.insurer_net_loss_pre_annual_capacity for item in self.occurrence_rows)
        for actual, expected, name in (
            (subject_oep, expected_subject_oep, "subject_oep"),
            (recovery_oep, expected_recovery_oep, "recovery_oep"),
            (net_oep, expected_net_oep, "net_oep"),
            (subject_aep, expected_subject_aep, "subject_aep"),
            (recovery_aep, expected_recovery_aep, "recovery_aep"),
            (net_aep, expected_net_aep, "net_aep"),
        ):
            if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-6):
                raise ValueError(f"{name} does not reconcile")
        if self.occurrence_rows:
            driver = min(
                self.occurrence_rows,
                key=lambda item: (-item.subject_loss, item.occurrence_sequence, item.event_id),
            )
            if self.common_oep_driver_event_id != driver.event_id:
                raise ValueError("common OEP driver does not match F17 tie-break")
            if (
                driver.gross_contractual_recovery_pre_annual_capacity != expected_recovery_oep
                or driver.insurer_net_loss_pre_annual_capacity != expected_net_oep
            ):
                raise ValueError("F17 common-driver monotonicity invariant failed")
        elif self.common_oep_driver_event_id is not None:
            raise ValueError("empty trial must have null OEP driver")
        if not isinstance(self.reconciliation_passed, bool) or not self.reconciliation_passed:
            raise ValueError("completed annual row requires passed F20 reconciliation")
        if not math.isclose(subject_aep, recovery_aep + net_aep, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("F20 annual reconciliation failed")


@dataclass(frozen=True, slots=True)
class CT4PreflightIssue:
    code: PreflightIssueCode
    annual_trial_id: int | None
    event_id: str | None
    message: str
    trace_reference: str

    def __post_init__(self) -> None:
        _enum("code", self.code, PreflightIssueCode)
        if self.annual_trial_id is not None:
            _positive_int("annual_trial_id", self.annual_trial_id)
        if self.event_id is not None:
            _nonblank("event_id", self.event_id)
        _nonblank("message", self.message)
        _nonblank("trace_reference", self.trace_reference)


@dataclass(frozen=True, slots=True)
class CT4CatalogueResult:
    simulation_input: CT4SimulationInput
    occurrence_rows: tuple[CT4OccurrenceLedgerRow, ...]
    annual_rows: tuple[CT4AnnualLedgerRow, ...]
    preflight_passed: bool

    def __post_init__(self) -> None:
        if not isinstance(self.simulation_input, CT4SimulationInput):
            raise ValueError("simulation_input must be CT4SimulationInput")
        if self.simulation_input.occurrence_definition_mode is not OccurrenceDefinitionMode.CATALOGUE_DEFINED:
            raise ValueError("catalogue result requires catalogue-defined mode")
        if not isinstance(self.occurrence_rows, tuple) or not all(
            isinstance(item, CT4OccurrenceLedgerRow) for item in self.occurrence_rows
        ):
            raise ValueError("occurrence_rows must contain CT4OccurrenceLedgerRow values")
        if not isinstance(self.annual_rows, tuple) or not all(
            isinstance(item, CT4AnnualLedgerRow) for item in self.annual_rows
        ):
            raise ValueError("annual_rows must contain CT4AnnualLedgerRow values")
        if not isinstance(self.preflight_passed, bool) or not self.preflight_passed:
            raise ValueError("completed catalogue result requires passed preflight")
        expected_ids = tuple(range(1, self.simulation_input.trial_count + 1))
        if tuple(item.annual_trial_id for item in self.annual_rows) != expected_ids:
            raise ValueError("annual rows must preserve every trial in contiguous order")
        flattened = tuple(
            occurrence
            for annual in self.annual_rows
            for occurrence in annual.occurrence_rows
        )
        if self.occurrence_rows != flattened:
            raise ValueError("occurrence_rows must equal the ordered annual-ledger rows")


@dataclass(frozen=True, slots=True)
class HoursCandidateWindow:
    candidate_id: str
    start: float
    end: float
    component_ids: tuple[str, ...]
    subject_loss: float
    admissibility: CandidateAdmissibility
    exclusion_codes: tuple[HoursExclusionCode, ...]
    exclusion_reasons: tuple[str, ...]
    affected_ids: tuple[str, ...]
    rule_reference: str

    def __post_init__(self) -> None:
        _nonblank("candidate_id", self.candidate_id)
        start = _finite("start", self.start)
        end = _finite("end", self.end)
        if end <= start:
            raise ValueError("candidate end must exceed start")
        _strings("component_ids", self.component_ids, allow_empty=False)
        _unique("component_ids", self.component_ids)
        _finite("subject_loss", self.subject_loss)
        _enum("admissibility", self.admissibility, CandidateAdmissibility)
        if not isinstance(self.exclusion_codes, tuple) or not all(
            isinstance(item, HoursExclusionCode) for item in self.exclusion_codes
        ):
            raise ValueError("exclusion_codes must contain HoursExclusionCode values")
        _unique("exclusion_codes", self.exclusion_codes)
        _strings("exclusion_reasons", self.exclusion_reasons)
        _strings("affected_ids", self.affected_ids)
        _nonblank("rule_reference", self.rule_reference)
        excluded = self.admissibility is CandidateAdmissibility.EXCLUDED
        if excluded != bool(self.exclusion_codes) or excluded != bool(self.exclusion_reasons):
            raise ValueError("admissibility must match exclusion codes and reasons")


@dataclass(frozen=True, slots=True)
class HoursCandidateSet:
    candidate_set_id: str
    window_ids: tuple[str, ...]
    total_subject_loss: float
    total_contractual_recovery: float | None
    admissibility: CandidateAdmissibility
    exclusion_codes: tuple[HoursExclusionCode, ...]
    exclusion_reasons: tuple[str, ...]
    affected_ids: tuple[str, ...] = ()
    rule_reference: str = "CT4-section-8"

    def __post_init__(self) -> None:
        _nonblank("candidate_set_id", self.candidate_set_id)
        _strings("window_ids", self.window_ids, allow_empty=False)
        _unique("window_ids", self.window_ids)
        _finite("total_subject_loss", self.total_subject_loss)
        if self.total_contractual_recovery is not None:
            _finite("total_contractual_recovery", self.total_contractual_recovery)
        _enum("admissibility", self.admissibility, CandidateAdmissibility)
        if not isinstance(self.exclusion_codes, tuple) or not all(
            isinstance(item, HoursExclusionCode) for item in self.exclusion_codes
        ):
            raise ValueError("exclusion_codes must contain HoursExclusionCode values")
        _unique("exclusion_codes", self.exclusion_codes)
        _strings("exclusion_reasons", self.exclusion_reasons)
        _strings("affected_ids", self.affected_ids)
        _nonblank("rule_reference", self.rule_reference)
        excluded = self.admissibility is CandidateAdmissibility.EXCLUDED
        if excluded != bool(self.exclusion_codes) or excluded != bool(self.exclusion_reasons):
            raise ValueError("admissibility must match exclusion evidence")
        if not excluded and self.total_contractual_recovery is None:
            raise ValueError("valid candidate set requires contractual recovery")


@dataclass(frozen=True, slots=True)
class HoursElectionIssue:
    code: HoursElectionIssueCode
    candidate_set_id: str | None
    message: str
    affected_ids: tuple[str, ...]
    rule_reference: str

    def __post_init__(self) -> None:
        _enum("code", self.code, HoursElectionIssueCode)
        if self.candidate_set_id is not None:
            _nonblank("candidate_set_id", self.candidate_set_id)
        _nonblank("message", self.message)
        _strings("affected_ids", self.affected_ids)
        _nonblank("rule_reference", self.rule_reference)


@dataclass(frozen=True, slots=True)
class HoursClauseResult:
    scenario: HoursClauseScenario
    candidate_windows: tuple[HoursCandidateWindow, ...]
    candidate_sets: tuple[HoursCandidateSet, ...]
    election_status: HoursElectionStatus
    selected_election_method: HoursElectionMethod
    selected_candidate_set_id: str | None
    valid_candidate_set_ids: tuple[str, ...]
    selected_occurrence_rows: tuple[CT4OccurrenceLedgerRow, ...]
    annual_row: CT4AnnualLedgerRow | None
    election_issues: tuple[HoursElectionIssue, ...]
    tie_break_facts: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.scenario, HoursClauseScenario):
            raise ValueError("scenario must be HoursClauseScenario")
        if not isinstance(self.candidate_windows, tuple) or not all(
            isinstance(item, HoursCandidateWindow) for item in self.candidate_windows
        ):
            raise ValueError("candidate_windows must contain HoursCandidateWindow values")
        if not isinstance(self.candidate_sets, tuple) or not all(
            isinstance(item, HoursCandidateSet) for item in self.candidate_sets
        ):
            raise ValueError("candidate_sets must contain HoursCandidateSet values")
        _unique("candidate window ID", tuple(item.candidate_id for item in self.candidate_windows))
        _unique("candidate set ID", tuple(item.candidate_set_id for item in self.candidate_sets))
        _enum("election_status", self.election_status, HoursElectionStatus)
        _enum("selected_election_method", self.selected_election_method, HoursElectionMethod)
        _strings("valid_candidate_set_ids", self.valid_candidate_set_ids)
        expected_valid = tuple(
            item.candidate_set_id
            for item in self.candidate_sets
            if item.admissibility is CandidateAdmissibility.VALID
        )
        if self.valid_candidate_set_ids != expected_valid:
            raise ValueError("valid_candidate_set_ids must identify every valid generated set")
        if not isinstance(self.selected_occurrence_rows, tuple) or not all(
            isinstance(item, CT4OccurrenceLedgerRow) for item in self.selected_occurrence_rows
        ):
            raise ValueError("selected_occurrence_rows must contain CT4OccurrenceLedgerRow values")
        if not isinstance(self.election_issues, tuple) or not all(
            isinstance(item, HoursElectionIssue) for item in self.election_issues
        ):
            raise ValueError("election_issues must contain HoursElectionIssue values")
        _strings("tie_break_facts", self.tie_break_facts)
        if self.election_status is HoursElectionStatus.SELECTED:
            _nonblank("selected_candidate_set_id", self.selected_candidate_set_id)
            if self.selected_candidate_set_id not in self.valid_candidate_set_ids:
                raise ValueError("selected candidate set must be valid")
            if not self.selected_occurrence_rows or not isinstance(self.annual_row, CT4AnnualLedgerRow):
                raise ValueError("selected election requires occurrence and annual ledgers")
            if self.election_issues:
                raise ValueError("selected election cannot contain blocking issues")
        else:
            if self.selected_candidate_set_id is not None or self.selected_occurrence_rows or self.annual_row is not None:
                raise ValueError("blocked election cannot contain selected results")
            if not self.election_issues:
                raise ValueError("blocked election requires structured issues")


@dataclass(frozen=True, slots=True)
class TailWarning:
    code: TailWarningCode
    return_period: float
    observations_per_return_period: float
    message: str

    def __post_init__(self) -> None:
        _enum("code", self.code, TailWarningCode)
        if _finite("return_period", self.return_period, positive=True) <= 1:
            raise ValueError("return_period must exceed one")
        _finite("observations_per_return_period", self.observations_per_return_period)
        _nonblank("message", self.message)


@dataclass(frozen=True, slots=True)
class TailEstimate:
    level: float
    value: float
    warnings: tuple[TailWarning, ...] = ()

    def __post_init__(self) -> None:
        _finite("level", self.level, positive=True)
        _finite("value", self.value)
        if not isinstance(self.warnings, tuple) or not all(
            isinstance(item, TailWarning) for item in self.warnings
        ):
            raise ValueError("warnings must contain TailWarning values")


@dataclass(frozen=True, slots=True)
class EmpiricalExceedancePoint:
    rank: int
    loss: float
    exceedance_probability: float

    def __post_init__(self) -> None:
        _positive_int("rank", self.rank)
        _finite("loss", self.loss)
        probability = _finite(
            "exceedance_probability",
            self.exceedance_probability,
            positive=True,
        )
        if probability > 1:
            raise ValueError("exceedance_probability must not exceed one")


@dataclass(frozen=True, slots=True)
class PerspectiveAnalytics:
    perspective: MetricPerspective
    annual_average_loss: float
    population_standard_deviation: float
    coefficient_of_variation: float | None
    coefficient_status: RatioStatus
    oep_sample: tuple[float, ...]
    aep_sample: tuple[float, ...]
    var_estimates: tuple[TailEstimate, ...]
    tvar_estimates: tuple[TailEstimate, ...]
    return_period_estimates: tuple[TailEstimate, ...]
    oep_curve: tuple[EmpiricalExceedancePoint, ...] = ()
    aep_curve: tuple[EmpiricalExceedancePoint, ...] = ()
    oep_return_period_estimates: tuple[TailEstimate, ...] = ()
    aep_return_period_estimates: tuple[TailEstimate, ...] = ()
    oep_var_estimates: tuple[TailEstimate, ...] = ()
    aep_var_estimates: tuple[TailEstimate, ...] = ()
    oep_tvar_estimates: tuple[TailEstimate, ...] = ()
    aep_tvar_estimates: tuple[TailEstimate, ...] = ()
    formula_references: tuple[str, ...] = ("F19", "F21", "F22", "F23", "F24")

    def __post_init__(self) -> None:
        _enum("perspective", self.perspective, MetricPerspective)
        mean = _finite("annual_average_loss", self.annual_average_loss)
        _finite("population_standard_deviation", self.population_standard_deviation)
        if not isinstance(self.oep_sample, tuple) or not isinstance(self.aep_sample, tuple):
            raise ValueError("OEP and AEP samples must be tuples")
        if len(self.oep_sample) != len(self.aep_sample) or not self.oep_sample:
            raise ValueError("OEP and AEP samples must have equal positive length")
        for value in self.oep_sample + self.aep_sample:
            _finite("annual sample value", value)
        expected_mean = math.fsum(float(value) for value in self.aep_sample) / len(self.aep_sample)
        if not math.isclose(mean, expected_mean, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("annual_average_loss must equal the AEP sample mean")
        expected_variance = math.fsum(
            (float(value) - expected_mean) ** 2 for value in self.aep_sample
        ) / len(self.aep_sample)
        expected_standard_deviation = math.sqrt(expected_variance)
        if not math.isclose(
            float(self.population_standard_deviation),
            expected_standard_deviation,
            rel_tol=1e-12,
            abs_tol=1e-6,
        ):
            raise ValueError("population_standard_deviation does not reconcile")
        _enum("coefficient_status", self.coefficient_status, RatioStatus)
        if mean == 0:
            if self.coefficient_of_variation is not None or self.coefficient_status is not RatioStatus.NOT_APPLICABLE_ZERO_MEAN:
                raise ValueError("zero mean requires null CV and zero-mean status")
        else:
            coefficient = _finite("coefficient_of_variation", self.coefficient_of_variation)
            if self.coefficient_status is not RatioStatus.APPLICABLE:
                raise ValueError("positive mean requires applicable CV status")
            if not math.isclose(
                coefficient,
                expected_standard_deviation / expected_mean,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise ValueError("coefficient_of_variation does not reconcile")
        for name, values in (
            ("var_estimates", self.var_estimates),
            ("tvar_estimates", self.tvar_estimates),
            ("return_period_estimates", self.return_period_estimates),
            ("oep_return_period_estimates", self.oep_return_period_estimates),
            ("aep_return_period_estimates", self.aep_return_period_estimates),
            ("oep_var_estimates", self.oep_var_estimates),
            ("aep_var_estimates", self.aep_var_estimates),
            ("oep_tvar_estimates", self.oep_tvar_estimates),
            ("aep_tvar_estimates", self.aep_tvar_estimates),
        ):
            if not isinstance(values, tuple) or not all(isinstance(item, TailEstimate) for item in values):
                raise ValueError(f"{name} must contain TailEstimate values")
        for name, curve, sample in (
            ("oep_curve", self.oep_curve, self.oep_sample),
            ("aep_curve", self.aep_curve, self.aep_sample),
        ):
            if not isinstance(curve, tuple) or not all(
                isinstance(item, EmpiricalExceedancePoint) for item in curve
            ):
                raise ValueError(f"{name} must contain EmpiricalExceedancePoint values")
            if curve:
                expected_losses = tuple(sorted((float(value) for value in sample), reverse=True))
                if tuple(item.rank for item in curve) != tuple(range(1, len(sample) + 1)):
                    raise ValueError(f"{name} ranks must be contiguous from one")
                if tuple(item.loss for item in curve) != expected_losses:
                    raise ValueError(f"{name} losses must be the descending empirical sample")
                expected_probabilities = tuple(
                    rank / len(sample) for rank in range(1, len(sample) + 1)
                )
                if tuple(item.exceedance_probability for item in curve) != expected_probabilities:
                    raise ValueError(f"{name} must use the frozen r/Y plotting position")
        _strings("formula_references", self.formula_references, allow_empty=False)


@dataclass(frozen=True, slots=True)
class CT4TailAnalytics:
    perspectives: tuple[PerspectiveAnalytics, ...]
    aal_reconciliation_passed: bool
    formula_references: tuple[str, ...] = ("F19", "F20", "F21", "F22", "F23", "F24")

    def __post_init__(self) -> None:
        if not isinstance(self.perspectives, tuple) or not all(
            isinstance(item, PerspectiveAnalytics) for item in self.perspectives
        ):
            raise ValueError("perspectives must contain PerspectiveAnalytics values")
        expected = (
            MetricPerspective.SUBJECT,
            MetricPerspective.RECOVERY_PRE_ANNUAL_CAPACITY,
            MetricPerspective.INSURER_NET_PRE_ANNUAL_CAPACITY,
        )
        if tuple(item.perspective for item in self.perspectives) != expected:
            raise ValueError("perspectives must contain subject, recovery and net in frozen order")
        if not isinstance(self.aal_reconciliation_passed, bool) or not self.aal_reconciliation_passed:
            raise ValueError("completed tail analytics requires passed AAL reconciliation")
        subject, recovery, net = (
            item.annual_average_loss for item in self.perspectives
        )
        if not math.isclose(subject, recovery + net, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("F20 AAL reconciliation failed")
        _strings("formula_references", self.formula_references, allow_empty=False)


@dataclass(frozen=True, slots=True)
class CT4RunIdentity:
    simulation_id: str
    input_hash: str
    result_hash: str
    engine_version: str
    schema_version: str

    def __post_init__(self) -> None:
        for name in ("simulation_id", "engine_version", "schema_version"):
            _nonblank(name, getattr(self, name))
        for name in ("input_hash", "result_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise ValueError(f"{name} must be lowercase SHA-256 hex")
