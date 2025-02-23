from aqt import mw
from aqt.qt import qconnect, QAction
from aqt.utils import showInfo


def testFunction() -> None:
    deck_id = mw.col.decks.current()["id"]
    query = f"did:{deck_id}"
    note_ids = mw.col.find_notes(query)

    flagged_cards = 0
    for note_id in note_ids:
        if is_marked_for_review(note_id):
            flagged_cards += 1

    card_count = mw.col.card_count()
    showInfo(f"Card marked for review: {flagged_cards}/{card_count}")


def is_marked_for_review(note_id: int) -> bool:
    # NOTE: flags are assigned to cards, not notes
    card_ids = mw.col.find_cards(f"nid:{note_id}")
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        if card.flags == 2:  # orange flag, our convention to mark a note for review
            return True
    return False


action = QAction("Count cards marked for review", mw)
qconnect(action.triggered, testFunction)
mw.form.menuTools.addAction(action)
