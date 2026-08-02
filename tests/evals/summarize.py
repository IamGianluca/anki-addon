"""Summarize an eval results directory.

Usage: uv run python tests/evals/summarize.py [results_dir] [--write]

With no results_dir, summarizes the most recent run in
tests/evals/results/ — the usual thing to do after `make eval`.
--write also snapshots the summary (without colors or judge reasons)
to tests/evals/scores.md, a tracked, diff-friendly file: commit it
together with a prompt or model change to record its measured effect.

Per task, prints pass@1 (mean per-trial success), mean score (partial
credit across graded dimensions), and pass^k (all trials passed).
Trials that passed cleanly are silent; partial and full failures show
individual check verdicts for diagnostic visibility.
Colors are used when the output stream is a terminal.
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
    mean_scores = []
    for task_id, trials in sorted(by_task.items()):
        k = len(trials)
        n_passed = sum(1 for t in trials if t["passed"])
        task_scores = [t.get("score") for t in trials if t.get("score") is not None]
        n_tasks_passed += n_passed == k
        pass_rates.append(n_passed / k)
        if task_scores:
            mean_scores.append(sum(task_scores) / len(task_scores))
        _print_task(out, color, with_reasons, task_id, trials, n_passed)
        print(file=out)

    score_line = ""
    if mean_scores:
        score_line = f", mean score {sum(mean_scores) / len(mean_scores):.0%}"
    print(
        f"summary: {n_tasks_passed}/{len(by_task)} tasks pass^k, "
        f"mean pass@1 {sum(pass_rates) / len(pass_rates):.0%}"
        f"{score_line}",
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
    # Compute mean score for this task.
    task_scores = [t.get("score") for t in trials if t.get("score") is not None]
    score_str = ""
    if task_scores:
        mean_s = sum(task_scores) / len(task_scores)
        score_str = f"  score {mean_s:.0%}"

    print(
        f"{_marker(all_passed, color)} {task_id:<28} "
        f"pass@1 {n_passed / k:>4.0%}  "
        f"pass^{k} {int(all_passed)}  ({n_passed}/{k} trials)"
        f"{score_str}",
        file=out,
    )
    for trial in trials:
        has_detail = not trial["passed"] or trial.get("failures") or trial.get(
            "unknowns"
        )
        if has_detail:
            _print_trial(out, color, with_reasons, trial)


def _print_trial(
    out: io.TextIOBase, color: bool, with_reasons: bool, trial: dict
) -> None:
    stats = trial.get("stats", {})
    steps = stats.get("n_steps")
    detail_parts = []
    if steps is not None:
        errors = stats.get("n_schema_errors", 0)
        detail_parts.append(f"{steps} steps")
        if errors:
            detail_parts.append(f"{errors} schema errors")
    score = trial.get("score")
    if score is not None:
        detail_parts.append(f"score {score:.0%}")
    detail = f"  ({', '.join(detail_parts)})" if detail_parts else ""
    print(
        f"  trial {trial['trial']}: {_marker(trial['passed'], color)}{detail}",
        file=out,
    )

    # Prefer the structured checks if available.
    checks = trial.get("checks")
    if checks:
        _print_checks(out, color, with_reasons, checks)
    else:
        # Fallback for old records without structured checks.
        _print_legacy_trial(out, trial)


def _print_checks(
    out: io.TextIOBase,
    color: bool,
    with_reasons: bool,
    checks: list[dict],
) -> None:
    """Print individual check verdicts with compact markers."""
    for check in checks:
        if check["verdict"] == "pass":
            continue  # silent on passing checks
        mark = {
            "fail": _paint("✗", _RED, color),
            "unknown": _paint("?", _YELLOW, color),
        }.get(check["verdict"], _paint("?", _YELLOW, color))
        name = check["name"]
        reason = check.get("reason", "")
        print(f"    {mark} {name}", file=out)
        if reason and with_reasons:
            if len(reason) > _MAX_REASON:
                reason = reason[:_MAX_REASON] + "…"
            _print_wrapped(out, "       ", reason)


def _print_legacy_trial(
    out: io.TextIOBase,
    trial: dict,
) -> None:
    """Fallback for old records that use flat failures/unknowns lists."""
    # Old prefixes for judge-originated messages.
    _JUDGE_PREFIX = "judge "
    for failure in trial.get("failures", []):
        if failure.startswith(_JUDGE_PREFIX):
            continue
        _print_wrapped(out, "    failure: ", failure)
    for unknown in trial.get("unknowns", []):
        if unknown.startswith(_JUDGE_PREFIX):
            continue
        _print_wrapped(out, "    unknown: ", unknown)
    for verdict in trial.get("judge_verdicts", []):
        _print_verdict(out, False, False, verdict)


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
