"""Summarize an eval results directory.

Usage: uv run python tests/evals/summarize.py [results_dir]

With no argument, summarizes the most recent run in
tests/evals/results/ — the usual thing to do after `make eval`.

Per task, prints pass@1 (mean per-trial success) and pass^k (all
trials passed). Trials that passed cleanly are silent; failures and
judge verdicts are printed with their reasons wrapped for
readability. Colors are used when stdout is a terminal.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

RESULTS_ROOT = Path(__file__).parent / "results"

# graders.py emits judge-originated failures/unknowns with these
# prefixes; they are shown in the judge section, not the failure list.
_JUDGE_FAILURE_PREFIX = "judge rejected "
_JUDGE_UNKNOWN_PREFIX = "judge could not decide "

_WIDTH = 79
_MAX_REASON = 600
_GREEN, _RED, _YELLOW = "32", "31", "33"


def main() -> None:
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else _latest_run()
    records = [
        json.loads(path.read_text())
        for path in sorted(results_dir.glob("*.trial*.json"))
    ]
    if not records:
        raise SystemExit(f"no trial records in {results_dir}")

    by_task: dict[str, list[dict]] = {}
    for record in records:
        by_task.setdefault(record["task_id"], []).append(record)

    print(f"results: {results_dir}\n")
    n_tasks_passed = 0
    pass_rates = []
    for task_id, trials in sorted(by_task.items()):
        k = len(trials)
        n_passed = sum(trial["passed"] for trial in trials)
        n_tasks_passed += n_passed == k
        pass_rates.append(n_passed / k)
        _print_task(task_id, trials, n_passed)
        print()

    print(
        f"summary: {n_tasks_passed}/{len(by_task)} tasks pass^k, "
        f"mean pass@1 {sum(pass_rates) / len(pass_rates):.0%}"
    )


def _print_task(task_id: str, trials: list[dict], n_passed: int) -> None:
    k = len(trials)
    print(
        f"{_marker(n_passed == k)} {task_id:<28} "
        f"pass@1 {n_passed / k:>4.0%}  "
        f"pass^{k} {int(n_passed == k)}  ({n_passed}/{k} trials)"
    )
    for trial in trials:
        has_detail = (
            not trial["passed"]
            or trial["failures"]
            or trial["unknowns"]
            or trial.get("judge_verdicts")
        )
        if has_detail:
            _print_trial(trial)


def _print_trial(trial: dict) -> None:
    stats = trial.get("stats", {})
    steps = stats.get("n_steps")
    detail = ""
    if steps is not None:
        errors = stats.get("n_schema_errors", 0)
        detail = f"  ({steps} steps, {errors} schema errors)"
    print(f"  trial {trial['trial']}: {_marker(trial['passed'])}{detail}")

    for failure in trial["failures"]:
        if not failure.startswith(_JUDGE_FAILURE_PREFIX):
            _print_wrapped("    failure: ", failure)
    for unknown in trial["unknowns"]:
        if not unknown.startswith(_JUDGE_UNKNOWN_PREFIX):
            _print_wrapped("    unknown: ", unknown)
    for verdict in trial.get("judge_verdicts", []):
        _print_verdict(verdict)


def _print_verdict(verdict: dict) -> None:
    mark = {
        "pass": _paint("✓", _GREEN),
        "fail": _paint("✗", _RED),
    }.get(verdict["verdict"], _paint("?", _YELLOW))
    assertion = textwrap.shorten(
        verdict["assertion"], width=65, placeholder="…"
    )
    print(f"    judge {mark} {assertion}")
    reason = verdict["reason"]
    if len(reason) > _MAX_REASON:
        reason = reason[:_MAX_REASON] + "…"
    _print_wrapped("      ", reason)


def _print_wrapped(prefix: str, text: str) -> None:
    print(
        textwrap.fill(
            text,
            width=_WIDTH,
            initial_indent=prefix,
            subsequent_indent=" " * len(prefix),
        )
    )


def _marker(passed: bool) -> str:
    return _paint("✓", _GREEN) if passed else _paint("✗", _RED)


def _paint(text: str, code: str) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def _latest_run() -> Path:
    runs = sorted(path for path in RESULTS_ROOT.iterdir() if path.is_dir())
    if not runs:
        raise SystemExit(f"no results in {RESULTS_ROOT} — run make eval first")
    return runs[-1]


if __name__ == "__main__":
    main()
