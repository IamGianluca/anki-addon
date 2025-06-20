import sys

import pytest

from .fakes.aqt_fakes import FakeCard, FakeCollection, FakeMainWindow, FakeNote

# ---------
# Anki
# ---------


@pytest.fixture
def note1():
    return FakeNote(1, {"Front": "Question 1", "Back": "Answer 1"})


@pytest.fixture
def note2():
    return FakeNote(2, {"Front": "Question 2", "Back": "Answer 2"})


@pytest.fixture
def note3():
    return FakeNote(3, {"Front": "Question 3", "Back": "Answer 3"})


@pytest.fixture
def cloze1():
    return FakeNote(
        4,
        {"type": 1, "Text": "This is a {{c1::fake note}}", "Back Extra": ""},
    )


@pytest.fixture
def collection(note1, note2, note3, cloze1):
    collection = FakeCollection()
    collection.notes = {1: note1, 2: note2, 3: note3, 4: cloze1}

    # Create cards for each note
    card_id = 100
    for note_id, note in collection.notes.items():
        # Create 2 cards per note (e.g., for front/back cards)
        for i in range(2):
            card = FakeCard(card_id, note_id)
            collection.cards[card_id] = card
            card_id += 1

    # Set orange flag (id=2) to cards of notes 1 and 3
    # In Anki, flags are set on cards, not notes
    for card in collection.cards.values():
        if card.note_id in [1, 3, 4]:  # Notes marked for review
            card.flags = 2  # Orange flag

    return collection


@pytest.fixture()
def mw(monkeypatch, collection):
    fake_mw = FakeMainWindow(collection)
    monkeypatch.setattr("aqt.mw", fake_mw)

    # If modules have already imported mw, patch in those modules too
    for name, module in list(sys.modules.items()):
        if hasattr(module, "mw"):
            monkeypatch.setattr(f"{name}.mw", fake_mw)

    return fake_mw


# ---------
# Qdrant
# ---------


@pytest.fixture
def first_response():
    return {"id": "doc_1", "score": 0.95, "payload": {"text": "Result 1"}}


@pytest.fixture
def second_response():
    return {"id": "doc_2", "score": 0.87, "payload": {"text": "Result 2"}}


@pytest.fixture
def third_response():
    return {"id": "doc_3", "score": 0.75, "payload": {"text": "Result 3"}}
