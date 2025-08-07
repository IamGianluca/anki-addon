from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.decks import DeckDict
    from anki.notes import Note


def ensure_config(config: Optional[dict]) -> dict:
    if config is None:
        raise RuntimeError("Config not initialized")
    return config


def ensure_collection(col: Optional[Collection]) -> Collection:
    if col is None:
        raise RuntimeError("Collection not initialized")
    return col


def ensure_deck(deck: Optional[DeckDict]) -> DeckDict:
    if deck is None:
        raise RuntimeError("Deck not initialized")
    return deck


def ensure_note(note: Optional[Note]) -> Note:
    if note is None:
        raise RuntimeError("Note not initialized")
    return note


def is_cloze_note(note) -> bool:
    from anki.consts import MODEL_CLOZE

    return note.note_type()["type"] == MODEL_CLOZE
