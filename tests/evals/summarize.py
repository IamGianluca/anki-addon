"""Summarize an eval results directory.

Usage: uv run python tests/evals/summarize.py tests/evals/results/<stamp>

Prints per-task pass@1 (mean per-trial success) and pass^k (all trials
passed) — the two ways to read non-deterministic results — followed by
every recorded failure and judge "unknown".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    results_dir = Path(sys.argv[1])
    records = [
        json.loads(path.read_text())
        for path in sorted(results_dir.glob("*.trial*.json"))
    ]
    if not records:
        print(f"no trial records in {results_dir}")
        return

    by_task: dict[str, list[dict]] = {}
    for record in records:
        by_task.setdefault(record["task_id"], []).append(record)

    for task_id, trials in sorted(by_task.items()):
        k = len(trials)
        n_passed = sum(trial["passed"] for trial in trials)
        print(
            f"{task_id}: pass@1={n_passed / k:.0%} "
            f"pass^{k}={int(n_passed == k)} ({n_passed}/{k} trials)"
        )
        for trial in trials:
            for failure in trial["failures"]:
                print(f"  trial {trial['trial']}: {failure}")
            for unknown in trial["unknowns"]:
                print(f"  trial {trial['trial']}: [unknown] {unknown}")


if __name__ == "__main__":
    main()
