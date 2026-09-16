"""Immutable CT5 post-capacity analytics contracts."""

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real

from cat_treaty.ct4_models import TailWarning
from cat_treaty.ct5_models import CT5MetricPerspective


class CT5RatioStatus(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE_ZERO_MEAN = "not_applicable_zero_mean"
    NOT_APPLICABLE_NEGATIVE_MEAN = "not_applicable_negative_mean"


class CT5ConditionalMetricStatus(str, Enum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE_NO_POSITIVE_PREMIUM = "not_applicable_no_positive_premium"


def _finite(name: str, value: object, *, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    if non_negative and result < 0:
        raise ValueError(f"{name} must be non-negative")
    return result


def _positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _tuple_of(name: str, values: object, item_type: type[object]) -> None:
    if not isinstance(values, tuple) or not all(
        isinstance(item, item_type) for item in values
    ):
        raise ValueError(f"{name} must contain {item_type.__name__} values")


def _close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-6)


@dataclass(frozen=True, slots=True)
class CT5TailEstimate:
    level: float
    value: float
    warnings: tuple[TailWarning, ...] = ()

    def __post_init__(self) -> None:
        level = _finite("level", self.level, non_negative=True)
        if level <= 0:
            raise ValueError("level must be greater than zero")
        _finite("value", self.value)
        _tuple_of("warnings", self.warnings, TailWarning)


@dataclass(frozen=True, slots=True)
class CT5ExceedancePoint:
    rank: int
    value: float
    exceedance_probability: float

    def __post_init__(self) -> None:
        _positive_int("rank", self.rank)
        _finite("value", self.value)
        probability = _finite(
            "exceedance_probability",
            self.exceedance_probability,
            non_negative=True,
        )
        if probability <= 0 or probability > 1:
            raise ValueError("exceedance_probability must lie in (0, 1]")


@dataclass(frozen=True, slots=True)
class CT5PerspectiveAnalytics:
    perspective: CT5MetricPerspective
    annual_average: float
    population_standard_deviation: float
    coefficient_of_variation: float | None
    coefficient_status: CT5RatioStatus
    oep_sample: tuple[float, ...]
    aep_sample: tuple[float, ...]
    oep_curve: tuple[CT5ExceedancePoint, ...]
    aep_curve: tuple[CT5ExceedancePoint, ...]
    oep_var_estimates: tuple[CT5TailEstimate, ...]
    aep_var_estimates: tuple[CT5TailEstimate, ...]
    oep_tvar_estimates: tuple[CT5TailEstimate, ...]
    aep_tvar_estimates: tuple[CT5TailEstimate, ...]
    oep_return_period_estimates: tuple[CT5TailEstimate, ...]
    aep_return_period_estimates: tuple[CT5TailEstimate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.perspective, CT5MetricPerspective):
            raise ValueError("perspective must be CT5MetricPerspective")
        mean = _finite("annual_average", self.annual_average)
        deviation = _finite(
            "population_standard_deviation",
            self.population_standard_deviation,
            non_negative=True,
        )
        if not isinstance(self.oep_sample, tuple) or not isinstance(self.aep_sample, tuple):
            raise ValueError("OEP and AEP samples must be tuples")
        if not self.aep_sample or len(self.oep_sample) != len(self.aep_sample):
            raise ValueError("OEP and AEP samples must have equal positive length")
        signed = self.perspective is CT5MetricPerspective.NET_CASH_SETTLEMENT
        for value in self.oep_sample + self.aep_sample:
            _finite("sample value", value, non_negative=not signed)
        expected_mean = math.fsum(float(value) for value in self.aep_sample) / len(self.aep_sample)
        if not _close(mean, expected_mean):
            raise ValueError("annual_average must equal AEP sample mean")
        variance = math.fsum(
            (float(value) - expected_mean) ** 2 for value in self.aep_sample
        ) / len(self.aep_sample)
        if not _close(deviation, math.sqrt(variance)):
            raise ValueError("population_standard_deviation does not reconcile")
        if not isinstance(self.coefficient_status, CT5RatioStatus):
            raise ValueError("coefficient_status must be CT5RatioStatus")
        if mean > 0:
            if self.coefficient_of_variation is None or self.coefficient_status is not CT5RatioStatus.APPLICABLE:
                raise ValueError("positive mean requires applicable coefficient")
            coefficient = _finite(
                "coefficient_of_variation",
                self.coefficient_of_variation,
                non_negative=True,
            )
            if not math.isclose(coefficient, deviation / mean, rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError("coefficient_of_variation does not reconcile")
        else:
            expected_status = (
                CT5RatioStatus.NOT_APPLICABLE_ZERO_MEAN
                if mean == 0
                else CT5RatioStatus.NOT_APPLICABLE_NEGATIVE_MEAN
            )
            if self.coefficient_of_variation is not None or self.coefficient_status is not expected_status:
                raise ValueError("non-positive mean requires null coefficient and matching status")
        for name, values, item_type in (
            ("oep_curve", self.oep_curve, CT5ExceedancePoint),
            ("aep_curve", self.aep_curve, CT5ExceedancePoint),
            ("oep_var_estimates", self.oep_var_estimates, CT5TailEstimate),
            ("aep_var_estimates", self.aep_var_estimates, CT5TailEstimate),
            ("oep_tvar_estimates", self.oep_tvar_estimates, CT5TailEstimate),
            ("aep_tvar_estimates", self.aep_tvar_estimates, CT5TailEstimate),
            ("oep_return_period_estimates", self.oep_return_period_estimates, CT5TailEstimate),
            ("aep_return_period_estimates", self.aep_return_period_estimates, CT5TailEstimate),
        ):
            _tuple_of(name, values, item_type)


@dataclass(frozen=True, slots=True)
class CT5TailAnalytics:
    perspectives: tuple[CT5PerspectiveAnalytics, ...]
    aal_reconciliation_passed: bool

    def __post_init__(self) -> None:
        _tuple_of("perspectives", self.perspectives, CT5PerspectiveAnalytics)
        if tuple(item.perspective for item in self.perspectives) != tuple(CT5MetricPerspective):
            raise ValueError("perspectives must follow the frozen six-perspective order")
        if not isinstance(self.aal_reconciliation_passed, bool) or not self.aal_reconciliation_passed:
            raise ValueError("completed analytics requires passed AAL reconciliation")
        subject, recovery, net = (
            self.perspectives[index].annual_average for index in (0, 1, 2)
        )
        if not _close(subject, recovery + net):
            raise ValueError("subject AAL must equal recovery AAL plus insurer-net AAL")


@dataclass(frozen=True, slots=True)
class CT5LayerExhaustionMetric:
    layer_id: str
    exhaustion_probability: float

    def __post_init__(self) -> None:
        if not isinstance(self.layer_id, str) or not self.layer_id.strip():
            raise ValueError("layer_id must be a non-empty string")
        probability = _finite(
            "exhaustion_probability",
            self.exhaustion_probability,
            non_negative=True,
        )
        if probability > 1:
            raise ValueError("exhaustion_probability must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class CT5OperationalAnalytics:
    probability_capacity_constrains_event: float
    average_recovery_constrained: float
    layer_exhaustion: tuple[CT5LayerExhaustionMetric, ...]
    average_reinstatements_used: float
    maximum_reinstatements_used: float
    average_reinstatement_premium_unconditional: float
    average_reinstatement_premium_conditional: float | None
    conditional_premium_status: CT5ConditionalMetricStatus

    def __post_init__(self) -> None:
        probability = _finite(
            "probability_capacity_constrains_event",
            self.probability_capacity_constrains_event,
            non_negative=True,
        )
        if probability > 1:
            raise ValueError("constraint probability must lie in [0, 1]")
        for name in (
            "average_recovery_constrained",
            "average_reinstatements_used",
            "maximum_reinstatements_used",
            "average_reinstatement_premium_unconditional",
        ):
            _finite(name, getattr(self, name), non_negative=True)
        _tuple_of("layer_exhaustion", self.layer_exhaustion, CT5LayerExhaustionMetric)
        layer_ids = tuple(item.layer_id for item in self.layer_exhaustion)
        if len(layer_ids) != len(set(layer_ids)):
            raise ValueError("layer exhaustion IDs must be unique")
        if not isinstance(self.conditional_premium_status, CT5ConditionalMetricStatus):
            raise ValueError("conditional_premium_status is invalid")
        if self.average_reinstatement_premium_conditional is None:
            if self.conditional_premium_status is not CT5ConditionalMetricStatus.NOT_APPLICABLE_NO_POSITIVE_PREMIUM:
                raise ValueError("null conditional premium requires not-applicable status")
        else:
            _finite(
                "average_reinstatement_premium_conditional",
                self.average_reinstatement_premium_conditional,
                non_negative=True,
            )
            if self.conditional_premium_status is not CT5ConditionalMetricStatus.APPLICABLE:
                raise ValueError("conditional premium value requires applicable status")


@dataclass(frozen=True, slots=True)
class CT5Analytics:
    tail: CT5TailAnalytics
    operational: CT5OperationalAnalytics

    def __post_init__(self) -> None:
        if not isinstance(self.tail, CT5TailAnalytics):
            raise ValueError("tail must be CT5TailAnalytics")
        if not isinstance(self.operational, CT5OperationalAnalytics):
            raise ValueError("operational must be CT5OperationalAnalytics")
