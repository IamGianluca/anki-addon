import json

import pytest
from tests.fakes.note_fakes import FakeNoteRepository
from tests.fakes.openai_fakes import FakeCompletionProvider

from addon.application.services.curator_agent import (
    CuratorAgent,
)
from addon.application.services.curator_tools import CuratorTools
from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.entities.proposals import CreateProposal, EditProposal


def _step(action: dict, thought: str = "reasoning") -> str:
    return json.dumps({"thought": thought, "action": action})


@pytest.fixture
def adam_cluster() -> dict[int, AddonNote]:
    return {
        1: AddonNote(
            front="What does beta_2 control in Adam?",
            back="Decay rate of the second moment estimate.",
            tags=["ml", "optimizers"],
        ),
        2: AddonNote(
            front="What does beta_1 control in Adam?",
            back="Decay rate of the first moment estimate.",
            tags=["ml", "optimizers"],
        ),
    }


def _run_agent(
    responses: list[str],
    cluster: dict[int, AddonNote],
    seed: int = 1,
    max_steps: int = 15,
    instruction: str | None = None,
):
    client = FakeCompletionProvider(responses)
    tools = CuratorTools(FakeNoteRepository(cluster))
    agent = CuratorAgent(client, tools, max_steps=max_steps)
    session = agent.run(NoteId(seed), instruction=instruction)
    return session, client


def test_agent_explores_proposes_and_finishes(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [
        _step({"action": "search_notes", "query": "beta"}),
        _step({"action": "read_note", "note_id": 2}),
        _step(
            {
                "action": "propose_edit",
                "note_id": 2,
                "front": "What does beta_1 control in Adam?",
                "back": "Decay rate of the first moment "
                "(gradient) estimate. Typical value: 0.9.",
                "tags": ["ml", "optimizers"],
                "rationale": "add the typical value",
            }
        ),
        _step({"action": "finish", "summary": "added typical value"}),
    ]

    # When
    session, _ = _run_agent(responses, adam_cluster)

    # Then
    assert session.summary == "added typical value"
    (edit,) = [p for p in session.change_set if isinstance(p, EditProposal)]
    assert edit.note_id == 2
    assert "0.9" in edit.after.back
    # tool observations were fed back into the conversation
    assert any(
        "beta_1 control" in m["content"]
        for m in session.transcript
        if m["role"] == "user"
    )


def test_seed_note_content_is_in_the_first_prompt(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [_step({"action": "finish", "summary": "nothing to do"})]

    # When
    _, client = _run_agent(
        responses, adam_cluster, instruction="focus on tags"
    )

    # Then
    first_messages = client.prompts_received[0]
    assert first_messages[0]["role"] == "system"
    seed_message = first_messages[1]["content"]
    assert "What does beta_2 control in Adam?" in seed_message
    assert "Additional instruction: focus on tags" in seed_message


def test_agent_stops_at_max_steps_without_finish(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [
        _step({"action": "search_notes", "query": "beta"}),
        _step({"action": "search_notes", "query": "optimizers"}),
    ]

    # When
    session, _ = _run_agent(responses, adam_cluster, max_steps=2)

    # Then
    assert session.summary is None
    assert len(session.change_set) == 0


def test_invalid_json_is_fed_back_and_loop_recovers(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [
        "this is not json",
        _step({"action": "finish", "summary": "recovered"}),
    ]

    # When
    session, client = _run_agent(responses, adam_cluster)

    # Then
    assert session.summary == "recovered"
    second_call_messages = client.prompts_received[1]
    assert any(
        "did not match the required schema" in m["content"]
        for m in second_call_messages
        if m["role"] == "user"
    )


def test_tool_error_becomes_observation(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [
        _step({"action": "read_note", "note_id": 999}),
        _step({"action": "finish", "summary": "gave up"}),
    ]

    # When
    session, client = _run_agent(responses, adam_cluster)

    # Then
    assert session.summary == "gave up"
    assert len(session.change_set) == 0
    second_call_messages = client.prompts_received[1]
    assert any(
        "error: note 999 not found" in m["content"]
        for m in second_call_messages
        if m["role"] == "user"
    )


def test_split_action_flows_through_to_change_set(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [
        _step(
            {
                "action": "propose_split",
                "note_id": 1,
                "kept_front": "What does beta_2 control in Adam?",
                "kept_back": "Decay rate of the second moment estimate.",
                "kept_tags": ["ml", "optimizers"],
                "new_notes": [
                    {
                        "front": "Typical value of beta_2 in Adam?",
                        "back": "0.999",
                    }
                ],
                "rationale": "separate the typical value fact",
            }
        ),
        _step({"action": "finish", "summary": "split done"}),
    ]

    # When
    session, _ = _run_agent(responses, adam_cluster)

    # Then
    edits = [p for p in session.change_set if isinstance(p, EditProposal)]
    creates = [p for p in session.change_set if isinstance(p, CreateProposal)]
    assert len(edits) == 1
    assert len(creates) == 1
    # notetype omitted in the action: inherits the original's type
    assert creates[0].note.notetype == edits[0].before.notetype


def test_structured_output_schema_is_requested(
    adam_cluster: dict[int, AddonNote],
) -> None:
    # Given
    responses = [_step({"action": "finish", "summary": "done"})]

    # When
    _, client = _run_agent(responses, adam_cluster)

    # Then
    kwargs = client.kwargs_received[0]
    assert kwargs["response_format"]["type"] == "json_schema"
