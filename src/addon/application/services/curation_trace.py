"""Persistence of curator session traces for offline review.

Every production curation session writes one JSON trace file, in the
same record shape the eval harness writes for trials — the eval viewer
renders both. The one thing production records add is the `outcome`:
in evals the graders decide, in production the user decides, and that
decision (which proposals were approved, cancelled, or rejected) is
the production grade. Rejected and cancelled traces are the mine for
error analysis: each one is a real session where the agent's work was
not good enough.

Records are plain JSON files, one per session, so they can be copied
between machines and exported to any tracing platform later.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from ...domain.entities.note import AddonNote, NoteId
from ...domain.entities.proposals import (
    CreateProposal,
    EditProposal,
    Proposal,
)
from .curator_agent import CurationSession

TraceStatus = Literal[
    "applied", "rejected", "cancelled", "no_changes", "failed"
]


@dataclass(frozen=True)
class TraceOutcome:
    """What the user decided about a session's change set.

    The human's decision is the production grade: `applied` means the
    proposals were good enough to accept; `rejected`, `cancelled`, and
    `no_changes` are the traces to mine for failure modes; `failed`
    means the session crashed before finishing.
    """

    status: TraceStatus
    approved: tuple[Proposal, ...] = ()
    rejected: tuple[Proposal, ...] = ()
    error: str | None = None


def render_note(note: AddonNote) -> dict:
    """Serialize a note for a trace record."""
    return {
        "front": note.front,
        "back": note.back,
        "tags": note.tags or [],
        "notetype": note.notetype.value,
        "extra_fields": note.extra_fields,
    }


def render_proposal(proposal: Proposal) -> dict:
    """Serialize a proposal for a trace record.

    The shape is the one the eval harness writes, so records from
    production and evals render identically in the viewer.
    """
    if isinstance(proposal, EditProposal):
        return {
            "type": "edit",
            "note_id": proposal.note_id,
            "rationale": proposal.rationale,
            "before": render_note(proposal.before),
            "after": render_note(proposal.after),
        }
    if isinstance(proposal, CreateProposal):
        return {
            "type": "create",
            "rationale": proposal.rationale,
            "note": render_note(proposal.note),
        }
    return {
        "type": "delete",
        "note_id": proposal.note_id,
        "rationale": proposal.rationale,
        "before": render_note(proposal.before),
    }


class CurationTraceStore:
    """Writes one JSON trace per curation session.

    Traces land in `<directory>/<stamp>/note_<seed_id>.trial0.json`,
    mirroring the eval results layout so the eval viewer can render
    them by pointing it at the directory.
    """

    def __init__(
        self, directory: Path, model: str, provider: str = "unknown"
    ) -> None:
        self._directory = directory
        self._model = model
        self._provider = provider

    def save(
        self,
        session: CurationSession,
        seed_note: AddonNote,
        seed_note_id: NoteId,
        instruction: str | None,
        outcome: TraceOutcome,
    ) -> Path:
        """Persist a completed session and what the user did with it."""
        record = {
            "source": "production",
            "task_id": f"note_{seed_note_id}",
            "trial": 0,
            "passed": outcome.status != "failed",
            "score": 1.0 if outcome.status != "failed" else 0.0,
            "stats": {"steps": _count_steps(session.transcript)},
            "summary": session.summary,
            "cluster": [{"id": seed_note_id, **render_note(seed_note)}],
            "change_set": [render_proposal(p) for p in session.change_set],
            "transcript": session.transcript,
            "model": self._model,
            "provider": self._provider,
            "instruction": instruction,
            "outcome": {
                "status": outcome.status,
                "approved": [render_proposal(p) for p in outcome.approved],
                "rejected": [render_proposal(p) for p in outcome.rejected],
                "error": outcome.error,
            },
        }
        return self._write(record, seed_note_id)

    def save_failure(
        self, seed_note_id: NoteId, instruction: str | None, error: str
    ) -> Path:
        """Persist a session that crashed before completing.

        The agent loop holds its transcript locally and loses it on an
        exception, so a failed trace carries metadata and the error
        only — still enough to spot recurring infrastructure failures.
        """
        record = {
            "source": "production",
            "task_id": f"note_{seed_note_id}",
            "trial": 0,
            "passed": False,
            "score": 0.0,
            "stats": {},
            "summary": None,
            "cluster": [],
            "change_set": [],
            "transcript": [],
            "model": self._model,
            "provider": self._provider,
            "instruction": instruction,
            "outcome": {
                "status": "failed",
                "approved": [],
                "rejected": [],
                "error": error,
            },
        }
        return self._write(record, seed_note_id)

    def _write(self, record: dict, seed_note_id: NoteId) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = self._directory / stamp
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / f"note_{seed_note_id}.trial0.json"
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        )
        return path


def _count_steps(transcript: list[dict]) -> int:
    return sum(1 for m in transcript if m.get("role") == "assistant")
