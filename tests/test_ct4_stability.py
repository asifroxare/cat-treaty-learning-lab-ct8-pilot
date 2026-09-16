"""G11/G42 frozen reference reproducibility and stability tests."""

from dataclasses import FrozenInstanceError

import pytest

from cat_treaty.stability import (
    REFERENCE_BASELINE_SEED,
    REFERENCE_BASELINE_TRIALS,
    REFERENCE_CANDIDATE_TRIALS,
    REFERENCE_GENERATOR_ID,
    REFERENCE_SEEDS,
    generate_reference_metrics,
    run_stability_gate,
)


def test_g11_reference_generator_is_exactly_reproducible() -> None:
    first = generate_reference_metrics(5_000, 20260915)
    second = generate_reference_metrics(5_000, 20260915)
    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.seed = 1  # type: ignore[misc]


def test_seed_change_is_disclosed_and_changes_reference_realization() -> None:
    first = generate_reference_metrics(5_000, 11)
    second = generate_reference_metrics(5_000, 29)
    assert first.seed == 11 and second.seed == 29
    assert first != second


def test_reference_generator_validates_trial_count_and_seed() -> None:
    for trials, seed in ((0, 1), (True, 1), (1, -1), (1, True)):
        with pytest.raises(ValueError):
            generate_reference_metrics(trials, seed)  # type: ignore[arg-type]


def test_g42_every_frozen_stability_comparison_passes() -> None:
    result = run_stability_gate()
    assert result.generator_id == REFERENCE_GENERATOR_ID
    assert (result.baseline.trial_count, result.baseline.seed) == (
        REFERENCE_BASELINE_TRIALS,
        REFERENCE_BASELINE_SEED,
    )
    assert {(item.trial_count, item.seed) for item in result.candidates} == {
        (trials, seed)
        for trials in REFERENCE_CANDIDATE_TRIALS
        for seed in REFERENCE_SEEDS
    }
    assert len(result.comparisons) == 70
    assert all(item.passed for item in result.comparisons)
    assert result.passed is True
