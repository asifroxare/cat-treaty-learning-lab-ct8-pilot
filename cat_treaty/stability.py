"""Frozen CT4 discrete reference generator and stability acceptance gate."""

from dataclasses import dataclass
from functools import lru_cache
import math
import random

from cat_treaty.tail import empirical_tvar, nearest_rank_quantile


REFERENCE_GENERATOR_ID = "ct4_discrete_reference_v1"
REFERENCE_BASELINE_TRIALS = 500_000
REFERENCE_BASELINE_SEED = 20_260_915
REFERENCE_CANDIDATE_TRIALS = (25_000, 100_000)
REFERENCE_SEEDS = (11, 29, 47, 71, 101)


@dataclass(frozen=True, slots=True)
class ReferenceMetrics:
    trial_count: int
    seed: int
    recovery_aal: float
    annual_attachment_frequency: float
    recovery_oep_10: float
    recovery_oep_20: float
    recovery_aep_10: float
    recovery_aep_20: float
    recovery_aep_tvar_99: float


@dataclass(frozen=True, slots=True)
class StabilityComparison:
    metric: str
    trial_count: int
    seed: int
    baseline: float
    candidate: float
    difference: float
    tolerance: float
    basis: str
    passed: bool


@dataclass(frozen=True, slots=True)
class StabilityGateResult:
    generator_id: str
    baseline: ReferenceMetrics
    candidates: tuple[ReferenceMetrics, ...]
    comparisons: tuple[StabilityComparison, ...]
    passed: bool


def generate_reference_metrics(trial_count: int, seed: int) -> ReferenceMetrics:
    """Run the spec-frozen MT19937 catalogue with the declared draw order."""

    if isinstance(trial_count, bool) or not isinstance(trial_count, int) or trial_count < 1:
        raise ValueError("trial_count must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    rng = random.Random(seed)
    oep: list[float] = []
    aep: list[float] = []
    attached_years = 0
    for _ in range(trial_count):
        event_count = _poisson_inverse(rng.random(), 0.8)
        annual_recoveries: list[float] = []
        for _ in range(event_count):
            severity_draw = rng.random()
            rng.random()  # event time in [0, 365); consumed even though order is immaterial here
            annual_recoveries.append(_reference_recovery(severity_draw))
        if annual_recoveries:
            attached_years += 1
            oep.append(max(annual_recoveries))
            aep.append(math.fsum(annual_recoveries))
        else:
            oep.append(0.0)
            aep.append(0.0)
    oep_sample = tuple(oep)
    aep_sample = tuple(aep)
    return ReferenceMetrics(
        trial_count=trial_count,
        seed=seed,
        recovery_aal=math.fsum(aep_sample) / trial_count,
        annual_attachment_frequency=attached_years / trial_count,
        recovery_oep_10=nearest_rank_quantile(oep_sample, 0.9),
        recovery_oep_20=nearest_rank_quantile(oep_sample, 0.95),
        recovery_aep_10=nearest_rank_quantile(aep_sample, 0.9),
        recovery_aep_20=nearest_rank_quantile(aep_sample, 0.95),
        recovery_aep_tvar_99=empirical_tvar(aep_sample, 0.99),
    )


@lru_cache(maxsize=1)
def run_stability_gate() -> StabilityGateResult:
    """Execute every frozen sample-size/seed comparison without tuned tolerances."""

    baseline = generate_reference_metrics(
        REFERENCE_BASELINE_TRIALS,
        REFERENCE_BASELINE_SEED,
    )
    candidates = tuple(
        generate_reference_metrics(trials, seed)
        for trials in REFERENCE_CANDIDATE_TRIALS
        for seed in REFERENCE_SEEDS
    )
    comparisons = tuple(
        comparison
        for candidate in candidates
        for comparison in _compare(baseline, candidate)
    )
    return StabilityGateResult(
        generator_id=REFERENCE_GENERATOR_ID,
        baseline=baseline,
        candidates=candidates,
        comparisons=comparisons,
        passed=all(item.passed for item in comparisons),
    )


def _compare(
    baseline: ReferenceMetrics,
    candidate: ReferenceMetrics,
) -> tuple[StabilityComparison, ...]:
    tolerances = {
        25_000: {
            "recovery_aal": (0.03, "relative"),
            "annual_attachment_frequency": (0.015, "absolute_probability"),
            "recovery_oep_10": (0.05, "relative"),
            "recovery_oep_20": (0.05, "relative"),
            "recovery_aep_10": (0.10, "relative"),
            "recovery_aep_20": (0.10, "relative"),
            "recovery_aep_tvar_99": (0.10, "relative"),
        },
        100_000: {
            "recovery_aal": (0.015, "relative"),
            "annual_attachment_frequency": (0.0075, "absolute_probability"),
            "recovery_oep_10": (0.05, "relative"),
            "recovery_oep_20": (0.05, "relative"),
            "recovery_aep_10": (0.05, "relative"),
            "recovery_aep_20": (0.05, "relative"),
            "recovery_aep_tvar_99": (0.06, "relative"),
        },
    }[candidate.trial_count]
    results = []
    for metric, (tolerance, basis) in tolerances.items():
        baseline_value = float(getattr(baseline, metric))
        candidate_value = float(getattr(candidate, metric))
        if basis == "relative":
            if baseline_value == 0:
                raise ValueError("frozen relative comparison has zero baseline")
            difference = abs(candidate_value - baseline_value) / abs(baseline_value)
        else:
            difference = abs(candidate_value - baseline_value)
        results.append(
            StabilityComparison(
                metric=metric,
                trial_count=candidate.trial_count,
                seed=candidate.seed,
                baseline=baseline_value,
                candidate=candidate_value,
                difference=difference,
                tolerance=tolerance,
                basis=basis,
                passed=difference <= tolerance,
            )
        )
    return tuple(results)


def _poisson_inverse(uniform_draw: float, rate: float) -> int:
    probability = math.exp(-rate)
    cumulative = probability
    count = 0
    while uniform_draw > cumulative:
        count += 1
        probability *= rate / count
        cumulative += probability
    return count


def _reference_recovery(uniform_draw: float) -> float:
    if uniform_draw < 0.70:
        return 5_000_000.0
    if uniform_draw < 0.95:
        return 25_000_000.0
    return 50_000_000.0
