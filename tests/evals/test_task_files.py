"""LLM-free validation of the eval task set.

Runs in make test_slow like any other fast test: task files are the
suite's source of truth, so a malformed task — or a reference solution
that no longer passes the outcome graders — fails loudly and cheaply.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.evals.formatting import check_formatting, written_fields
from tests.evals.graders import grade_outcome
from tests.evals.harness import (
    TASKS_DIR,
    build_reference_proposals,
    load_task,
)

_TASK_FILES = sorted(TASKS_DIR.glob("*.json"))
_TASK_IDS = [path.stem for path in _TASK_FILES]


@pytest.mark.parametrize("task_path", _TASK_FILES, ids=_TASK_IDS)
def test_task_definition_is_coherent(task_path: Path) -> None:
    # Given / When
    task = load_task(task_path)

    # Then
    note_ids = {note.id for note in task.notes}
    assert len(note_ids) == len(task.notes), "duplicate note ids"
    assert task.seed_note_id in note_ids
    for proposal in task.reference:
        if proposal.type in ("edit", "delete"):
            assert proposal.note_id in note_ids
    for note_id in (
        *task.expect.must_touch,
        *task.expect.must_not_touch,
    ):
        assert note_id in note_ids
    # Every task must be solvable by construction; for should-not-fire
    # tasks the reference is the empty change set.
    assert task.reference or task.expect.empty, (
        "task has no reference solution"
    )


@pytest.mark.parametrize("task_path", _TASK_FILES, ids=_TASK_IDS)
def test_reference_solution_passes_outcome_graders(
    task_path: Path,
) -> None:
    # Given
    task = load_task(task_path)
    proposals = build_reference_proposals(task)

    # When
    result = grade_outcome(task, proposals)

    # Then
    assert result.passed, result.failures


@pytest.mark.parametrize("task_path", _TASK_FILES, ids=_TASK_IDS)
def test_reference_solution_respects_formatting_rules(
    task_path: Path,
) -> None:
    """Reference solutions are known-good agent output, so they must
    obey the same standing house-style rules the agent must obey."""
    # Given
    task = load_task(task_path)
    proposals = build_reference_proposals(task)

    # When
    violations = check_formatting(written_fields(proposals))

    # Then
    assert not violations, [
        f"{v.rule} [{v.field}] {v.snippet}" for v in violations
    ]
