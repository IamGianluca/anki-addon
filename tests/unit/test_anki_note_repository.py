import pytest
from tests.fakes.aqt_fakes import FakeCollection

from addon.domain.entities.note import AddonNote, AddonNoteType, NoteId
from addon.domain.repositories.note_repository import NoteNotFoundError
from addon.infrastructure.persistence.anki_note_repository import (
    AnkiNoteRepository,
)


@pytest.fixture
def repository(collection: FakeCollection) -> AnkiNoteRepository:
    return AnkiNoteRepository(collection)


def test_search_finds_notes_by_text_terms(
    repository: AnkiNoteRepository,
) -> None:
    # When
    results = repository.search("question 2")

    # Then
    assert results == [2]


def test_search_respects_limit(repository: AnkiNoteRepository) -> None:
    # When
    results = repository.search("question", limit=2)

    # Then
    assert len(results) == 2


def test_get_returns_mapped_note(repository: AnkiNoteRepository) -> None:
    # When
    note = repository.get(NoteId(1))

    # Then
    assert note.front == "Question 1"
    assert note.back == "Answer 1"
    assert note.notetype == AddonNoteType.BASIC


def test_get_returns_mapped_cloze_note(
    repository: AnkiNoteRepository,
) -> None:
    # When
    note = repository.get(NoteId(4))

    # Then
    assert note.front == "This is a {{c1::fake note}}"
    assert note.notetype == AddonNoteType.CLOZE


def test_get_unknown_note_raises(repository: AnkiNoteRepository) -> None:
    # When / Then
    with pytest.raises(NoteNotFoundError):
        repository.get(NoteId(999))


def test_update_changes_fields_and_tags(
    repository: AnkiNoteRepository, collection: FakeCollection
) -> None:
    # When
    repository.update(
        NoteId(1),
        AddonNote(front="New question", back="New answer", tags=["ml"]),
    )

    # Then
    note = collection.get_note(1)
    assert note["Front"] == "New question"
    assert note["Back"] == "New answer"
    assert note.tags == ["ml"]
    assert note.was_flushed()


def test_update_unknown_note_raises(
    repository: AnkiNoteRepository,
) -> None:
    # When / Then
    with pytest.raises(NoteNotFoundError):
        repository.update(NoteId(999), AddonNote(front="f", back="b"))


def test_add_creates_basic_note_in_deck(
    repository: AnkiNoteRepository, collection: FakeCollection
) -> None:
    # When
    note_id = repository.add(
        AddonNote(
            front="What does beta_2 control in Adam?",
            back="Decay rate of the second moment estimate.",
            tags=["ml"],
        ),
        deck_name="Default",
    )

    # Then
    note = collection.get_note(note_id)
    assert note is not None
    assert note["Front"] == "What does beta_2 control in Adam?"
    assert note.tags == ["ml"]
    assert collection.find_notes("beta_2") == [note_id]


def test_add_creates_cloze_note(
    repository: AnkiNoteRepository, collection: FakeCollection
) -> None:
    # When
    note_id = repository.add(
        AddonNote(
            front="The capital of France is {{c1::Paris}}",
            back="",
            notetype=AddonNoteType.CLOZE,
        ),
        deck_name="Default",
    )

    # Then
    note = collection.get_note(note_id)
    assert note["Text"] == "The capital of France is {{c1::Paris}}"
    assert note.note_type()["type"] == 1


def test_add_unknown_deck_raises(repository: AnkiNoteRepository) -> None:
    # When / Then
    with pytest.raises(RuntimeError, match="Deck 'Nope' not found"):
        repository.add(AddonNote(front="f", back="b"), deck_name="Nope")


def test_add_unknown_notetype_raises(
    collection: FakeCollection,
) -> None:
    # Given
    repository = AnkiNoteRepository(collection, basic_notetype="NoSuchType")

    # When / Then
    with pytest.raises(RuntimeError, match="Notetype 'NoSuchType'"):
        repository.add(AddonNote(front="f", back="b"), deck_name="Default")


def test_remove_deletes_notes_and_their_cards(
    repository: AnkiNoteRepository, collection: FakeCollection
) -> None:
    # When
    repository.remove([NoteId(1)])

    # Then
    assert collection.get_note(1) is None
    assert collection.find_notes("nid:1") == []
    remaining_note_ids = {card.note_id for card in collection.cards.values()}
    assert 1 not in remaining_note_ids


def test_remove_unknown_note_raises(
    repository: AnkiNoteRepository,
) -> None:
    # When / Then
    with pytest.raises(NoteNotFoundError):
        repository.remove([NoteId(999)])
