from __future__ import annotations

from typing import TYPE_CHECKING

from aqt import mw
from aqt.utils import showInfo

from ...utils import ensure_collection

if TYPE_CHECKING:
    from anki.collection import Collection


def display_notes_marked_for_review_count() -> None:
    col = ensure_collection(mw.col)
    deck_id = col.decks.current()["id"]
    query = f"did:{deck_id}"
    note_ids = col.find_notes(query)

    flagged_notes = 0
    for note_id in note_ids:
        if is_note_marked_for_review(col, note_id):
            flagged_notes += 1

    notes_count = len(col.find_notes(f"did:{deck_id}"))
    showInfo(f"Notes marked for review: {flagged_notes}/{notes_count}")


def is_note_marked_for_review(col: Collection, note_id: int) -> bool:
    # NOTE: Flags are assigned to cards, not notes. For this reason, we are
    # iterating through the cards associated to a note to find if any of them
    # has an orange (id=2) flag
    card_ids = col.find_cards(f"nid:{note_id}")
    for card_id in card_ids:
        card = col.get_card(card_id)
        if (
            card.flags == 2
        ):  # orange flag, our convention to mark a note for review
            return True
    return False
