"""Tests for production trace persistence (CurationTraceStore).

The record shape is shared with the eval harness, so these tests also
pin the format the eval viewer renders.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from addon.application.services.curation_trace import (
    CurationTraceStore,
    TraceOutcome,
    render_proposal,
)
from addon.application.services.curator_agent import CurationSession
from addon.domain.entities.note import AddonNote, AddonNoteType, NoteId
from addon.domain.entities.proposals import (
    EditProposal,
    ProposedChangeSet,
)


def _seed_note() -> AddonNote:
    return AddonNote(
        front="<b>seed front</b>",
        back="seed back",
        tags=["seed"],
        notetype=AddonNoteType.BASIC,
        extra_fields={"Extra": "value"},
    )


def _session() -> CurationSession:
    before = AddonNote(
        front="What is the capital of France?",
        back="Paris",
        notetype=AddonNoteType.BASIC,
    )
    after = dataclasses.replace(before, tags=["geo"])
    change_set = ProposedChangeSet()
    change_set.add_edit(EditProposal(NoteId(1), before, after, "add tag"))
    edit_step = '{"thought": "edit it", "action": {"action": "propose_edit"}}'
    finish_step = '{"thought": "done", "action": {"action": "finish"}}'
    return CurationSession(
        change_set=change_set,
        transcript=[
            {"role": "user", "content": "seed"},
            {"role": "assistant", "content": edit_step},
            {"role": "user", "content": "Edit proposal recorded."},
            {"role": "assistant", "content": finish_step},
        ],
        summary="Added a tag.",
    )


def test_save_writes_full_record_with_outcome(tmp_path: Path) -> None:
    # Given
    store = CurationTraceStore(tmp_path, model="qwen", provider="openai")
    session = _session()
    seed = _seed_note()

    # When
    path = store.save(
        session,
        seed,
        NoteId(42),
        instruction="focus on tags",
        outcome=TraceOutcome(
            status="applied",
            approved=tuple(session.change_set),
        ),
    )

    # Then
    assert path.name == "note_42.trial0.json"
    assert path.parent.name.startswith("20")  # timestamped run dir
    record = json.loads(path.read_text())
    assert record["source"] == "production"
    assert record["model"] == "qwen"
    assert record["provider"] == "openai"
    assert record["task_id"] == "note_42"
    assert record["instruction"] == "focus on tags"
    assert record["passed"] is True
    assert record["summary"] == "Added a tag."
    assert record["stats"] == {"steps": 2}
    assert record["cluster"] == [
        {
            "id": 42,
            "front": "<b>seed front</b>",
            "back": "seed back",
            "tags": ["seed"],
            "notetype": "basic",
            "extra_fields": {"Extra": "value"},
        }
    ]
    assert record["transcript"] == session.transcript
    assert record["change_set"] == [
        render_proposal(p) for p in session.change_set
    ]
    assert record["outcome"]["status"] == "applied"
    assert record["outcome"]["approved"] == record["change_set"]
    assert record["outcome"]["rejected"] == []
    assert record["outcome"]["error"] is None


def test_save_rejected_session_records_human_verdict(tmp_path: Path) -> None:
    # Given
    store = CurationTraceStore(tmp_path, model="qwen", provider="openai")
    session = _session()

    # When
    path = store.save(
        session,
        _seed_note(),
        NoteId(42),
        None,
        TraceOutcome(status="rejected", rejected=tuple(session.change_set)),
    )

    # Then
    record = json.loads(path.read_text())
    assert record["outcome"]["status"] == "rejected"
    assert record["outcome"]["approved"] == []
    assert record["outcome"]["rejected"] == record["change_set"]


def test_save_failure_writes_metadata_only_record(tmp_path: Path) -> None:
    # Given
    store = CurationTraceStore(tmp_path, model="qwen", provider="openai")

    # When
    path = store.save_failure(NoteId(7), None, "connection refused")

    # Then
    record = json.loads(path.read_text())
    assert record["passed"] is False
    assert record["transcript"] == []
    assert record["change_set"] == []
    assert record["outcome"]["status"] == "failed"
    assert record["outcome"]["error"] == "connection refused"
