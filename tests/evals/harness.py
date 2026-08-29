"""Eval harness for the CuratorAgent.

Loads task definitions from JSON files in tasks/, runs the real
CuratorAgent with a real LLM client against a fresh in-memory
repository per trial, and persists one JSON record per trial (cluster,
change set, full transcript, grade) for later reading.

Grading lives in graders.py; this module owns task definitions, trial
execution, and record keeping. See README.md for how to run evals and
how to write tasks.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from pydantic import BaseModel, Field, model_validator
from tests.fakes.note_fakes import FakeNoteRepository

from addon.application.services.curation_trace import (
    render_note,
    render_proposal,
)
from addon.application.services.curator_agent import (
    CurationSession,
    CuratorAgent,
)
from addon.application.services.curator_tools import CuratorTools
from addon.domain.entities.note import AddonNote, AddonNoteType, NoteId
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
    Proposal,
)

if TYPE_CHECKING:
    from tests.evals.graders import GradeResult

    from addon.application.protocols import CompletionProvider

TASKS_DIR = Path(__file__).parent / "tasks"


class TaskNote(BaseModel):
    """One note of the cluster a task seeds the repository with."""

    id: int
    front: str
    back: str = ""
    tags: list[str] = []
    notetype: Literal["basic", "cloze"] = "basic"
    extra_fields: dict[str, str] = {}


class Expectation(BaseModel):
    """Deterministic success criteria for a task.

    edits/creates/deletes are [min, max] ranges on the number of
    proposals of that type; None means "don't check". facts are strings
    that must appear in the notes after applying the change set,
    matched on word boundaries ("0.9" does not match "0.999").
    must_not_contain are words that must not appear in the proposed
    notes (edited and created ones only — the agent is only
    responsible for what it writes), matched the same way.
    no_dollar_math requires the proposed notes to contain no '$'
    character at all — the word-boundary machinery above cannot see
    a $ glued to word characters — so clusters that opt in must not
    contain legitimate dollar amounts.
    """

    finish: bool = True
    empty: bool = False
    edits: Optional[tuple[int, int]] = None
    creates: Optional[tuple[int, int]] = None
    deletes: Optional[tuple[int, int]] = None
    must_touch: list[int] = []
    must_not_touch: list[int] = []
    facts: list[str] = []
    must_not_contain: list[str] = []
    no_dollar_math: bool = False
    read_before_propose: bool = True


class ReferenceProposal(BaseModel):
    """One entry of a task's human-authored reference solution.

    A split is expressed as its outcome: an edit of the original note
    plus one create per new note.
    """

    type: Literal["edit", "create", "delete"]
    note_id: Optional[int] = None
    front: Optional[str] = None
    back: Optional[str] = None
    tags: Optional[list[str]] = None
    notetype: Optional[Literal["basic", "cloze"]] = None
    rationale: str = "reference solution"

    @model_validator(mode="after")
    def _required_fields_present(self) -> "ReferenceProposal":
        if self.type in ("edit", "delete") and self.note_id is None:
            raise ValueError(f"{self.type} proposal requires note_id")
        if self.type == "create" and self.front is None:
            raise ValueError("create proposal requires front")
        return self


class EvalTask(BaseModel):
    """One eval task: a seeded cluster, success criteria, and a
    reference solution proving the task is solvable."""

    id: str
    suite: Literal["capability", "regression"] = "capability"
    desc: str
    seed_note_id: int
    instruction: Optional[str] = None
    trials: int = Field(default=1, ge=1)
    max_steps: int = 15
    notes: list[TaskNote] = Field(min_length=1)
    expect: Expectation = Field(default_factory=Expectation)
    judge_assertions: list[str] = []
    reference: list[ReferenceProposal] = []


def load_task(path: Path) -> EvalTask:
    return EvalTask.model_validate_json(path.read_text())


@dataclass
class TrialOutcome:
    """Everything a grader or record needs from one trial: the session
    the agent produced and the notes it started from."""

    task: EvalTask
    session: CurationSession
    seeded_notes: dict[int, AddonNote]


def run_trial(task: EvalTask, client: CompletionProvider) -> TrialOutcome:
    """Run one trial of a task.

    The repository is rebuilt from the task definition on every call,
    so no state leaks between trials. The agent matches production: the
    real CuratorAgent, the real CuratorTools, the caller's (real) LLM
    client — only the note collection is a fake.
    """
    notes = {note.id: _to_domain(note) for note in task.notes}
    tools = CuratorTools(FakeNoteRepository(notes))
    agent = CuratorAgent(client, tools, max_steps=task.max_steps)
    session = agent.run(
        NoteId(task.seed_note_id), instruction=task.instruction
    )
    return TrialOutcome(task=task, session=session, seeded_notes=notes)


def build_reference_proposals(task: EvalTask) -> list[Proposal]:
    """Instantiate a task's reference solution as domain proposals, so
    test_task_files can verify it passes the outcome graders."""
    notes_by_id = {note.id: note for note in task.notes}
    proposals: list[Proposal] = []
    for ref in task.reference:
        if ref.type == "delete":
            before = _to_domain(notes_by_id[ref.note_id])
            proposals.append(
                DeleteProposal(NoteId(ref.note_id), before, ref.rationale)
            )
        elif ref.type == "edit":
            before = _to_domain(notes_by_id[ref.note_id])
            after = dataclasses.replace(
                before,
                front=ref.front if ref.front is not None else before.front,
                back=ref.back if ref.back is not None else before.back,
                tags=ref.tags if ref.tags is not None else before.tags,
            )
            proposals.append(
                EditProposal(NoteId(ref.note_id), before, after, ref.rationale)
            )
        else:
            proposals.append(
                CreateProposal(
                    AddonNote(
                        front=ref.front or "",
                        back=ref.back or "",
                        tags=ref.tags or [],
                        notetype=AddonNoteType(ref.notetype or "basic"),
                    ),
                    ref.rationale,
                )
            )
    return proposals


def write_trial_record(
    results_dir: Path,
    trial_index: int,
    outcome: TrialOutcome,
    grade: GradeResult,
    model: str | None = None,
) -> Path:
    """Persist one trial's full record as JSON. The record is the
    artifact to read when a failure looks unfair — never trust a score
    nobody has spot-checked in the transcripts."""
    record = {
        "task_id": outcome.task.id,
        "trial": trial_index,
        "passed": grade.passed,
        "score": grade.score,
        "checks": [
            {"name": c.name, "verdict": c.verdict, "reason": c.reason}
            for c in grade.checks
        ],
        "failures": grade.failures,  # backward compat
        "unknowns": grade.unknowns,  # backward compat
        "stats": grade.stats,
        "summary": outcome.session.summary,
        "cluster": [
            {"id": note_id, **render_note(note)}
            for note_id, note in outcome.seeded_notes.items()
        ],
        "change_set": [render_proposal(p) for p in outcome.session.change_set],
        "transcript": outcome.session.transcript,
    }
    if model is not None:
        record["model"] = model
    path = results_dir / f"{outcome.task.id}.trial{trial_index}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return path


def _to_domain(note: TaskNote) -> AddonNote:
    return AddonNote(
        front=note.front,
        back=note.back,
        tags=list(note.tags),
        notetype=AddonNoteType(note.notetype),
        extra_fields=dict(note.extra_fields),
    )
