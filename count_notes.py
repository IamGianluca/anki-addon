from typing import Optional
from anki.collection import Collection
from aqt import mw
from aqt.qt import qconnect, QAction
from aqt.utils import showInfo


def display_notes_marked_for_review_count() -> None:
    col = ensure_collection(mw.col)
    deck_id = col.decks.current()["id"]
    query = f"did:{deck_id}"
    note_ids = col.find_notes(query)

    flagged_notes = 0
    for note_id in note_ids:
        if is_note_marked_for_review(note_id):
            flagged_notes += 1

    notes_count = len(col.find_notes(f"did:{deck_id}"))
    showInfo(f"Notes marked for review: {flagged_notes}/{notes_count}")


def is_note_marked_for_review(note_id: int) -> bool:
    # NOTE: Flags are assigned to cards, not notes. For this reason, we are iterating
    # through the cards associated to a note to find if any of them has an orange (id=2)
    # flag
    col = ensure_collection(mw.col)
    card_ids = col.find_cards(f"nid:{note_id}")
    for card_id in card_ids:
        card = col.get_card(card_id)
        if card.flags == 2:  # orange flag, our convention to mark a note for review
            return True
    return False


def ensure_collection(col: Optional[Collection]) -> Collection:
    if col is None:
        raise RuntimeError("Collection not initialized")
    return col


action = QAction("Count notes marked for review", mw)
qconnect(action.triggered, display_notes_marked_for_review_count)
mw.form.menuTools.addAction(action)
