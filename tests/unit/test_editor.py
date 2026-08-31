import dataclasses

import pytest
from tests.conftest import FakeCollection, FakeMainWindow, FakeNote

from addon.application.use_cases.apply_curation import apply_proposals
from addon.domain.entities.note import NoteId
from addon.domain.entities.proposals import EditProposal
from addon.infrastructure.persistence.anki_note_repository import (
    AnkiNoteMapper,
    AnkiNoteRepository,
)
from addon.infrastructure.ui.editor import EditorDialog


def test_init_editor_dialog_with_cards_marked_for_review(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """EditorDialog is correctly initialized with three notes, two of them
    marked for review.
    """
    # When
    editor_dialog = EditorDialog(collection)

    # Then
    assert len(editor_dialog) == 3
    assert editor_dialog.review_notes[0].id == 1
    assert editor_dialog.review_notes[1].id == 3


def test_init_editor_dialog_without_cards_marked_for_review() -> None:
    """EditorDialog raises an error if initialized without any card marked
    for review.
    """
    # Given
    collection = FakeCollection()
    note = FakeNote(
        1,
        {
            "Front": "Question 1",
            "Back": "Answer 1",
        },
    )
    collection.notes = {1: note}

    # When and Then
    with pytest.raises(ValueError) as exc_info:
        EditorDialog(collection)  # type: ignore

    assert "No notes marked for review" in str(exc_info.value)


def test_current_note(mw: FakeMainWindow, collection: FakeCollection) -> None:
    """Test current_note() retrieves correct note and creates backup of
    original fields.
    """
    # Given
    editor_dialog = EditorDialog(collection)

    # When
    note = editor_dialog.current_note()

    # Then
    assert note.id == 1
    assert note["Front"] == "Question 1"
    assert note["Back"] == "Answer 1"


def test_restore_note_to_original(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Test restoring note fields to original values"""
    # Given
    editor_dialog = EditorDialog(collection)
    note = editor_dialog.current_note()

    # Modify the note
    note["Front"] = "Modified Question"
    note["Back"] = "Modified Answer"

    # When
    editor_dialog.restore_current_note()
    restored_note = editor_dialog.current_note()

    # Then
    assert restored_note.id == 1
    assert restored_note["Front"] == "Question 1"
    assert restored_note["Back"] == "Answer 1"


def test_has_next_note(mw: FakeMainWindow, collection: FakeCollection) -> None:
    """Test has_next_note() returns correct value"""
    # Given
    editor_dialog = EditorDialog(collection)

    # Then
    assert editor_dialog.has_next_note()

    # When
    editor_dialog.move_to_next_note()

    # Then
    assert editor_dialog.has_next_note()

    # When
    editor_dialog.move_to_next_note()

    # Then
    assert not editor_dialog.has_next_note()


def test_next_note(mw: FakeMainWindow, collection: FakeCollection) -> None:
    """Test next_note() advances to the next note correctly"""
    # Given
    editor_dialog = EditorDialog(collection)

    # Then
    next_note = editor_dialog.current_note()
    assert next_note.id == 1

    # When
    next_note = editor_dialog.move_to_next_note()

    # Then
    assert next_note.id == 3

    # When
    next_note = editor_dialog.move_to_next_note()

    # Then
    assert next_note.id == 4


def test_orange_flag_is_removed_after_saving_changes(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """After making changes to a note and pressing `Save` in the editor, the
    orange flag should be remove in each card of that note.
    """
    # Given
    editor_dialog = EditorDialog(collection)
    current_note = editor_dialog.current_note()

    # Then
    card_ids = mw.col.find_cards(f"nid:{current_note.id}")
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 2 and not card.was_flushed()

    # When
    editor_dialog.strip_orange_flag(current_note)

    # Then
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags != 2 and card.was_flushed()


def test_editor_review_counts(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    # Given
    editor_dialog = EditorDialog(collection)
    assert len(editor_dialog) == 3


def test_save_note_keep_flag_preserves_orange_flag(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Test that save_note_keep_flag preserves the orange flag on cards."""
    # Given
    editor_dialog = EditorDialog(collection)
    current_note = editor_dialog.current_note()

    # Verify note has orange flag initially
    card_ids = mw.col.find_cards(f"nid:{current_note.id}")
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 2  # Orange flag

    # Modify note content
    current_note["Front"] = "Modified content"

    # When: Save note keeping flag
    editor_dialog.save_note_keep_flag(current_note)

    # Then: Flag should still be orange (2)
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 2  # Still orange

    # And note should be saved
    assert current_note.was_flushed()


def test_save_note_keep_flag_vs_strip_orange_flag_behavior(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Test that save_note_keep_flag behaves differently
    from strip_orange_flag.
    """
    # Given
    editor_dialog = EditorDialog(collection)
    current_note = editor_dialog.current_note()

    # Get card IDs for verification
    card_ids = mw.col.find_cards(f"nid:{current_note.id}")

    # Test strip_orange_flag behavior
    editor_dialog.strip_orange_flag(current_note)
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 0  # Flag removed

    # Reset flag to orange for second test
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        card.flags = 2  # Reset to orange
        mw.col.update_card(card)

    # Test save_note_keep_flag behavior
    editor_dialog.save_note_keep_flag(current_note)
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 2  # Flag preserved


def test_restore_note_preserves_tags(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Test that restoring a note also restores its original tags"""
    # Given
    editor_dialog = EditorDialog(collection)
    current_note = editor_dialog.current_note()

    # Store original tags
    original_tags = current_note.tags.copy()
    assert original_tags == []  # Initial state

    # When: Modify tags
    current_note.tags = ["new_tag", "another_tag"]

    # Then restore
    editor_dialog.restore_current_note()

    # Then: Tags should be restored to original
    assert current_note.tags == original_tags


def test_fake_collection_find_notes_filters_by_deck_id() -> None:
    """FakeCollection.find_notes respects the deck ID in the query."""
    # Given
    collection = FakeCollection()
    collection.notes = {
        1: FakeNote(1, {"Front": "Q1", "Back": "A1"}),
        2: FakeNote(2, {"Front": "Q2", "Back": "A2"}),
    }
    current_deck_id = collection.decks.current()["id"]

    # When / Then — matching deck ID returns notes
    assert collection.find_notes(f"did:{current_deck_id}") == [1, 2]

    # When / Then — non-matching deck ID returns empty
    assert collection.find_notes("did:999") == []

    # When / Then — query without did: returns empty
    assert collection.find_notes("tag:foo") == []


def test_navigating_to_note_shows_changes_applied_while_dialog_open(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Changes the curator applies to a later review note while the
    dialog is open are visible when navigating to it.
    """
    # Given
    editor_dialog = EditorDialog(collection)
    assert editor_dialog.current_note().id == 1

    # When — the curator applies an edit to note 3 (the next review
    # note) while the dialog is still showing note 1
    curated = FakeNote(3, {"Front": "Curated Front", "Back": "Curated Back"})
    collection.update_note(curated)

    # When — the user saves and navigates to the next note
    next_note = editor_dialog.move_to_next_note()

    # Then — the curated content is shown, not the stale pre-curation copy
    assert next_note is not None
    assert next_note["Front"] == "Curated Front"
    assert next_note["Back"] == "Curated Back"


def test_curated_changes_survive_full_review_flow(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Full 'Improve note with AI' flow: the curator applies an approved
    edit to the next review note (B) while the dialog is on note A. The
    user saves A, navigates to B, saves B and exits, then reopens the
    editor — B must still have the curated content in the collection.
    """
    # Given — the review editor is open on note 1 (A), with note 3 (B)
    # flagged as the next note to review
    editor_dialog = EditorDialog(collection)
    assert editor_dialog.current_note().id == 1

    # When — the curator applies an approved edit to B through the real
    # apply path (AnkiNoteRepository + apply_proposals)
    repository = AnkiNoteRepository(collection)
    before = AnkiNoteMapper.to_addon_note(collection.get_note(3))
    after = dataclasses.replace(
        before, front="Curated Front", back="Curated Back"
    )
    apply_proposals(
        repository,
        [EditProposal(NoteId(3), before, after, "curate the note")],
        deck_name="Default",
    )

    # When — the user saves A and navigates to B
    note_a = editor_dialog.current_note()
    editor_dialog.strip_orange_flag(note_a)
    collection.update_note(note_a)
    note_b = editor_dialog.move_to_next_note()
    assert note_b is not None

    # Then — B shows the curated content
    assert note_b["Front"] == "Curated Front"
    assert note_b["Back"] == "Curated Back"

    # When — the user saves B, exits the editor (cancel restores the
    # current note from backup) and reopens it
    collection.update_note(note_b)
    editor_dialog.restore_current_note()
    reopened = EditorDialog(collection)
    reopened_b = reopened.current_note()

    # Then — the curated changes are still in the collection
    assert reopened_b.id == 3
    assert reopened_b["Front"] == "Curated Front"
    assert reopened_b["Back"] == "Curated Back"


def test_skip_multiple_notes_preserves_original_content(
    mw: FakeMainWindow, collection: FakeCollection
) -> None:
    """Test that skipping multiple notes and then making changes doesn't
    overwrite previous notes with wrong content.
    """
    """
    To reproduce the issue:
    1. Skip one or more cards
    2. Make some changes to the note and press Save.

    The skipped cards will change content and become duplicated of the
    first card skipped. The last card is correct.
    """
    # Given
    editor_dialog = EditorDialog(collection)
    assert len(editor_dialog) == 3

    # Store original content for verification
    original_note1_front = editor_dialog.review_notes[0]["Front"]
    original_note1_back = editor_dialog.review_notes[0]["Back"]
    original_note2_front = editor_dialog.review_notes[1]["Front"]
    original_note2_back = editor_dialog.review_notes[1]["Back"]
    original_note3_front = editor_dialog.review_notes[2]["Text"]
    original_note3_back = editor_dialog.review_notes[2]["Back Extra"]

    # When: Skip to note 3
    _ = editor_dialog.move_to_next_note()  # Note 2
    note3 = editor_dialog.move_to_next_note()  # Note 3
    assert note3

    # Now restore current note to original
    note3["Text"] = "changes"
    editor_dialog.restore_current_note()

    # Then: Each note should have its own original content restored
    restored_note1 = editor_dialog.review_notes[0]
    restored_note2 = editor_dialog.review_notes[1]

    assert restored_note1["Front"] == original_note1_front
    assert restored_note1["Back"] == original_note1_back
    assert restored_note2["Front"] == original_note2_front
    assert restored_note2["Back"] == original_note2_back
    assert note3["Text"] == original_note3_front
    assert note3["Back Extra"] == original_note3_back
