"""Capability and regression evals for the CuratorAgent.

Runs the real agent against a real LLM on the task set in
tests/evals/tasks/. Gated behind RUN_EVALS=1: trials are slow,
non-deterministic, and spend LLM tokens, so they never run as part of
make test / make test_slow. See tests/evals/README.md.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from tests.evals.graders import grade_trial
from tests.evals.harness import (
    TASKS_DIR,
    load_task,
    run_trial,
    write_trial_record,
)

if TYPE_CHECKING:
    from addon.application.protocols import CompletionProvider

_RUN = os.environ.get("RUN_EVALS") == "1"
_STRICT = os.environ.get("EVAL_STRICT") == "1"

pytestmark = [
    pytest.mark.eval,
    pytest.mark.skipif(
        not _RUN, reason="LLM evals are opt-in: set RUN_EVALS=1"
    ),
]

_TASK_FILES = sorted(TASKS_DIR.glob("*.json"))
_TASK_IDS = [path.stem for path in _TASK_FILES]


@pytest.mark.parametrize("task_path", _TASK_FILES, ids=_TASK_IDS)
def test_curator_task(
    task_path: Path,
    llm_client: CompletionProvider,
    eval_results_dir: Path,
) -> None:
    # Given
    task = load_task(task_path)

    # When
    failures_by_trial: list[list[str]] = []
    for trial_index in range(task.trials):
        outcome = run_trial(task, llm_client)
        grade = grade_trial(task, outcome, judge_client=llm_client)
        record = write_trial_record(
            eval_results_dir, trial_index, outcome, grade
        )
        verdict = "PASS" if grade.passed else "FAIL"
        print(f"\n[{task.id} trial {trial_index}] {verdict} -> {record}")
        failures_by_trial.append(grade.failures)

    # Then
    # Capability tasks report only — they are a hill to climb, not a
    # gate. Regression tasks must pass every trial (pass^k).
    if task.suite == "regression" or _STRICT:
        failures = [f for f in failures_by_trial if f]
        assert not failures, f"{task.id}: {failures}"
