"""Summarize an eval results directory.

Usage: uv run python tests/evals/summarize.py [results_dir]

With no argument, summarizes the most recent run in
tests/evals/results/ — the usual thing to do after `make eval`.

Prints per-task pass@1 (mean per-trial success) and pass^k (all trials
passed) — the two ways to read non-deterministic results — followed by
every recorded failure and judge "unknown".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS_ROOT = Path(__file__).parent / "results"


def main() -> None:
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_run()
    print(f"results: {results_dir}")
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
            for verdict in trial.get("judge_verdicts", []):
                assertion = verdict["assertion"]
                if len(assertion) > 60:
                    assertion = assertion[:60] + "..."
                print(
                    f"  trial {trial['trial']}: "
                    f"[judge:{verdict['verdict']}] {assertion!r} — "
                    f"{verdict['reason']}"
                )


def _latest_run() -> Path:
    runs = sorted(path for path in RESULTS_ROOT.iterdir() if path.is_dir())
    if not runs:
        raise SystemExit(f"no results in {RESULTS_ROOT} — run make eval first")
    return runs[-1]


if __name__ == "__main__":
    main()
