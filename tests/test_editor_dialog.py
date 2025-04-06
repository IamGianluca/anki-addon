import sys
import pytest
from addon.standalone_editor import EditorDialog
from tests.conftest import FakeCollection, FakeMainWindow, FakeNote


def test_init_editor_dialog_with_cards_marked_for_review(mw, collection):
    """EditorDialog is correctly initialized with three notes, two of them
    marked for review.
    """
    # When
    editor_dialog = EditorDialog(collection)

    # Then
    assert len(editor_dialog.review_notes) == 2
    assert editor_dialog.review_notes[0].id == 1
    assert editor_dialog.review_notes[1].id == 3
    assert editor_dialog.current_index == 0


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


# def test_current_note(collection):
#     """Test current_note retrieves correct note and stores original fields"""
#     collection, is_marked_for_review = collection
#     editor_dialog = EditorDialog(collection)
#
#     note = editor_dialog.current_note()
#
#     assert note.id == 1
#     assert note["Front"] == "Question 1"
#     assert note["Back"] == "Answer 1"
#     assert editor_dialog.original_fields == {
#         "Front": "Question 1",
#         "Back": "Answer 1",
#     }
#
#
# def test_restore_note_to_original(collection):
#     """Test restoring note fields to original values"""
#     collection, is_marked_for_review = collection
#     editor_dialog = EditorDialog(collection)
#
#     # First get the current note to store original values
#     note = editor_dialog.current_note()
#
#     # Modify the note
#     note["Front"] = "Modified Question"
#     note["Back"] = "Modified Answer"
#
#     # Restore to original
#     restored_note = editor_dialog.restore_note_to_original()
#
#     assert restored_note.id == 1
#     assert restored_note["Front"] == "Question 1"
#     assert restored_note["Back"] == "Answer 1"
#
#
# def test_has_next_note(collection):
#     """Test has_next_note returns correct value"""
#     collection, is_marked_for_review = collection
#     editor_dialog = EditorDialog(collection)
#
#     assert editor_dialog.has_next_note() is True
#
#     # Move to the last note
#     editor_dialog.current_index = 1
#
#     assert editor_dialog.has_next_note() is False
#
#
# def test_next_note(collection):
#     """Test next_note advances to the next note correctly"""
#     collection, is_marked_for_review = collection
#     editor_dialog = EditorDialog(collection)
#
#     next_note = editor_dialog.next_note()
#
#     assert editor_dialog.current_index == 1
#     assert next_note.id == 3
#     assert next_note["Front"] == "Question 3"
#
#     # No more notes after this
#     assert editor_dialog.next_note() is None
#     assert editor_dialog.current_index == 1  # Index doesn't change when no more notes
#
#
# def test_flush_on_restore(collection):
#     """Test that flush is called when restoring a note"""
#     collection, is_marked_for_review = collection
#     editor_dialog = EditorDialog(collection)
#
#     # First get the current note to store original values
#     note = editor_dialog.current_note()
#
#     # Modify the note
#     note["Front"] = "Modified Question"
#
#     # Restore to original and flush
#     restored_note = editor_dialog.restore_note_to_original()
#     restored_note.flush()
#
#     assert restored_note.flushed is True
