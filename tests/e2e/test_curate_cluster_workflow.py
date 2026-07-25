import json

import pytest
from tests.fakes.aqt_fakes import FakeCollection
from tests.fakes.openai_fakes import FakeCompletionProvider

from addon.application.services.curator_agent import CuratorAgent
from addon.application.services.curator_tools import CuratorTools
from addon.application.use_cases.apply_curation import apply_proposals
from addon.domain.entities.note import NoteId
from addon.infrastructure.persistence.anki_note_repository import (
    AnkiNoteRepository,
)


def _step(action: dict) -> str:
    return json.dumps({"thought": "reasoning", "action": action})


@pytest.mark.slow
def test_complete_curation_workflow(collection: FakeCollection) -> None:
    """E2E test: full curation journey from agent session to applied
    changes in the collection.

    1. CuratorAgent explores the collection (scripted LLM responses)
    2. Proposals accumulate in the session's change set
    3. User approves all proposals in review
    4. apply_proposals persists them to the collection
    """
    # Given: an agent scripted to edit note 1 and create a new note
    responses = [
        _step({"action": "search_notes", "query": "question"}),
        _step({"action": "read_note", "note_id": 1}),
        _step(
            {
                "action": "propose_edit",
                "note_id": 1,
                "front": "Question 1",
                "back": "Answer 1 (expanded)",
                "tags": ["reviewed"],
                "rationale": "expand the answer",
            }
        ),
        _step(
            {
                "action": "propose_create",
                "front": "Question 1 follow-up",
                "back": "Follow-up answer",
                "tags": ["reviewed"],
                "notetype": "basic",
                "rationale": "gap in the cluster",
            }
        ),
        _step({"action": "finish", "summary": "edited note 1, added one"}),
    ]
    repository = AnkiNoteRepository(collection)
    agent = CuratorAgent(
        FakeCompletionProvider(responses), CuratorTools(repository)
    )

    # When: run the session, approve everything, apply
    session = agent.run(NoteId(1))
    assert session.summary == "edited note 1, added one"

    approved = list(session.change_set)
    report = apply_proposals(repository, approved, deck_name="Default")

    # Then: changes persisted to the collection
    assert report.edits == 1
    assert report.creates == 1

    edited_note = collection.get_note(1)
    assert edited_note["Back"] == "Answer 1 (expanded)"
    assert edited_note.tags == ["reviewed"]

    created_ids = collection.find_notes("follow-up")
    assert len(created_ids) == 1
    created_note = collection.get_note(created_ids[0])
    assert created_note["Front"] == "Question 1 follow-up"
    assert created_note.tags == ["reviewed"]
