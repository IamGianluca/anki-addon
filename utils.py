from typing import Optional

from anki.collection import Collection
from anki.decks import DeckDict
from anki.notes import Note


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
