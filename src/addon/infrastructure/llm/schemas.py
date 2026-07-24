from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class AddonNoteChanges(BaseModel):
    """Pydantic schema for LLM structured output when formatting notes.

    This schema defines the expected JSON structure that the LLM should return
    when formatting or editing notes. It's used for generating JSON schemas
    and validating LLM responses.

    Attributes:
        front: Updated front side content.
        back: Updated back side content.
    """

    front: str
    back: str


class SearchNotesAction(BaseModel):
    action: Literal["search_notes"]
    query: str
    limit: int = 10


class ReadNoteAction(BaseModel):
    action: Literal["read_note"]
    note_id: int


class ProposeEditAction(BaseModel):
    action: Literal["propose_edit"]
    note_id: int
    front: str
    back: str
    tags: list[str]
    rationale: str


class ProposeCreateAction(BaseModel):
    action: Literal["propose_create"]
    front: str
    back: str
    tags: list[str]
    notetype: str
    rationale: str


class ProposeDeleteAction(BaseModel):
    action: Literal["propose_delete"]
    note_id: int
    rationale: str


class NewNoteFields(BaseModel):
    """Fields of one new note within a split proposal. `notetype`
    omitted means: inherit the split note's type."""

    front: str
    back: str
    tags: list[str] = []
    notetype: Optional[str] = None


class ProposeSplitAction(BaseModel):
    action: Literal["propose_split"]
    note_id: int
    kept_front: str
    kept_back: str
    kept_tags: list[str]
    new_notes: list[NewNoteFields]
    rationale: str


class FinishAction(BaseModel):
    action: Literal["finish"]
    summary: str


AgentAction = Union[
    SearchNotesAction,
    ReadNoteAction,
    ProposeEditAction,
    ProposeCreateAction,
    ProposeDeleteAction,
    ProposeSplitAction,
    FinishAction,
]


class AgentStep(BaseModel):
    """One turn of the curation agent: the model's reasoning followed
    by exactly one action to execute."""

    thought: str
    action: AgentAction = Field(discriminator="action")
