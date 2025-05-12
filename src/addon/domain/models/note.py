from typing import List, Optional

from pydantic import BaseModel


class AddonNote(BaseModel):
    guid: str
    front: str
    back: str
    tags: Optional[List[str]] = None
    notetype: Optional[str] = None
    deck_name: Optional[str] = None


class AddonNoteChanges(BaseModel):
    front: str
    back: str
    tags: Optional[List[str]] = None
