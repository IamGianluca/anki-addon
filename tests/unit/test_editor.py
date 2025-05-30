import sys

import pytest
from tests.conftest import FakeCollection, FakeMainWindow, FakeNote

from addon.domain.models.editor import EditorDialog


def test_init_editor_dialog_with_cards_marked_for_review(mw, collection):
    """EditorDialog is correctly initialized with three notes, two of them
    marked for review.
    """
    # When
    editor_dialog = EditorDialog(collection)

    # Then
    assert len(editor_dialog) == 3
    assert editor_dialog.review_notes[0].id == 1
    assert editor_dialog.review_notes[1].id == 3


def test_init_editor_dialog_without_cards_marked_for_review(monkeypatch):
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

    fake_mw = FakeMainWindow(collection)
    monkeypatch.setattr("aqt.mw", fake_mw)
    for name, module in list(sys.modules.items()):
        if hasattr(module, "mw"):
            monkeypatch.setattr(f"{name}.mw", fake_mw)

    # When and Then
    with pytest.raises(ValueError) as exc_info:
        EditorDialog(collection)  # type: ignore

    assert "No notes marked for review" in str(exc_info.value)


def test_current_note(mw, collection):
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


def test_restore_note_to_original(mw, collection):
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


def test_has_next_note(mw, collection):
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


def test_next_note(mw, collection):
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


def test_orange_flag_is_removed_after_saving_changes(mw, collection):
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


def test_editor_review_counts(mw, collection):
    # Given
    editor_dialog = EditorDialog(collection)
    assert len(editor_dialog) == 3


def test_skip_multiple_notes_preserves_original_content(mw, collection):
    """Test that skipping multiple notes and then making changes doesn't
    overwrite previous notes with wrong content.
    """
    """
    To reproduce the issue:
    1. Skip one or more cards
    2. Make some changes to the note and press Save.

    The skipped cards will change content and become duplicated of the first card skipped. The last card is correct.
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
