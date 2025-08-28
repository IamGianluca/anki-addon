from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AddonNoteType(str, Enum):
    BASIC = "basic"
    CLOZE = "cloze"


class AddonNote(BaseModel):
    guid: str = Field(default_factory=lambda: str(uuid4()))
    front: str
    back: str
    tags: Optional[List[str]] = None
    notetype: AddonNoteType = Field(default=AddonNoteType.BASIC)
    deck_name: Optional[str] = None


class AddonNoteChanges(BaseModel):
    front: str
    back: str
    tags: Optional[List[str]] = None


class AddonCollection:
    def __init__(self, name: str) -> None:
        self.name = name
        self.notes = []

    def add(self, note: AddonNote) -> None:
        self.notes.append(note)

    def add_batch(self, notes: List[AddonNote]) -> None:
        for note in notes:
            self.add(note)

    def get(self, note_guid: str) -> Optional[AddonNote]:
        for note in self.notes:
            if note.guid == note_guid:
                return note

    def __iter__(self):
        return iter(self.notes)
