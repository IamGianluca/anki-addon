import sys

import pytest

from addon.domain.entities.note import AddonCollection, AddonNote
from addon.infrastructure.configuration.settings import AddonConfig

from .fakes.aqt_fakes import FakeCard, FakeCollection, FakeMainWindow, FakeNote

###########
# Domain fixtures
###########


@pytest.fixture
def addon_note1() -> AddonNote:
    return AddonNote(front="front_one", back="back_one")


@pytest.fixture
def addon_note2() -> AddonNote:
    return AddonNote(front="front_two", back="back_two")


@pytest.fixture
def addon_note3() -> AddonNote:
    return AddonNote(front="front_three", back="back_three")


@pytest.fixture
def addon_collection(addon_note1, addon_note2, addon_note3) -> AddonCollection:
    collection = AddonCollection(name="default")
    collection.add(notes=[addon_note1, addon_note2, addon_note3])
    return collection


###########
# Anki fixtures
###########


@pytest.fixture
def addon_config() -> AddonConfig:
    return AddonConfig.create_nullable()


@pytest.fixture
def note1() -> FakeNote:
    return FakeNote(1, {"Front": "Question 1", "Back": "Answer 1"})


@pytest.fixture
def note2() -> FakeNote:
    return FakeNote(2, {"Front": "Question 2", "Back": "Answer 2"})


@pytest.fixture
def note3() -> FakeNote:
    return FakeNote(3, {"Front": "Question 3", "Back": "Answer 3"})


@pytest.fixture
def cloze1() -> FakeNote:
    return FakeNote(
        4,
        {"type": 1, "Text": "This is a {{c1::fake note}}", "Back Extra": ""},
    )


@pytest.fixture
def collection(note1, note2, note3, cloze1) -> FakeCollection:
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
def mw(monkeypatch, collection) -> FakeMainWindow:
    fake_mw = FakeMainWindow(collection)
    monkeypatch.setattr("aqt.mw", fake_mw)

    # If modules have already imported mw, patch in those modules too
    for name, module in list(sys.modules.items()):
        if hasattr(module, "mw"):
            monkeypatch.setattr(f"{name}.mw", fake_mw)

    return fake_mw


###########
# Qdrant fixtures
###########


@pytest.fixture
def first_response() -> dict[str, object]:
    return {"id": "doc_1", "score": 0.95, "payload": {"text": "Result 1"}}


@pytest.fixture
def second_response() -> dict[str, object]:
    return {"id": "doc_2", "score": 0.87, "payload": {"text": "Result 2"}}


@pytest.fixture
def third_response() -> dict[str, object]:
    return {"id": "doc_3", "score": 0.75, "payload": {"text": "Result 3"}}
