"""FastHTML viewer for curator eval results and production traces.

Loads record JSON files from a run directory and renders:
- Dashboard: all runs with aggregate pass rates (plus production
  trace sessions with their outcomes)
- Run detail: per-task breakdown with trial grid
- Trial detail: seed notes, transcript, checks, judge verdicts,
  change set, production outcome, and annotations

Run:  uv run python -m tests.evals.viewer [--dir PATH]
The --dir flag points at the addon's traces/ folder to review
production sessions instead of eval results.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fasthtml.common import (  # noqa: F401
    H1,
    H2,
    H3,
    H4,
    A,
    Button,
    Datalist,
    Div,
    FastHTML,
    Form,
    Header,
    Input,
    JSONResponse,
    Label,
    Li,
    Main,
    Option,
    P,
    Pre,
    RedirectResponse,
    Request,
    Script,
    Section,
    Span,
    Style,
    Table,
    Tbody,
    Td,
    Textarea,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
)


def _results_dir() -> Path:
    """Directory of run folders to view.

    The `--dir` flag sets EVAL_VIEWER_DIR in __main__.py before the
    server starts. It is resolved per request rather than at import
    time because `python -m tests.evals.viewer` imports this package
    (running this module top to bottom) before __main__.py executes.
    """
    return Path(
        os.environ.get(
            "EVAL_VIEWER_DIR", Path(__file__).parent.parent / "results"
        )
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@dataclass
class RunSummary:
    """Aggregated stats for one run (one timestamped directory).

    Eval runs aggregate trials per task; production runs are one
    session per directory. Annotations are per-record, keyed by record
    file name.
    """

    stamp: str
    model: str = "unknown"
    elapsed: float = 0.0
    total_trials: int = 0
    passed_trials: int = 0
    tasks: dict[str, list[TrialRecord]] = field(default_factory=dict)
    annotations: dict[str, dict[str, str]] = field(default_factory=dict)
    is_production: bool = False

    @property
    def pass_rate(self) -> float:
        if self.total_trials == 0:
            return 0.0
        return self.passed_trials / self.total_trials

    @property
    def session(self) -> TrialRecord | None:
        """The single trial of a production run, if any."""
        for trials in self.tasks.values():
            for trial in trials:
                return trial
        return None


@dataclass
class TrialRecord:
    """One trial (eval) or session (production) loaded from JSON."""

    task_id: str
    trial_index: int
    passed: bool
    score: float
    checks: list[dict[str, str]]
    judge_verdicts: list[dict[str, Any]]
    stats: dict[str, Any]
    summary: str | None
    cluster: list[dict[str, Any]]
    change_set: list[dict[str, Any]]
    transcript: list[dict[str, str]]
    model: str | None
    source: str = "eval"
    outcome: dict[str, Any] | None = None
    instruction: str | None = None
    file_name: str = ""


def load_runs() -> list[RunSummary]:
    """Load all runs from the results directory, newest first."""
    results_dir = _results_dir()
    if not results_dir.exists():
        return []

    run_dirs = sorted(
        [p for p in results_dir.iterdir() if p.is_dir()],
        reverse=True,
    )

    runs: list[RunSummary] = []
    for run_dir in run_dirs:
        summary = RunSummary(stamp=run_dir.name)

        meta_path = run_dir / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            summary.model = meta.get("model", "unknown")
            summary.elapsed = meta.get("elapsed_seconds", 0.0)

        ann_path = run_dir / "annotations.json"
        if ann_path.exists():
            summary.annotations = json.loads(ann_path.read_text())

        for trial_file in sorted(run_dir.glob("*.trial*.json")):
            data = json.loads(trial_file.read_text())
            # Older runs lack 'score'/'checks'; synthesize from failures.
            checks = data.get("checks", [])
            score = data.get("score", 1.0 if data.get("passed") else 0.0)
            trial = TrialRecord(
                task_id=data["task_id"],
                trial_index=data["trial"],
                passed=data["passed"],
                score=score,
                checks=checks,
                judge_verdicts=data.get("judge_verdicts", []),
                stats=data.get("stats", {}),
                summary=data.get("summary"),
                cluster=data.get("cluster", []),
                change_set=data.get("change_set", []),
                transcript=data.get("transcript", []),
                model=data.get("model"),
                source=data.get("source", "eval"),
                outcome=data.get("outcome"),
                instruction=data.get("instruction"),
                file_name=trial_file.name,
            )
            summary.total_trials += 1
            if trial.passed:
                summary.passed_trials += 1
            if trial.source == "production":
                summary.is_production = True
                if summary.model == "unknown" and trial.model:
                    summary.model = trial.model

            summary.tasks.setdefault(trial.task_id, []).append(trial)

        runs.append(summary)

    return runs


# ---------------------------------------------------------------------------
# Failure mode aggregation
# ---------------------------------------------------------------------------


_ANNOTATION_KEY_RE = re.compile(
    r"^(?P<task_id>.+)\.trial(?P<trial>\d+)\.json$"
)


def parse_annotation_key(file_name: str) -> tuple[str, int] | None:
    """Split an annotation key like 'note_123.trial0.json' into
    (task_id, trial_index); None if the name is not a record key."""
    match = _ANNOTATION_KEY_RE.match(file_name)
    if match is None:
        return None
    return match.group("task_id"), int(match.group("trial"))


def failure_modes(runs: list[RunSummary]) -> dict[str, dict[str, Any]]:
    """Group annotations by label into failure modes.

    Returns {label: {label, count, records}} sorted by count descending,
    then label ascending. Each record carries the run stamp, task id,
    trial index, note, and update time so the UI can link back to the
    trial page. Annotations without a label or with an unparseable key
    are skipped.
    """
    modes: dict[str, dict[str, Any]] = {}
    for run in runs:
        for file_name, ann in run.annotations.items():
            label = (ann.get("label") or "").strip()
            if not label:
                continue
            key = parse_annotation_key(file_name)
            if key is None:
                continue
            task_id, trial = key
            record = {
                "run": run.stamp,
                "file_name": file_name,
                "task_id": task_id,
                "trial": trial,
                "note": ann.get("note", ""),
                "updated": ann.get("updated", ""),
            }
            mode = modes.setdefault(label, {"label": label, "records": []})
            mode["records"].append(record)
    for mode in modes.values():
        mode["records"].sort(
            key=lambda r: (r["updated"], r["run"], r["file_name"]),
            reverse=True,
        )
        mode["count"] = len(mode["records"])
    return dict(sorted(modes.items(), key=lambda kv: (-kv[1]["count"], kv[0])))


def coverage(runs: list[RunSummary]) -> dict[str, Any]:
    """Review coverage for one results directory.

    Returns {annotated, total, per_run: {stamp: {annotated, total}}}
    where 'annotated' counts annotation records (labelled or not) and
    'total' counts trial records on disk.
    """
    per_run = {
        r.stamp: {"annotated": len(r.annotations), "total": r.total_trials}
        for r in runs
    }
    return {
        "annotated": sum(v["annotated"] for v in per_run.values()),
        "total": sum(v["total"] for v in per_run.values()),
        "per_run": per_run,
    }


# ---------------------------------------------------------------------------
# Agent taxonomy (patterns.json)
# ---------------------------------------------------------------------------
# The taxonomy stores only interpretation: a description per failure
# mode. Counts and example records are always derived from the
# annotations files, so the two can never disagree.


def _patterns_path() -> Path:
    """Corpus-level taxonomy file beside the run folders being viewed."""
    return _results_dir() / "patterns.json"


def load_patterns(path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load {label: {description}} from the taxonomy file."""
    path = path or _patterns_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data if isinstance(data, dict) else {}


def save_patterns(
    patterns: dict[str, dict[str, str]], path: Path | None = None
) -> None:
    """Write the taxonomy, replacing any previous version."""
    path = path or _patterns_path()
    path.write_text(json.dumps(patterns, indent=2, ensure_ascii=False) + "\n")


def _patterns_view(runs: list[RunSummary]) -> dict[str, Any]:
    """Failure modes with agent descriptions attached, plus coverage.

    The payload behind GET /api/patterns: the agent reads it to
    organize annotations into modes, and pushes descriptions back
    via POST.
    """
    modes = failure_modes(runs)
    stored = load_patterns()
    for label, mode in modes.items():
        mode["description"] = stored.get(label, {}).get("description", "")
    return {"patterns": modes, "coverage": coverage(runs)}


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

CSS = """
:root {
    --bg: #fafafa;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --text-muted: #6b7280;
    --border: #e5e7eb;
    --green: #16a34a;
    --red: #dc2626;
    --yellow: #ca8a04;
    --blue: #2563eb;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 2rem;
    max-width: 1200px;
    margin: 0 auto;
}

h1 { font-size: 1.75rem; margin-bottom: 1.5rem; }
h2 { font-size: 1.25rem; margin-bottom: 1rem; }
h3 { font-size: 1.1rem; margin-bottom: 0.5rem; }

a { color: var(--blue); text-decoration: none; }
a:hover { text-decoration: underline; }

.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}

.badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-pass { background: #dcfce7; color: var(--green); }
.badge-fail { background: #fee2e2; color: var(--red); }
.badge-unknown { background: #fef9c3; color: var(--yellow); }

table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
}
th, td {
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border);
}
th { font-weight: 600; font-size: 0.85rem; color: var(--text-muted); }

.transcript-entry {
    border-left: 3px solid var(--border);
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    background: var(--card-bg);
}
.transcript-entry.system { border-color: var(--text-muted); }
.transcript-entry.user { border-color: var(--blue); }
.transcript-entry.tool { border-color: var(--yellow); }
.transcript-entry.assistant { border-color: var(--green); }

.transcript-role {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.25rem;
}

.check-list { list-style: none; }
.check-list li {
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.check-list li:last-child { border-bottom: none; }

.proposal-block {
    background: #f8fafc;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
}
.stat-box {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.75rem;
    text-align: center;
}
.stat-value { font-size: 1.5rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); }
"""

JS = Script("""
function toggle(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}
""")

# Repeated inline styles extracted for line-length compliance.
_PRE_STYLE = (
    "font-size: 0.8rem; white-space: pre-wrap; word-break: break-word;"
)
_BUTTON_STYLE = "font-size: 0.75rem; margin-bottom: 0.5rem; cursor: pointer;"
_THOUGHT_STYLE = "font-size: 0.85rem; margin-bottom: 0.25rem;"


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastHTML(
    hdrs=[
        Title("Eval Viewer"),
        Style(CSS),
        JS,
    ],
)
rt = app.route


def _badge(text: str, cls: str) -> Span:
    return Span(text, cls=f"badge badge-{cls}")


_OUTCOME_BADGE_CLS = {
    "applied": "pass",
    "rejected": "fail",
    "cancelled": "unknown",
    "no_changes": "unknown",
    "failed": "fail",
}


def _outcome_badge(status: str) -> Span:
    cls = _OUTCOME_BADGE_CLS.get(status, "unknown")
    return _badge(status.replace("_", " ").upper(), cls)


def _proposal_block(p: dict, show_rationale: bool = True) -> Div:
    """Render one change-set proposal (edit/create/delete).

    `show_rationale=False` drops the rationale line — used in the
    outcome card, where the rationale is the agent's, not the user's:
    the user never explains why they approved or rejected.
    """
    ptype = p.get("type", "edit").upper()
    if ptype == "EDIT":
        return Div(
            H4(f"EDIT note {p.get('note_id')}"),
            P(f"Rationale: {p.get('rationale', '')}")
            if show_rationale
            else "",
            Div(
                P("Before:"),
                Pre(
                    json.dumps(p.get("before", {}), indent=2),
                    style="font-size: 0.8rem; margin: 0.25rem 0;",
                ),
                P("After:"),
                Pre(
                    json.dumps(p.get("after", {}), indent=2),
                    style="font-size: 0.8rem; margin: 0.25rem 0;",
                ),
            ),
            cls="proposal-block",
        )
    if ptype == "CREATE":
        return Div(
            H4("CREATE"),
            P(f"Rationale: {p.get('rationale', '')}")
            if show_rationale
            else "",
            Pre(
                json.dumps(p.get("note", {}), indent=2),
                style="font-size: 0.8rem;",
            ),
            cls="proposal-block",
        )
    return Div(
        H4(f"DELETE note {p.get('note_id')}"),
        P(f"Rationale: {p.get('rationale', '')}") if show_rationale else "",
        Pre(
            json.dumps(p.get("before", {}), indent=2),
            style="font-size: 0.8rem;",
        ),
        cls="proposal-block",
    )


def _labels_used(runs: list[RunSummary]) -> list[str]:
    """Distinct annotation labels across all runs, for the datalist."""
    labels = {
        ann.get("label", "")
        for run in runs
        for ann in run.annotations.values()
        if ann.get("label")
    }
    return sorted(labels)


def _annotation_badge(run: RunSummary, trial: TrialRecord) -> str | Span:
    """The annotation label for a record, or a dash if unannotated."""
    ann = run.annotations.get(trial.file_name)
    if not ann or not ann.get("label"):
        return "—"
    return _badge(ann["label"], "unknown")


def _nav() -> Header:
    return Header(
        A("Dashboard", href="/"),
        Span("  |  ", style="margin: 0 0.5rem;"),
        A("Progress", href="/progress"),
        Span("  |  ", style="margin: 0 0.5rem;"),
        Span(
            f"Results: {_results_dir().name}",
            style="font-size: 0.75rem; color: var(--text-muted);",
        ),
        style="margin-bottom: 1.5rem;",
    )


def _run_link(run: RunSummary) -> A:
    return A(f"{run.stamp}  ({run.model})", href=f"/run/{run.stamp}")


@rt("/")
async def get():  # noqa: F811
    runs = load_runs()
    if not runs:
        return Main(_nav(), H1("Eval Viewer"), P("No results found."))

    eval_runs = [r for r in runs if not r.is_production]
    prod_runs = [r for r in runs if r.is_production]

    sections = []
    if eval_runs:
        rows = []
        for run in eval_runs:
            rows.append(
                Tr(
                    Td(_run_link(run)),
                    Td(f"{run.pass_rate:.0%}"),
                    Td(f"{run.passed_trials}/{run.total_trials}"),
                    Td(f"{run.elapsed:.0f}s"),
                    Td(str(len(run.tasks))),
                )
            )
        sections.extend(
            [
                H2("Eval runs"),
                Table(
                    Thead(
                        Tr(
                            Th("Run"),
                            Th("Pass Rate"),
                            Th("Trials"),
                            Th("Elapsed"),
                            Th("Tasks"),
                        )
                    ),
                    Tbody(*rows),
                ),
            ]
        )

    if prod_runs:
        rows = []
        for run in prod_runs:
            trial = run.session
            if trial is None:
                continue
            outcome = trial.outcome or {}
            status = outcome.get("status", "unknown")
            steps = trial.stats.get("steps", "")
            summary = (trial.summary or "").replace("\n", " ")[:120]
            rows.append(
                Tr(
                    Td(
                        A(
                            f"{run.stamp}  ({trial.task_id})",
                            href=(
                                f"/trial/{run.stamp}/{trial.task_id}/"
                                f"{trial.trial_index}"
                            ),
                        )
                    ),
                    Td(run.model),
                    Td(_outcome_badge(status)),
                    Td(steps),
                    Td(summary or ""),
                    Td(_annotation_badge(run, trial)),
                )
            )
        sections.extend(
            [
                H2("Production traces"),
                P(
                    "Sessions recorded by the addon. The outcome is "
                    "what you decided in the review dialog — that "
                    "decision is the production grade.",
                    style=("color: var(--text-muted); font-size: 0.85rem;"),
                ),
                Table(
                    Thead(
                        Tr(
                            Th("Session"),
                            Th("Model"),
                            Th("Outcome"),
                            Th("Steps"),
                            Th("Summary"),
                            Th("Annotation"),
                        )
                    ),
                    Tbody(*rows),
                ),
            ]
        )

    return Main(_nav(), H1("Eval Viewer"), *sections)


@rt("/run/{stamp}")
async def get(stamp: str):  # noqa: F811
    runs = load_runs()
    run = next((r for r in runs if r.stamp == stamp), None)
    if run is None:
        return Main(_nav(), H1("Run not found"))

    if run.is_production:
        trial = run.session
        if trial is None:
            return Main(_nav(), H1("Run not found"))
        outcome = trial.outcome or {}
        return Main(
            _nav(),
            H2(f"Session: {run.stamp}"),
            Div(
                _outcome_badge(outcome.get("status", "unknown")),
                Span(f"  {trial.task_id}"),
                Span(f"  |  Model: {run.model}"),
                style="margin-bottom: 1rem;",
            ),
            Section(
                H3("Summary"),
                P(trial.summary or "(none)"),
                cls="card",
            ),
            A(
                "Open session →",
                href=f"/trial/{stamp}/{trial.task_id}/{trial.trial_index}",
            ),
        )

    max_trials = max((len(t) for t in run.tasks.values()), default=0)

    task_rows = []
    for task_id, trials in sorted(run.tasks.items()):
        passed = sum(1 for t in trials if t.passed)
        avg_score = sum(t.score for t in trials) / len(trials) if trials else 0

        trial_cells = []
        for t in trials:
            trial_cells.append(
                Td(
                    A(
                        _badge("PASS", "pass")
                        if t.passed
                        else _badge("FAIL", "fail"),
                        href=f"/trial/{stamp}/{t.task_id}/{t.trial_index}",
                    )
                )
            )

        task_rows.append(
            Tr(
                Td(A(task_id, href=f"/task/{stamp}/{task_id}")),
                Td(f"{passed}/{len(trials)}"),
                Td(f"{avg_score:.0%}"),
                *trial_cells,
            )
        )

    return Main(
        _nav(),
        H2(f"Run: {run.stamp}"),
        P(f"Model: {run.model}  |  Elapsed: {run.elapsed:.0f}s"),
        Div(
            _badge(
                f"{run.pass_rate:.0%} pass",
                "pass" if run.pass_rate >= 0.8 else "fail",
            ),
            Span(f"  ({run.passed_trials}/{run.total_trials} trials)"),
            style="margin-bottom: 1rem;",
        ),
        Table(
            Thead(
                Tr(
                    Th("Task"),
                    Th("Passed"),
                    Th("Avg Score"),
                    *[Th(f"T{i}") for i in range(max_trials)],
                )
            ),
            Tbody(*task_rows),
        ),
    )


@rt("/task/{stamp}/{task_id}")
async def get(stamp: str, task_id: str):  # noqa: F811
    runs = load_runs()
    run = next((r for r in runs if r.stamp == stamp), None)
    if run is None:
        return Main(_nav(), H1("Run not found"))

    trials = run.tasks.get(task_id, [])
    if not trials:
        return Main(_nav(), H1("Task not found"))

    trial_cards = []
    for t in trials:
        check_items = []
        for check in t.checks:
            cls = check["verdict"]
            reason = (
                Span(
                    f"— {check['reason']}",
                    style="color: var(--text-muted); font-size: 0.85rem;",
                )
                if check.get("reason")
                else ""
            )
            check_items.append(
                Li(
                    _badge(check["verdict"].upper(), cls),
                    Span(check["name"]),
                    reason,
                )
            )

        trial_cards.append(
            Div(
                Div(
                    H3(f"Trial {t.trial_index}"),
                    _badge("PASS", "pass")
                    if t.passed
                    else _badge("FAIL", "fail"),
                    Span(f"  score: {t.score:.0%}"),
                    style="display: flex; align-items: center; gap: 0.5rem;",
                ),
                Div(
                    *[
                        Div(
                            Span(f"{k}:", style="font-weight: 600;"),
                            Span(f" {v}", style="color: var(--text-muted);"),
                        )
                        for k, v in t.stats.items()
                    ],
                    cls="stats-grid",
                ),
                P(
                    f"Summary: {t.summary}",
                    style="margin: 0.5rem 0; font-style: italic;",
                )
                if t.summary
                else "",
                Div(H4("Checks"), Ul(*check_items, cls="check-list")),
                A(
                    "View full transcript →",
                    href=f"/trial/{stamp}/{t.task_id}/{t.trial_index}",
                ),
                cls="card",
            )
        )

    return Main(
        _nav(),
        H2(task_id),
        A("← Back to run", href=f"/run/{stamp}"),
        *trial_cards,
    )


@rt("/trial/{stamp}/{task_id}/{trial_idx}")
async def get(stamp: str, task_id: str, trial_idx: int):  # noqa: F811
    runs = load_runs()
    run = next((r for r in runs if r.stamp == stamp), None)
    if run is None:
        return Main(_nav(), H1("Run not found"))

    trials = run.tasks.get(task_id, [])
    trial = next((t for t in trials if t.trial_index == trial_idx), None)
    if trial is None:
        return Main(_nav(), H1("Trial not found"))

    # Stats
    stats_items = []
    for k, v in trial.stats.items():
        stats_items.append(
            Div(
                Div(str(v), cls="stat-value"),
                Div(k.replace("_", " ").title(), cls="stat-label"),
                cls="stat-box",
            )
        )

    # Checks
    check_items = []
    for check in trial.checks:
        cls = check["verdict"]
        reason = (
            Span(f"— {check['reason']}", style="color: var(--text-muted);")
            if check.get("reason")
            else ""
        )
        check_items.append(
            Li(
                _badge(check["verdict"].upper(), cls),
                Span(f"<b>{check['name']}</b>"),
                reason,
            )
        )

    # Change set
    proposal_blocks = [_proposal_block(p) for p in trial.change_set]

    # Outcome — production only: what the user decided in review.
    outcome_card = ""
    if trial.outcome:
        outcome = trial.outcome
        status = outcome.get("status", "unknown")
        blocks = []
        if outcome.get("approved"):
            blocks.append(
                Div(
                    H4("Approved by user"),
                    *[
                        _proposal_block(p, show_rationale=False)
                        for p in outcome["approved"]
                    ],
                    style="margin-bottom: 1rem;",
                )
            )
        if outcome.get("rejected"):
            blocks.append(
                Div(
                    H4("Rejected by user"),
                    *[
                        _proposal_block(p, show_rationale=False)
                        for p in outcome["rejected"]
                    ],
                    style="margin-bottom: 1rem;",
                )
            )
        outcome_card = Section(
            H3("Outcome"),
            Div(
                _outcome_badge(status),
                Span(f"  {status}"),
                style="margin-bottom: 0.75rem;",
            ),
            P(f"Error: {outcome.get('error')}")
            if outcome.get("error")
            else "",
            *blocks
            if blocks
            else P("The session ended before any proposals were made."),
            cls="card",
        )

    # Annotation — free-text label + notes, saved to annotations.json.
    ann = run.annotations.get(trial.file_name, {})
    ann_label = ann.get("label", "")
    ann_note = ann.get("note", "")
    ann_updated = ann.get("updated", "")
    annotation_card = Section(
        H3("Annotation"),
        P(
            "Use this to record the failure mode this session shows "
            "(e.g. dropped_fact, wrong_split, overreach). Labels are "
            "free text; the same label on many sessions is a pattern "
            "worth turning into an eval task.",
            style="color: var(--text-muted); font-size: 0.85rem;",
        ),
        P(
            f"Saved: {ann_label}"
            + (f"  ({ann_updated})" if ann_updated else ""),
            style="font-weight: 600; margin: 0.5rem 0;",
        )
        if ann
        else P("Not annotated yet.", style="color: var(--text-muted);"),
        Form(
            Div(
                Label("Label", _for="label"),
                Input(
                    name="label",
                    value=ann_label,
                    placeholder="e.g. dropped_fact, wrong_split, overreach",
                    list="label-options",
                    style="width: 100%; margin-bottom: 0.5rem;",
                ),
                Datalist(
                    *[Option(label) for label in _labels_used(runs)],
                    id="label-options",
                ),
                Label("Notes", _for="note"),
                Textarea(
                    ann_note,
                    name="note",
                    rows=4,
                    style="width: 100%; margin-bottom: 0.5rem;",
                ),
                Button("Save annotation", type="submit"),
            ),
            method="post",
            action=f"/annotate/{stamp}/{task_id}/{trial_idx}",
        ),
        cls="card",
    )

    # Seed notes (the collection the agent started from)
    seed_blocks = []
    for note in trial.cluster:
        extra = (
            P(f"Extra fields: {json.dumps(note.get('extra_fields'))}")
            if note.get("extra_fields")
            else ""
        )
        seed_blocks.append(
            Div(
                H4(f"Note {note.get('id')}"),
                P(f"Front: {note.get('front', '')}"),
                P(f"Back: {note.get('back', '')}"),
                P(
                    "Tags: "
                    + (", ".join(note.get("tags", [])) or "(none)")
                    + f"  |  Type: {note.get('notetype', '')}"
                ),
                extra,
                cls="proposal-block",
            )
        )

    # Judge verdicts (raw LLM-judge output; older runs lack 'checks')
    judge_items = []
    for verdict in trial.judge_verdicts:
        vcls = verdict.get("verdict", "unknown")
        reason = (
            Span(
                f"— {verdict.get('reason', '')}",
                style="color: var(--text-muted);",
            )
            if verdict.get("reason")
            else ""
        )
        judge_items.append(
            Li(
                _badge(vcls.upper(), vcls),
                Span(verdict.get("assertion", "")),
                reason,
            )
        )

    # Transcript
    # After an assistant tool call, the next "user" message is the tool
    # response, not the human. Track this to label entries correctly.
    transcript_entries = []
    prev_was_tool_call = False
    for msg in trial.transcript:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        if role == "system" and len(content) > 500:
            display_content = content[:500] + "\n\n...(truncated)"
            entry_id = "system_full"
            transcript_entries.append(
                Div(
                    Span("SYSTEM", cls="transcript-role"),
                    Button(
                        "Show full system prompt",
                        onclick=f"toggle('{entry_id}')",
                        style=_BUTTON_STYLE,
                    ),
                    Pre(display_content, style=_PRE_STYLE),
                    Div(
                        Pre(content, style=_PRE_STYLE),
                        id=entry_id,
                        style="display: none;",
                    ),
                    cls="transcript-entry system",
                )
            )
            prev_was_tool_call = False
        elif role == "assistant" and content.startswith("{"):
            try:
                parsed = json.loads(content)
                thought = parsed.get("thought", "")
                action = parsed.get("action", {})
                action_type = action.get("action", "unknown")
                transcript_entries.append(
                    Div(
                        Span("ASSISTANT", cls="transcript-role"),
                        P(f"Thought: {thought}", style=_THOUGHT_STYLE),
                        P(
                            f"Action: <b>{action_type}</b>",
                            style="font-size: 0.85rem;",
                        ),
                        Pre(
                            json.dumps(action, indent=2, ensure_ascii=False),
                            style=_PRE_STYLE,
                        ),
                        cls="transcript-entry assistant",
                    )
                )
                prev_was_tool_call = True
            except json.JSONDecodeError:
                transcript_entries.append(
                    Div(
                        Span("ASSISTANT", cls="transcript-role"),
                        Pre(content, style=_PRE_STYLE),
                        cls="transcript-entry assistant",
                    )
                )
                prev_was_tool_call = False
        elif role == "user" and prev_was_tool_call:
            # This is the tool's output, not the human's message.
            transcript_entries.append(
                Div(
                    Span("TOOL", cls="transcript-role"),
                    Pre(content, style=_PRE_STYLE),
                    cls="transcript-entry tool",
                )
            )
            prev_was_tool_call = False
        else:
            transcript_entries.append(
                Div(
                    Span(role.upper(), cls="transcript-role"),
                    Pre(content, style=_PRE_STYLE),
                    cls=f"transcript-entry {role}",
                )
            )
            prev_was_tool_call = False

    return Main(
        _nav(),
        H2(f"{task_id} — Trial {trial_idx}"),
        Div(
            A("← Back to task", href=f"/task/{stamp}/{task_id}"),
            Span("  |  "),
            A("← Back to run", href=f"/run/{stamp}"),
            style="margin-bottom: 1rem;",
        ),
        Div(*stats_items, cls="stats-grid"),
        Section(
            H3("Summary"),
            P(f"Instruction: {trial.instruction}")
            if trial.instruction
            else "",
            P(trial.summary or "(none)"),
            cls="card",
        )
        if trial.summary or trial.instruction
        else "",
        Section(
            H3("Seed Notes"),
            Button(
                "Show seed notes",
                onclick="toggle('seed_notes')",
                style=_BUTTON_STYLE,
            ),
            Div(*seed_blocks, id="seed_notes", style="display: none;"),
            cls="card",
        ),
        Section(H3("Checks"), Ul(*check_items, cls="check-list"), cls="card"),
        (
            Section(
                H3("Judge Verdicts"),
                Ul(*judge_items, cls="check-list"),
                cls="card",
            )
            if trial.judge_verdicts
            else ""
        ),
        Section(
            H3("Change Set"),
            *proposal_blocks if proposal_blocks else P("No changes proposed."),
            cls="card",
        ),
        outcome_card,
        annotation_card,
        Section(H3("Transcript"), *transcript_entries),
    )


@rt("/annotate/{stamp}/{task_id}/{trial_idx}", methods=["post"])
async def post(  # noqa: F811
    stamp: str, task_id: str, trial_idx: int, label: str = "", note: str = ""
) -> RedirectResponse:
    """Save an annotation for one record; redirect back to its page."""
    ann_path = _results_dir() / stamp / "annotations.json"
    annotations = json.loads(ann_path.read_text()) if ann_path.exists() else {}
    annotations[f"{task_id}.trial{trial_idx}.json"] = {
        "label": label.strip(),
        "note": note.strip(),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    ann_path.write_text(
        json.dumps(annotations, indent=2, ensure_ascii=False) + "\n"
    )
    return RedirectResponse(
        f"/trial/{stamp}/{task_id}/{trial_idx}", status_code=303
    )


@rt("/progress")
async def get():  # noqa: F811
    """Review progress: coverage stats and failure modes grouped by
    annotation label, each with its records and the agent's
    description of the mode (if the taxonomy has one)."""
    runs = load_runs()
    modes = failure_modes(runs)
    stored = load_patterns()
    cov = coverage(runs)

    percent = f"{cov['annotated'] / cov['total']:.0%}" if cov["total"] else "—"
    cov_rows = [
        Tr(
            Td(stamp),
            Td(f"{c['annotated']}/{c['total']}"),
            Td(f"{c['annotated'] / c['total']:.0%}" if c["total"] else "—"),
        )
        for stamp, c in sorted(cov["per_run"].items(), reverse=True)
        if c["total"]
    ]

    coverage_card = Section(
        H3("Coverage"),
        Div(
            Div(
                Div(str(cov["annotated"]), cls="stat-value"),
                Div("Annotated", cls="stat-label"),
                cls="stat-box",
            ),
            Div(
                Div(str(cov["total"]), cls="stat-value"),
                Div("Records", cls="stat-label"),
                cls="stat-box",
            ),
            Div(
                Div(percent, cls="stat-value"),
                Div("Reviewed", cls="stat-label"),
                cls="stat-box",
            ),
            cls="stats-grid",
        ),
        (
            Table(
                Thead(Tr(Th("Run"), Th("Annotated"), Th("%"))),
                Tbody(*cov_rows),
            )
            if cov_rows
            else ""
        ),
        cls="card",
    )

    if not modes:
        return Main(
            _nav(),
            H1("Progress"),
            coverage_card,
            H2("Failure modes"),
            P(
                "No annotations yet. Open a trial, save a label and "
                "note, and it will show up here grouped by label."
            ),
        )

    mode_cards = []
    for label, mode in modes.items():
        description = stored.get(label, {}).get("description", "")
        record_items = []
        for rec in mode["records"]:
            record_items.append(
                Li(
                    Div(
                        A(
                            f"{rec['run']}  ·  {rec['task_id']}",
                            href=(
                                f"/trial/{rec['run']}/{rec['task_id']}/"
                                f"{rec['trial']}"
                            ),
                        ),
                        Span(
                            f"  ({rec['updated']})",
                            style=(
                                "color: var(--text-muted); font-size: 0.85rem;"
                            ),
                        ),
                    ),
                    Pre(
                        rec["note"],
                        style=(
                            "font-size: 0.85rem; white-space: pre-wrap;"
                            " font-family: inherit; margin-top: 0.25rem;"
                        ),
                    )
                    if rec["note"]
                    else "",
                )
            )
        mode_cards.append(
            Section(
                Div(
                    H3(label),
                    _badge(str(mode["count"]), "unknown"),
                    style="display: flex; align-items: center; gap: 0.5rem;",
                ),
                P(
                    description,
                    style=(
                        "color: var(--text-muted); font-style: italic;"
                        " font-size: 0.9rem;"
                    ),
                )
                if description
                else "",
                Ul(*record_items, cls="check-list"),
                cls="card",
            )
        )

    return Main(
        _nav(),
        H1("Progress"),
        coverage_card,
        H2("Failure modes"),
        *mode_cards,
    )


@rt("/api/patterns")
async def get():  # noqa: F811
    """Failure modes with agent descriptions, plus coverage (JSON)."""
    return JSONResponse(_patterns_view(load_runs()))


@rt("/api/patterns", methods=["post"])
async def post(request: Request) -> JSONResponse:  # noqa: F811
    """Replace the stored taxonomy with the agent's latest version.

    Body: {label: {"description": str}}. Counts and records are
    always recomputed from annotations, so the agent only writes
    interpretation.
    """
    body = await request.json()
    save_patterns(body if isinstance(body, dict) else {})
    return JSONResponse(_patterns_view(load_runs()))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
