"""Graders for curator eval trials.

Three families, in order of preference:

- grade_outcome: deterministic checks on the change set and on the
  final state of the cluster after applying it. This is the grade that
  matters — proposals are what the user reviews and applies.
- grade_transcript: deterministic rule-adherence checks visible in the
  conversation (did the agent finish, did it read notes before
  proposing changes to them). Rule adherence, not solution shape:
  nothing here prescribes which actions a correct run must take.
- grade_by_judge: one LLM call per task assertion, with an explicit
  "unknown" verdict so the judge never has to guess.

Deterministic where possible, model-based where necessary.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from addon.domain.entities.note import AddonNoteType
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
    Proposal,
)

if TYPE_CHECKING:
    from tests.evals.harness import EvalTask, TrialOutcome

    from addon.application.protocols import CompletionProvider
    from addon.application.services.curator_agent import CurationSession

_TAG_RE = re.compile(r"<[^>]+>")
_CLOZE_RE = re.compile(r"\{\{c\d+::")
_SCHEMA_ERROR_MARKER = "did not match the required schema"


@dataclass
class Check:
    """One graded dimension of a trial.

    name: short label for the dimension (e.g. "no_deletes", "atomic").
    verdict: pass, fail, or unknown (judge could not decide).
    reason: explanation — always present, even for passes.
    """

    name: str
    verdict: str  # "pass" | "fail" | "unknown"
    reason: str


@dataclass
class GradeResult:
    """The grade of one trial.

    checks: individual graded dimensions — the trial passes iff all
        checks pass (no fails, no unknowns). Each check carries a
        human-readable name and reason for the summary output.
    stats: tracked metrics that don't affect passing (step count,
        schema errors, proposal counts).
    """

    checks: list[Check] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.verdict == "pass" for c in self.checks)

    @property
    def score(self) -> float:
        """Fraction of non-unknown checks that passed.

        Unknowns are excluded from the denominator — they represent
        missing information, not a failure. With zero decidable checks
        the score is 0.0.
        """
        decidable = [c for c in self.checks if c.verdict != "unknown"]
        if not decidable:
            return 0.0
        passed = sum(1 for c in decidable if c.verdict == "pass")
        return passed / len(decidable)

    @property
    def failures(self) -> list[str]:
        """Backward-compatible view: fail reasons as a flat list."""
        return [
            f"{c.name}: {c.reason}" if c.reason else c.name
            for c in self.checks
            if c.verdict == "fail"
        ]

    @property
    def unknowns(self) -> list[str]:
        """Backward-compatible view: unknown reasons as a flat list."""
        return [
            f"{c.name}: {c.reason}" if c.reason else c.name
            for c in self.checks
            if c.verdict == "unknown"
        ]

    def add_check(self, name: str, verdict: str, reason: str = "") -> None:
        """Add a single check result."""
        self.checks.append(Check(name=name, verdict=verdict, reason=reason))

    def merge(self, other: "GradeResult") -> None:
        self.checks.extend(other.checks)
        self.stats.update(other.stats)


def grade_trial(
    task: EvalTask,
    outcome: TrialOutcome,
    judge_client: CompletionProvider | None = None,
) -> GradeResult:
    """Grade one trial with all applicable grader families."""
    result = grade_outcome(task, list(outcome.session.change_set))
    result.merge(grade_transcript(task, outcome.session))
    if judge_client is not None:
        result.merge(grade_by_judge(task, outcome.session, judge_client))
    return result


def grade_outcome(task: EvalTask, proposals: list[Proposal]) -> GradeResult:
    """Grade the change set and the cluster state it produces.

    Each dimension is a separate check so partial credit is visible:
    correct edit count, correct create count, correct delete count,
    must-touch, must-not-touch, fact preservation, and cloze safety.

    Also used by test_task_files to validate reference solutions, so it
    must not look at the transcript.
    """
    result = GradeResult()
    expect = task.expect
    edits = [p for p in proposals if isinstance(p, EditProposal)]
    creates = [p for p in proposals if isinstance(p, CreateProposal)]
    deletes = [p for p in proposals if isinstance(p, DeleteProposal)]
    result.stats.update(
        n_edits=len(edits), n_creates=len(creates), n_deletes=len(deletes)
    )

    if expect.empty:
        if proposals:
            result.add_check(
                name="empty_change_set",
                verdict="fail",
                reason=f"expected an empty change set, got "
                f"{len(proposals)} proposal(s)",
            )
        else:
            result.add_check(name="empty_change_set", verdict="pass")
        return result

    _check_count(result, "edits", len(edits), expect.edits)
    _check_count(result, "creates", len(creates), expect.creates)
    _check_count(result, "deletes", len(deletes), expect.deletes)

    touched = {p.note_id for p in [*edits, *deletes]}
    for note_id in expect.must_touch:
        if note_id not in touched:
            result.add_check(
                name=f"must_touch_{note_id}",
                verdict="fail",
                reason=f"note {note_id} should have been edited or deleted",
            )
        else:
            result.add_check(name=f"must_touch_{note_id}", verdict="pass")
    for note_id in expect.must_not_touch:
        if note_id in touched:
            result.add_check(
                name=f"must_not_touch_{note_id}",
                verdict="fail",
                reason=f"note {note_id} should not have been touched",
            )
        else:
            result.add_check(name=f"must_not_touch_{note_id}", verdict="pass")

    final_text = _final_state_text(task, proposals)
    for fact in expect.facts:
        if fact.lower() not in final_text:
            result.add_check(
                name=f"fact_{fact}",
                verdict="fail",
                reason=f"fact {fact!r} is missing from the notes after "
                "applying the change set",
            )
        else:
            result.add_check(name=f"fact_{fact}", verdict="pass")

    for proposal in edits:
        if (
            proposal.before.notetype == AddonNoteType.CLOZE
            and _CLOZE_RE.search(proposal.before.front)
            and not _CLOZE_RE.search(proposal.after.front)
        ):
            result.add_check(
                name=f"cloze_safe_{proposal.note_id}",
                verdict="fail",
                reason=f"edit to cloze note {proposal.note_id} drops the "
                "cloze markup from the front",
            )
    return result


def grade_transcript(task: EvalTask, session: CurationSession) -> GradeResult:
    """Check agent behavior that is only visible in the conversation.

    read_before_propose enforces a rule stated in the agent's system
    prompt; the seed note is exempt because its content is already in
    the first user message, so reading it first would be ceremony.
    """
    result = GradeResult()
    if task.expect.finish and session.summary is None:
        result.add_check(
            name="finished",
            verdict="fail",
            reason="agent reached max_steps without calling finish",
        )
    elif task.expect.finish:
        result.add_check(name="finished", verdict="pass")

    read_ids: set[int] = set()
    reported: set[tuple[str, int]] = set()
    n_steps = 0
    n_schema_errors = 0
    for message in session.transcript:
        if message["role"] == "user":
            if _SCHEMA_ERROR_MARKER in message["content"]:
                n_schema_errors += 1
            continue
        n_steps += 1
        try:
            step = json.loads(message["content"])
        except json.JSONDecodeError:
            continue
        action = step.get("action", {})
        kind = action.get("action")
        note_id = action.get("note_id")
        if kind == "read_note" and note_id is not None:
            read_ids.add(note_id)
        elif (
            kind in ("propose_edit", "propose_delete", "propose_split")
            and note_id is not None
            and note_id != task.seed_note_id
            and note_id not in read_ids
            and task.expect.read_before_propose
            and (kind, note_id) not in reported
        ):
            reported.add((kind, note_id))
            result.add_check(
                name=f"read_before_{kind}_{note_id}",
                verdict="fail",
                reason=f"{kind} on note {note_id} without reading it first",
            )

    result.stats.update(
        n_steps=n_steps,
        n_schema_errors=n_schema_errors,
        finished=session.summary is not None,
    )
    return result


_JUDGE_VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "fail", "unknown"]},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "reason"],
    "additionalProperties": False,
}


@lru_cache(maxsize=1)
def _get_judge_prompt() -> str:
    return (Path(__file__).parent / "judge_prompt.md").read_text()


def grade_by_judge(
    task: EvalTask,
    session: CurationSession,
    judge_client: CompletionProvider,
) -> GradeResult:
    """Judge each of the task's assertions in a separate LLM call, so
    no single call trades one dimension off against another."""
    result = GradeResult()
    for assertion in task.judge_assertions:
        verdict, reason = _judge_assertion(
            task, session, judge_client, assertion
        )
        # Use a short name derived from the assertion for the check label.
        short_name = assertion[:40].replace(" ", "_")
        result.add_check(
            name=f"judge_{short_name}",
            verdict=verdict,
            reason=reason,
        )
    return result


def _judge_assertion(
    task: EvalTask,
    session: CurationSession,
    judge_client: CompletionProvider,
    assertion: str,
) -> tuple[str, str]:
    response = judge_client.run(
        [
            {"role": "system", "content": _get_judge_prompt()},
            {
                "role": "user",
                "content": (
                    f"Task: {task.desc}\n\n"
                    f"## Cluster before curation\n"
                    f"{_render_cluster(task)}\n\n"
                    f"## Proposed changes\n"
                    f"{_render_change_set(session)}\n\n"
                    f"## Agent's closing summary\n"
                    f"{session.summary or '(none)'}\n\n"
                    f"## Assertion\n{assertion}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "judge_verdict",
                "schema": _JUDGE_VERDICT_SCHEMA,
            },
        },
    )
    try:
        parsed = json.loads(response)
        verdict = parsed["verdict"]
        reason = str(parsed["reason"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return "unknown", f"unparseable judge response: {response[:200]}"
    if verdict not in ("pass", "fail", "unknown"):
        return "unknown", f"unexpected verdict {verdict!r}"
    return verdict, reason


def _check_count(
    result: GradeResult,
    label: str,
    actual: int,
    expected: tuple[int, int] | None,
) -> None:
    if expected is None:
        return
    low, high = expected
    if low <= actual <= high:
        result.add_check(name=label, verdict="pass")
    else:
        result.add_check(
            name=label,
            verdict="fail",
            reason=f"expected {label} in [{low}, {high}], got {actual}",
        )


def _final_state_text(task: EvalTask, proposals: list[Proposal]) -> str:
    """Plain text of every note in the cluster after applying the
    change set — the state facts are checked against."""
    edited = {
        p.note_id: p.after for p in proposals if isinstance(p, EditProposal)
    }
    deleted = {p.note_id for p in proposals if isinstance(p, DeleteProposal)}
    parts = [
        _plain(after.front, after.back, after.extra_fields)
        for note_id, after in edited.items()
        if note_id not in deleted
    ]
    parts += [
        _plain(note.front, note.back, note.extra_fields)
        for note in task.notes
        if note.id not in edited and note.id not in deleted
    ]
    parts += [
        _plain(p.note.front, p.note.back, p.note.extra_fields)
        for p in proposals
        if isinstance(p, CreateProposal)
    ]
    return " ".join(parts).lower()


def _plain(front: str, back: str, extra_fields: dict[str, str]) -> str:
    text = f"{front} {back} {' '.join(extra_fields.values())}"
    return html.unescape(_TAG_RE.sub("", text))


def _render_cluster(task: EvalTask) -> str:
    lines = []
    for note in task.notes:
        lines.append(f"Note {note.id} [{note.notetype}] tags={note.tags}")
        lines.append(f"  Front: {note.front}")
        lines.append(f"  Back: {note.back}")
        for name, value in note.extra_fields.items():
            lines.append(f"  {name}: {value}")
    return "\n".join(lines)


def _render_change_set(session: CurationSession) -> str:
    blocks = []
    for proposal in session.change_set:
        if isinstance(proposal, EditProposal):
            blocks.append(
                f"EDIT note {proposal.note_id} "
                f"(rationale: {proposal.rationale})\n"
                f"  old front: {proposal.before.front}\n"
                f"  new front: {proposal.after.front}\n"
                f"  old back: {proposal.before.back}\n"
                f"  new back: {proposal.after.back}"
            )
        elif isinstance(proposal, CreateProposal):
            blocks.append(
                f"CREATE {proposal.note.notetype.value} note "
                f"(rationale: {proposal.rationale})\n"
                f"  front: {proposal.note.front}\n"
                f"  back: {proposal.note.back}"
            )
        else:
            blocks.append(
                f"DELETE note {proposal.note_id} "
                f"(rationale: {proposal.rationale})\n"
                f"  front was: {proposal.before.front}"
            )
    return "\n\n".join(blocks) if blocks else "No changes proposed."
