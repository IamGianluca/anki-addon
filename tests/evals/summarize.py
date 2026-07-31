"""Summarize an eval results directory.

Usage: uv run python tests/evals/summarize.py [results_dir] [--write]

With no results_dir, summarizes the most recent run in
tests/evals/results/ — the usual thing to do after `make eval`.
--write also snapshots the summary (without colors or judge reasons)
to tests/evals/scores.md, a tracked, diff-friendly file: commit it
together with a prompt or model change to record its measured effect.

Per task, prints pass@1 (mean per-trial success) and pass^k (all
trials passed). Trials that passed cleanly are silent; failures and
judge verdicts are printed with their reasons wrapped for
readability. Colors are used when the output stream is a terminal.
"""

from __future__ import annotations

import io
import json
import os
import sys
import textwrap
from pathlib import Path

RESULTS_ROOT = Path(__file__).parent / "results"
SCORES_FILE = Path(__file__).parent / "scores.md"

# graders.py emits judge-originated failures/unknowns with these
# prefixes; they are shown in the judge section, not the failure list.
_JUDGE_FAILURE_PREFIX = "judge rejected "
_JUDGE_UNKNOWN_PREFIX = "judge could not decide "

_WIDTH = 79
_MAX_REASON = 600
_GREEN, _RED, _YELLOW = "32", "31", "33"


def main() -> None:
    write = "--write" in sys.argv
    positional = [a for a in sys.argv[1:] if a != "--write"]
    results_dir = Path(positional[0]) if positional else _latest_run()
    records = _load_records(results_dir)

    print(f"results: {results_dir}\n")
    _emit(records, sys.stdout, with_reasons=True)

    if write:
        buffer = io.StringIO()
        _emit(records, buffer, with_reasons=False)
        SCORES_FILE.write_text(
            f"# Eval scores\n\n"
            f"run: {results_dir.name}\n"
            f"model: {os.environ.get('OPENAI_MODEL', 'unknown')}\n\n"
            + buffer.getvalue()
        )
        print(f"\nwrote {SCORES_FILE}")


def _load_records(results_dir: Path) -> list[dict]:
    records = [
        json.loads(path.read_text())
        for path in sorted(results_dir.glob("*.trial*.json"))
    ]
    if not records:
        raise SystemExit(f"no trial records in {results_dir}")
    return records


def _emit(records: list[dict], out: io.TextIOBase, with_reasons: bool) -> None:
    color = out.isatty()
    by_task: dict[str, list[dict]] = {}
    for record in records:
        by_task.setdefault(record["task_id"], []).append(record)

    n_tasks_passed = 0
    pass_rates = []
    for task_id, trials in sorted(by_task.items()):
        k = len(trials)
        n_passed = sum(trial["passed"] for trial in trials)
        n_tasks_passed += n_passed == k
        pass_rates.append(n_passed / k)
        _print_task(out, color, with_reasons, task_id, trials, n_passed)
        print(file=out)

    print(
        f"summary: {n_tasks_passed}/{len(by_task)} tasks pass^k, "
        f"mean pass@1 {sum(pass_rates) / len(pass_rates):.0%}",
        file=out,
    )


def _print_task(
    out: io.TextIOBase,
    color: bool,
    with_reasons: bool,
    task_id: str,
    trials: list[dict],
    n_passed: int,
) -> None:
    k = len(trials)
    all_passed = n_passed == k
    print(
        f"{_marker(all_passed, color)} {task_id:<28} "
        f"pass@1 {n_passed / k:>4.0%}  "
        f"pass^{k} {int(all_passed)}  ({n_passed}/{k} trials)",
        file=out,
    )
    for trial in trials:
        has_detail = (
            not trial["passed"]
            or trial["failures"]
            or trial["unknowns"]
            or trial.get("judge_verdicts")
        )
        if has_detail:
            _print_trial(out, color, with_reasons, trial)


def _print_trial(
    out: io.TextIOBase, color: bool, with_reasons: bool, trial: dict
) -> None:
    stats = trial.get("stats", {})
    steps = stats.get("n_steps")
    detail = ""
    if steps is not None:
        errors = stats.get("n_schema_errors", 0)
        detail = f"  ({steps} steps, {errors} schema errors)"
    print(
        f"  trial {trial['trial']}: {_marker(trial['passed'], color)}{detail}",
        file=out,
    )
    for failure in trial["failures"]:
        if not failure.startswith(_JUDGE_FAILURE_PREFIX):
            _print_wrapped(out, "    failure: ", failure)
    for unknown in trial["unknowns"]:
        if not unknown.startswith(_JUDGE_UNKNOWN_PREFIX):
            _print_wrapped(out, "    unknown: ", unknown)
    for verdict in trial.get("judge_verdicts", []):
        _print_verdict(out, color, with_reasons, verdict)


def _print_verdict(
    out: io.TextIOBase, color: bool, with_reasons: bool, verdict: dict
) -> None:
    mark = {
        "pass": _paint("✓", _GREEN, color),
        "fail": _paint("✗", _RED, color),
    }.get(verdict["verdict"], _paint("?", _YELLOW, color))
    assertion = textwrap.shorten(
        verdict["assertion"], width=65, placeholder="…"
    )
    print(f"    judge {mark} {assertion}", file=out)
    if with_reasons:
        reason = verdict["reason"]
        if len(reason) > _MAX_REASON:
            reason = reason[:_MAX_REASON] + "…"
        _print_wrapped(out, "      ", reason)


def _print_wrapped(out: io.TextIOBase, prefix: str, text: str) -> None:
    print(
        textwrap.fill(
            text,
            width=_WIDTH,
            initial_indent=prefix,
            subsequent_indent=" " * len(prefix),
        ),
        file=out,
    )


def _marker(passed: bool, color: bool) -> str:
    if passed:
        return _paint("✓", _GREEN, color)
    return _paint("✗", _RED, color)


def _paint(text: str, code: str, color: bool) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if color else text


def _latest_run() -> Path:
    runs = sorted(path for path in RESULTS_ROOT.iterdir() if path.is_dir())
    if not runs:
        raise SystemExit(f"no results in {RESULTS_ROOT} — run make eval first")
    return runs[-1]


if __name__ == "__main__":
    main()
