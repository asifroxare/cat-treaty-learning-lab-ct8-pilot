"""Consolidated CT5 G47--G68 acceptance and permanent trace IDs."""

import ast
from pathlib import Path

from cat_treaty import prepare_ct5_hours_clause_entry
from cat_treaty.golden_cases import CT5_GOLDEN_CASE_EVIDENCE
from tests.test_ct4_metadata import completed_hours


def test_g47_to_g68_have_complete_unique_permanent_trace_ids() -> None:
    expected = tuple(f"G{number}" for number in range(47, 69))
    assert tuple(item.case_id for item in CT5_GOLDEN_CASE_EVIDENCE) == expected
    assert len({item.test_node_id for item in CT5_GOLDEN_CASE_EVIDENCE}) == len(expected)


def test_every_golden_trace_resolves_to_a_collected_test() -> None:
    root = Path(__file__).resolve().parents[1]
    for evidence in CT5_GOLDEN_CASE_EVIDENCE:
        relative_path, function_name = evidence.test_node_id.split("::", 1)
        source = root / relative_path
        assert source.is_file(), evidence.case_id
        functions = {
            node.name
            for node in ast.parse(source.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert function_name in functions, evidence.case_id


def test_g61_hours_clause_entry_uses_only_elected_occurrences() -> None:
    _, result, _ = completed_hours()
    entry = prepare_ct5_hours_clause_entry(result)

    assert entry.occurrence_rows == result.selected_occurrence_rows
    assert len(entry.event_times) == len(result.selected_occurrence_rows)
    elected_ids = {row.event_id.rsplit(":", 1)[-1] for row in entry.occurrence_rows}
    selected_set = next(
        item
        for item in result.candidate_sets
        if item.candidate_set_id == result.selected_candidate_set_id
    )
    assert result.selected_candidate_set_id in result.valid_candidate_set_ids
    assert elected_ids == set(selected_set.window_ids)
