from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.notes import Note


def ensure_collection(col: Optional[Collection]) -> Collection:
    if col is None:
        raise RuntimeError("Collection not initialized")
    return col


def ensure_note(note: Optional[Note]) -> Note:
    if note is None:
        raise RuntimeError("Note not initialized")
    return note


# Value of anki.consts.MODEL_CLOZE, inlined so that checking note types
# never imports anki at runtime (~1s, which unit tests would pay).
_MODEL_CLOZE = 1


def is_cloze_note(note: Note) -> bool:
    note_type = note.note_type()
    if note_type is None:
        return False
    return note_type["type"] == _MODEL_CLOZE
