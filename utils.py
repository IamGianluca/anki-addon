from typing import Optional

from anki.collection import Collection
from anki.decks import DeckId


def ensure_collection(col: Optional[Collection]) -> Collection:
    if col is None:
        raise RuntimeError("Collection not initialized")
    return col


def ensure_deck(deck: Optional[DeckId]) -> DeckId:
    if deck is None:
        raise RuntimeError("Deck not initialized")
    return deck
