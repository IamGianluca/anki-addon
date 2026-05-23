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


def is_cloze_note(note: Note) -> bool:
    from anki.consts import MODEL_CLOZE

    note_type = note.note_type()
    if note_type is None:
        return False
    return note_type["type"] == MODEL_CLOZE
