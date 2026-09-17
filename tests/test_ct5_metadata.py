"""CT5 canonical serialization, CT4 identity, and hash tests."""

from dataclasses import FrozenInstanceError, replace
import json

import pytest

from cat_treaty.ct4_metadata import build_ct4_run_identity
from cat_treaty.ct5_analytics import calculate_ct5_analytics
from cat_treaty.ct5_metadata import (
    CT5_ENGINE_VERSION,
    CT5_SCHEMA_VERSION,
    CT5RunIdentity,
    build_ct5_run_identity,
    canonicalize_ct5_inputs,
    canonicalize_ct5_result,
    serialize_ct5_inputs,
    serialize_ct5_result,
    validate_ct4_identity,
)
from cat_treaty.ct5_simulation import apply_ct5_catalogue
from cat_treaty.models import SettlementMode
from cat_treaty.tail import calculate_tail_analytics
from tests.test_ct4_simulation import event
from tests.test_ct5_simulation import ct4_result, terms


def completed_run():
    source = ct4_result(
        (
            event("E1", 60_000_000.0, event_time=1.0),
            event("E2", 45_000_000.0, event_time=2.0),
        ),
        (),
    )
    ct4_analytics = calculate_tail_analytics(source)
    ct4_identity = build_ct4_run_identity(
        simulation_input=source.simulation_input,
        result=source,
        analytics=ct4_analytics,
    )
    ct5_result = apply_ct5_catalogue(
        ct4_result=source,
        treaty_terms=terms(reinstatements=1),
    )
    ct5_analytics = calculate_ct5_analytics(ct5_result)
    return ct4_analytics, ct4_identity, ct5_result, ct5_analytics


def test_ct5_version_literals_are_frozen() -> None:
    assert CT5_ENGINE_VERSION == "ct5.0.0"
    assert CT5_SCHEMA_VERSION == "ct5.0"


def test_ct4_identity_is_reproduced_before_ct5_hashing() -> None:
    ct4_analytics, ct4_identity, result, _ = completed_run()
    assert validate_ct4_identity(
        ct5_result=result,
        ct4_analytics=ct4_analytics,
        ct4_identity=ct4_identity,
    ) is None
    tampered = replace(ct4_identity, result_hash="f" * 64)
    with pytest.raises(ValueError, match="reproduction failed"):
        validate_ct4_identity(
            ct5_result=result,
            ct4_analytics=ct4_analytics,
            ct4_identity=tampered,
        )


def test_unsupported_ct4_version_is_rejected() -> None:
    ct4_analytics, identity, result, _ = completed_run()
    with pytest.raises(ValueError, match="not supported"):
        validate_ct4_identity(
            ct5_result=result,
            ct4_analytics=ct4_analytics,
            ct4_identity=replace(identity, engine_version="ct4.0.1"),
        )


def test_input_serialization_is_canonical_json() -> None:
    _, identity, result, _ = completed_run()
    serialized = serialize_ct5_inputs(result.treaty_terms, identity)
    decoded = json.loads(serialized)
    assert serialized.decode() == json.dumps(
        decoded,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert decoded["ct4_input_hash"] == identity.input_hash
    assert decoded["ct4_result_hash"] == identity.result_hash
    assert decoded["relative_tolerance"] == 1e-12
    assert decoded["absolute_currency_tolerance"] == 1e-6


def test_non_contractual_layer_term_order_canonicalizes_identically() -> None:
    _, identity, result, _ = completed_run()
    reversed_terms = replace(
        result.treaty_terms,
        layer_terms=tuple(reversed(result.treaty_terms.layer_terms)),
    )
    assert serialize_ct5_inputs(result.treaty_terms, identity) == serialize_ct5_inputs(reversed_terms, identity)


def test_tranche_order_is_hash_significant() -> None:
    _, identity, result, _ = completed_run()
    layer = result.treaty_terms.layer_terms[0]
    first = layer.reinstatement_tranches[0]
    second = replace(first, sequence=2, premium_rate=2.0)
    two = replace(layer, reinstatement_tranches=(first, second))
    reversed_rates = replace(
        layer,
        reinstatement_tranches=(
            replace(first, premium_rate=2.0),
            replace(second, premium_rate=1.0),
        ),
    )
    base = replace(result.treaty_terms, layer_terms=(two, result.treaty_terms.layer_terms[1]))
    changed = replace(result.treaty_terms, layer_terms=(reversed_rates, result.treaty_terms.layer_terms[1]))
    assert serialize_ct5_inputs(base, identity) != serialize_ct5_inputs(changed, identity)


def test_display_references_do_not_change_input_serialization() -> None:
    _, identity, result, _ = completed_run()
    first = result.treaty_terms.layer_terms[0]
    changed = replace(
        result.treaty_terms,
        source_reference="other",
        rule_reference="other",
        layer_terms=(
            replace(first, source_reference="other", rule_reference="other"),
            result.treaty_terms.layer_terms[1],
        ),
    )
    assert serialize_ct5_inputs(result.treaty_terms, identity) == serialize_ct5_inputs(changed, identity)


def test_contractual_changes_change_canonical_input() -> None:
    _, identity, result, _ = completed_run()
    changed_terms = replace(
        result.treaty_terms,
        layer_terms=tuple(
            replace(item, settlement_mode=SettlementMode.DEDUCTED_FROM_SETTLEMENT)
            for item in result.treaty_terms.layer_terms
        ),
    )
    assert serialize_ct5_inputs(result.treaty_terms, identity) != serialize_ct5_inputs(changed_terms, identity)


def test_identity_is_deterministic_immutable_and_bound_to_ct4() -> None:
    ct4_analytics, ct4_identity, result, analytics = completed_run()
    first = build_ct5_run_identity(
        result=result,
        analytics=analytics,
        ct4_analytics=ct4_analytics,
        ct4_identity=ct4_identity,
    )
    second = build_ct5_run_identity(
        result=result,
        analytics=analytics,
        ct4_analytics=ct4_analytics,
        ct4_identity=ct4_identity,
    )
    assert first == second
    assert isinstance(first, CT5RunIdentity)
    assert first.ct4_input_hash == ct4_identity.input_hash
    assert first.ct4_result_hash == ct4_identity.result_hash
    assert len(first.input_hash) == len(first.result_hash) == 64
    with pytest.raises(FrozenInstanceError):
        first.result_hash = "0" * 64  # type: ignore[misc]


def test_engine_and_schema_versions_change_both_hashes() -> None:
    ct4_analytics, identity, result, analytics = completed_run()
    baseline = build_ct5_run_identity(result=result, analytics=analytics, ct4_analytics=ct4_analytics, ct4_identity=identity)
    engine = build_ct5_run_identity(result=result, analytics=analytics, ct4_analytics=ct4_analytics, ct4_identity=identity, engine_version="ct5.0.1")
    schema = build_ct5_run_identity(result=result, analytics=analytics, ct4_analytics=ct4_analytics, ct4_identity=identity, schema_version="ct5.1")
    assert len({baseline.input_hash, engine.input_hash, schema.input_hash}) == 3
    assert len({baseline.result_hash, engine.result_hash, schema.result_hash}) == 3


def test_result_serialization_is_deterministic_and_excludes_trace_wording() -> None:
    _, _, result, analytics = completed_run()
    serialized = serialize_ct5_result(result, analytics)
    decoded = json.loads(serialized)
    assert serialized.decode() == json.dumps(decoded, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    row = result.occurrence_rows[0]
    changed_row = replace(row, trace_references=("other",))
    changed_annual = replace(result.annual_rows[0], event_rows=(changed_row, result.annual_rows[0].event_rows[1]))
    changed = replace(result, occurrence_rows=(changed_row,) + result.occurrence_rows[1:], annual_rows=(changed_annual, result.annual_rows[1]))
    assert serialize_ct5_result(result, analytics) == serialize_ct5_result(changed, analytics)


def test_mismatched_analytics_are_rejected() -> None:
    _, _, result, analytics = completed_run()
    altered_operational = replace(
        analytics.operational,
        average_recovery_constrained=analytics.operational.average_recovery_constrained + 1.0,
    )
    with pytest.raises(ValueError, match="do not match"):
        canonicalize_ct5_result(result, replace(analytics, operational=altered_operational))


def test_metadata_public_exports() -> None:
    import cat_treaty

    expected = {
        "CT5_ENGINE_VERSION",
        "CT5_SCHEMA_VERSION",
        "CT5RunIdentity",
        "build_ct5_run_identity",
        "canonicalize_ct5_inputs",
        "canonicalize_ct5_result",
        "serialize_ct5_inputs",
        "serialize_ct5_result",
        "validate_ct4_identity",
    }
    assert expected.issubset(set(cat_treaty.__all__))
    assert all(hasattr(cat_treaty, item) for item in expected)
