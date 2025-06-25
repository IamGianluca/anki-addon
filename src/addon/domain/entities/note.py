from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AddonNoteType(str, Enum):
    BASIC = "basic"
    CLOZE = "cloze"


class AddonNote(BaseModel):
    guid: str
    front: str
    back: str
    tags: Optional[List[str]] = None
    notetype: AddonNoteType = Field(default=AddonNoteType.BASIC)
    deck_name: Optional[str] = None


class AddonNoteChanges(BaseModel):
    front: str
    back: str
    tags: Optional[List[str]] = None
