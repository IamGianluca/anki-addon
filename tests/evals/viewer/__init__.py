"""FastHTML viewer for curator eval results.

Load trial JSON files from tests/evals/results/ and render:
- Dashboard: all runs with aggregate pass rates
- Run detail: per-task breakdown with trial grid
- Trial detail: seed notes, transcript, checks, judge verdicts,
  change set

Run:  uv run python -m tests.evals.viewer
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fasthtml.common import (  # noqa: F401
    H1,
    H2,
    H3,
    H4,
    A,
    Button,
    Div,
    FastHTML,
    Header,
    Li,
    Main,
    P,
    Pre,
    Script,
    Section,
    Span,
    Style,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Title,
    Tr,
    Ul,
)

RESULTS_DIR = Path(__file__).parent.parent / "results"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


@dataclass
class RunSummary:
    """Aggregated stats for one eval run (one timestamped directory)."""

    stamp: str
    model: str = "unknown"
    elapsed: float = 0.0
    total_trials: int = 0
    passed_trials: int = 0
    tasks: dict[str, list[TrialRecord]] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        if self.total_trials == 0:
            return 0.0
        return self.passed_trials / self.total_trials


@dataclass
class TrialRecord:
    """One trial result loaded from JSON."""

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


def load_runs() -> list[RunSummary]:
    """Load all eval runs from the results directory, newest first."""
    if not RESULTS_DIR.exists():
        return []

    run_dirs = sorted(
        [p for p in RESULTS_DIR.iterdir() if p.is_dir()],
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
            )
            summary.total_trials += 1
            if trial.passed:
                summary.passed_trials += 1

            summary.tasks.setdefault(trial.task_id, []).append(trial)

        runs.append(summary)

    return runs


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


def _nav() -> Header:
    return Header(
        A("Dashboard", href="/"),
        Span("  |  ", style="margin: 0 0.5rem;"),
        Span(
            f"Results: {RESULTS_DIR.name}",
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
        return Main(_nav(), H1("Eval Viewer"), P("No eval results found."))

    rows = []
    for run in runs:
        rows.append(
            Tr(
                Td(_run_link(run)),
                Td(f"{run.pass_rate:.0%}"),
                Td(f"{run.passed_trials}/{run.total_trials}"),
                Td(f"{run.elapsed:.0f}s"),
                Td(str(len(run.tasks))),
            )
        )

    return Main(
        _nav(),
        H1("Eval Dashboard"),
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
    )


@rt("/run/{stamp}")
async def get(stamp: str):  # noqa: F811
    runs = load_runs()
    run = next((r for r in runs if r.stamp == stamp), None)
    if run is None:
        return Main(_nav(), H1("Run not found"))

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
    proposal_blocks = []
    for p in trial.change_set:
        ptype = p.get("type", "edit").upper()
        if ptype == "EDIT":
            proposal_blocks.append(
                Div(
                    H4(f"EDIT note {p.get('note_id')}"),
                    P(f"Rationale: {p.get('rationale', '')}"),
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
            )
        elif ptype == "CREATE":
            proposal_blocks.append(
                Div(
                    H4("CREATE"),
                    P(f"Rationale: {p.get('rationale', '')}"),
                    Pre(
                        json.dumps(p.get("note", {}), indent=2),
                        style="font-size: 0.8rem;",
                    ),
                    cls="proposal-block",
                )
            )
        else:
            proposal_blocks.append(
                Div(
                    H4(f"DELETE note {p.get('note_id')}"),
                    P(f"Rationale: {p.get('rationale', '')}"),
                    Pre(
                        json.dumps(p.get("before", {}), indent=2),
                        style="font-size: 0.8rem;",
                    ),
                    cls="proposal-block",
                )
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
                            json.dumps(
                                action, indent=2, ensure_ascii=False
                            ),
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
            P(trial.summary or "(none)"),
            cls="card",
        )
        if trial.summary
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
        Section(H3("Transcript"), *transcript_entries),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)
