from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from ...domain.entities.note import NoteId
from ...domain.entities.proposals import ProposedChangeSet
from ...infrastructure.llm.schemas import (
    AgentAction,
    AgentStep,
    FinishAction,
    ProposeCreateAction,
    ProposeDeleteAction,
    ProposeEditAction,
    ProposeSplitAction,
    ReadNoteAction,
    SearchNotesAction,
)
from ..protocols import CompletionProvider
from .curator_tools import CuratorTools


@dataclass
class CurationSession:
    """The result of a curator run.

    Attributes:
        change_set: The proposals accumulated during the session. Empty
            if the agent found nothing worth changing.
        transcript: The full message history, for review and debugging.
        summary: The agent's closing summary, or None if the loop hit
            max_steps without the agent calling finish.
    """

    change_set: ProposedChangeSet
    transcript: list[dict]
    summary: str | None


class CuratorAgent:
    """ReAct-style curation loop over a CompletionProvider.

    Each turn the model returns one structured AgentStep (validated
    against the JSON schema); the agent dispatches the action to
    CuratorTools and feeds the observation back as the next user
    message. The loop ends when the model calls finish or max_steps is
    reached.

    Invalid model output (unparseable JSON) is fed back as an error
    observation instead of raising, so a single bad turn does not kill
    the session.
    """

    def __init__(
        self,
        client: CompletionProvider,
        tools: CuratorTools,
        max_steps: int = 15,
    ) -> None:
        self._client = client
        self._tools = tools
        self._max_steps = max_steps

    def run(
        self, seed_note_id: NoteId, instruction: str | None = None
    ) -> CurationSession:
        """Run the curation loop seeded with the note the user is
        editing, plus an optional free-text instruction."""
        messages = self._initial_messages(seed_note_id, instruction)
        summary = None
        for _ in range(self._max_steps):
            response = self._client.run(
                prompt=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "agent_step",
                        "schema": AgentStep.model_json_schema(),
                    },
                },
            )
            messages.append({"role": "assistant", "content": response})
            try:
                step = AgentStep.model_validate_json(response)
            except ValidationError as e:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "error: your response did not match the "
                            "required schema "
                            f"({str(e)[:300]}). Respond with exactly "
                            "one action as specified."
                        ),
                    }
                )
                continue
            if isinstance(step.action, FinishAction):
                summary = step.action.summary
                break
            observation = self._dispatch(step.action)
            messages.append({"role": "user", "content": observation})
        return CurationSession(self._tools.change_set, messages, summary)

    def _initial_messages(
        self, seed_note_id: NoteId, instruction: str | None
    ) -> list[dict]:
        seed_content = self._tools.read_note(seed_note_id)
        user_message = (
            "Here is the note I am editing. Curate it together with "
            f"its cluster of related notes.\n\n{seed_content}"
        )
        if instruction:
            user_message += f"\n\nAdditional instruction: {instruction}"
        return [
            {"role": "system", "content": _get_system_prompt()},
            {"role": "user", "content": user_message},
        ]

    def _dispatch(self, action: AgentAction) -> str:
        tools = self._tools
        if isinstance(action, SearchNotesAction):
            return tools.search_notes(action.query, action.limit)
        if isinstance(action, ReadNoteAction):
            return tools.read_note(NoteId(action.note_id))
        if isinstance(action, ProposeEditAction):
            return tools.propose_edit(
                NoteId(action.note_id),
                action.front,
                action.back,
                action.tags,
                action.rationale,
            )
        if isinstance(action, ProposeCreateAction):
            return tools.propose_create(
                action.front,
                action.back,
                action.tags,
                action.notetype,
                action.rationale,
            )
        if isinstance(action, ProposeDeleteAction):
            return tools.propose_delete(
                NoteId(action.note_id), action.rationale
            )
        if isinstance(action, ProposeSplitAction):
            return tools.propose_split(
                NoteId(action.note_id),
                action.kept_front,
                action.kept_back,
                action.kept_tags,
                [n.model_dump(exclude_none=True) for n in action.new_notes],
                action.rationale,
            )
        raise ValueError(f"unexpected action: {action}")


@lru_cache(maxsize=1)
def _get_system_prompt() -> str:
    path = Path(__file__).parent / "prompt_curator.md"
    try:
        return path.read_text()
    except FileNotFoundError:
        raise RuntimeError(f"Curator prompt not found: {path}")
