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
class GradeResult:
    """The grade of one trial.

    failures: hard violations; the trial passes iff this is empty.
    unknowns: judge assertions the judge could not decide — recorded
        separately, never silently counted as pass or fail.
    stats: tracked metrics that don't affect passing (step count,
        schema errors, proposal counts).
    """

    failures: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures

    def merge(self, other: "GradeResult") -> None:
        self.failures.extend(other.failures)
        self.unknowns.extend(other.unknowns)
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
            result.failures.append(
                f"expected an empty change set, got {len(proposals)} "
                "proposal(s)"
            )
        return result

    _check_count(result, "edits", len(edits), expect.edits)
    _check_count(result, "creates", len(creates), expect.creates)
    _check_count(result, "deletes", len(deletes), expect.deletes)

    touched = {p.note_id for p in [*edits, *deletes]}
    for note_id in expect.must_touch:
        if note_id not in touched:
            result.failures.append(
                f"note {note_id} should have been edited or deleted"
            )
    for note_id in expect.must_not_touch:
        if note_id in touched:
            result.failures.append(
                f"note {note_id} should not have been touched"
            )

    final_text = _final_state_text(task, proposals)
    for fact in expect.facts:
        if fact.lower() not in final_text:
            result.failures.append(
                f"fact {fact!r} is missing from the notes after "
                "applying the change set"
            )

    for proposal in edits:
        if (
            proposal.before.notetype == AddonNoteType.CLOZE
            and _CLOZE_RE.search(proposal.before.front)
            and not _CLOZE_RE.search(proposal.after.front)
        ):
            result.failures.append(
                f"edit to cloze note {proposal.note_id} drops the "
                "cloze markup from the front"
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
        result.failures.append(
            "agent reached max_steps without calling finish"
        )

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
            result.failures.append(
                f"{kind} on note {note_id} without reading it first"
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

_JUDGE_SYSTEM_PROMPT = """\
You are grading an LLM flashcard-curation agent. You will be shown a
cluster of Anki notes, the changes the agent proposed, and ONE
assertion about those changes. Judge only that assertion, based only
on what you are shown.

Respond with JSON: {"verdict": "pass"|"fail"|"unknown", "reason": ...}.
Use "unknown" whenever the information shown is insufficient to decide
confidently — never guess."""


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
        if verdict == "fail":
            result.failures.append(f"judge rejected {assertion!r}: {reason}")
        elif verdict == "unknown":
            result.unknowns.append(
                f"judge could not decide {assertion!r}: {reason}"
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
            {"role": "system", "content": _JUDGE_SYSTEM_PROMPT},
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
    if not low <= actual <= high:
        result.failures.append(
            f"expected {label} in [{low}, {high}], got {actual}"
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
