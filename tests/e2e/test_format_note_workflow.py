import json

import pytest

from addon.application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from addon.infrastructure.external_services.openai import OpenAIClient
from addon.infrastructure.ui.editor import EditorDialog


@pytest.mark.slow
def test_complete_format_workflow_for_basic_note(addon_config, mw, collection):
    """E2E test: complete workflow from EditorDialog through formatting to persistence.

    Tests the full user journey:
    1. EditorDialog discovers notes marked with orange flag
    2. User formats note via NoteFormatter
    3. Note is saved and flag is removed
    4. Changes persist to collection
    """
    # Given: Setup formatter with canned LLM response
    response = json.dumps(
        {
            "front": "Most winning NHL team",
            "back": "Montreal Canadiens - 24 Stanley Cup championships",
            "tags": ["hockey"],
        }
    )
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When: Run complete workflow as user would
    editor_dialog = EditorDialog(collection)

    # Verify we have notes marked for review
    assert len(editor_dialog) == 3

    # Get current note and format it
    current_note = editor_dialog.current_note()
    original_front = current_note["Front"]
    formatted_note = format_note_workflow(current_note, formatter)

    # Save and remove flag
    editor_dialog.strip_orange_flag(formatted_note)
    formatted_note.flush()

    # Then: Verify end-to-end behavior
    # Note content was updated
    assert formatted_note["Front"] == "Most winning NHL team"
    assert (
        formatted_note["Back"]
        == "Montreal Canadiens - 24 Stanley Cup championships"
    )
    assert formatted_note["Front"] != original_front

    # Note was persisted
    assert formatted_note.was_flushed()

    # Orange flag was removed from all cards of this note
    card_ids = mw.col.find_cards(f"nid:{formatted_note.id}")
    assert len(card_ids) > 0
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 0  # Flag removed
        assert card.was_flushed()


@pytest.mark.slow
def test_complete_format_workflow_for_cloze_note(addon_config, mw, collection):
    """E2E test: complete workflow for cloze note type."""
    # Given: Setup formatter with canned LLM response for cloze
    response = json.dumps(
        {
            "front": "NHL history: {{c1::Montreal Canadiens}} most successful team",
            "back": "",
            "tags": ["hockey"],
        }
    )
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    # When: Run complete workflow
    editor_dialog = EditorDialog(collection)

    # Navigate to the cloze note (note with id=4)
    current_note = editor_dialog.current_note()
    while current_note.id != 4 and editor_dialog.has_next_note():
        current_note = editor_dialog.move_to_next_note()

    assert current_note.id == 4  # Verify we found the cloze note

    formatted_note = format_note_workflow(current_note, formatter)
    editor_dialog.strip_orange_flag(formatted_note)
    formatted_note.flush()

    # Then: Verify cloze-specific behavior
    assert "Montreal Canadiens" in formatted_note["Text"]
    assert formatted_note["Back Extra"] == ""
    assert formatted_note.was_flushed()

    # Orange flag removed
    card_ids = mw.col.find_cards(f"nid:{formatted_note.id}")
    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        assert card.flags == 0


@pytest.mark.slow
def test_format_workflow_preserves_note_on_skip(addon_config, mw, collection):
    """E2E test: skipping a note and restoring preserves original content."""
    # Given
    response = json.dumps(
        {"front": "Changed", "back": "Changed", "tags": ["test"]}
    )
    openai = OpenAIClient.create_null(addon_config, responses=[response])
    formatter = NoteFormatter(openai)

    editor_dialog = EditorDialog(collection)
    current_note = editor_dialog.current_note()

    # Store original content
    original_front = current_note["Front"]
    original_back = current_note["Back"]

    # When: Format note but then restore (user changed their mind)
    formatted_note = format_note_workflow(current_note, formatter)
    assert formatted_note["Front"] == "Changed"  # Verify it was changed

    # Restore to original
    editor_dialog.restore_current_note()
    current_note = editor_dialog.current_note()

    # Then: Original content is preserved
    assert current_note["Front"] == original_front
    assert current_note["Back"] == original_back
