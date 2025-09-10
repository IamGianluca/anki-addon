from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ...application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from ...infrastructure.configuration.settings import AddonConfig
from ...infrastructure.external_services.openai import OpenAIClient
from ...infrastructure.ui.editor import EditorDialog
from ...utils import ensure_collection, ensure_note

if TYPE_CHECKING:
    from aqt.editor import Editor


def open_standalone_editor() -> None:
    """The open_standalone_editor() function creates the actual user interface:

    - It creates a dialog window with an Anki editor widget
    - It adds buttons for saving changes, skipping to the next note, or
      canceling the editing session
    - It implements handlers for each button's functionality
    """
    from aqt import mw
    from aqt.editor import Editor
    from aqt.utils import showInfo
    from PyQt6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

    # Create a new window
    dialog = QDialog(mw)
    dialog.setWindowTitle("Standalone Editor")
    dialog.resize(800, 600)
    layout = QVBoxLayout()
    dialog.setLayout(layout)

    # Initialize our editor state
    col = ensure_collection(mw.col)
    try:
        editor_state = EditorDialog(col)
    except ValueError as e:
        # Handle the case where no notes are marked for review
        from aqt.utils import showInfo

        showInfo(str(e))
        return

    # Load an Editor widget
    editor_widget = QWidget(dialog)
    editor = Editor(mw, editor_widget, dialog)
    editor.setNote(editor_state.current_note())
    layout.addWidget(editor.widget)

    # Create button layout with manual buttons
    button_layout = QHBoxLayout()
    save_button = QPushButton("Save")
    save_keep_flag_button = QPushButton("Save & Keep Flagged")
    skip_button = QPushButton("Skip")
    cancel_button = QPushButton("Cancel")

    button_layout.addWidget(save_button)
    button_layout.addWidget(save_keep_flag_button)
    button_layout.addWidget(skip_button)
    button_layout.addWidget(cancel_button)
    layout.addLayout(button_layout)

    # Define our button handlers
    def save_handler() -> None:
        editor.saveNow(lambda: after_save_complete_callback())

    def after_save_complete_callback() -> None:
        """Update the note in collection and close dialog."""
        # First save the current note
        current_note = editor_state.current_note()
        current_note = editor_state.strip_orange_flag(current_note)
        current_note.flush()

        # Then handle navigation to next note
        if editor_state.has_next_note():
            next_note = editor_state.move_to_next_note()
            editor.setNote(next_note)
        else:
            # No more notes to review
            dialog.accept()
            mw.reset()

    def save_keep_flag_handler() -> None:
        editor.saveNow(lambda: after_save_keep_flag_complete_callback())

    def after_save_keep_flag_complete_callback() -> None:
        """Save note but keep the orange flag for future editing."""
        # Save the current note without removing the flag
        current_note = editor_state.current_note()
        current_note = editor_state.save_note_keep_flag(current_note)

        # Then handle navigation to next note
        if editor_state.has_next_note():
            next_note = editor_state.move_to_next_note()
            editor.setNote(next_note)
        else:
            # No more notes to review
            dialog.accept()
            mw.reset()

    def skip_handler() -> None:
        # Discard any changes made to the note in the current editing session
        editor_state.restore_current_note()

        # Then handle navigation to next note
        if editor_state.has_next_note():
            next_note = editor_state.move_to_next_note()
            editor.setNote(next_note)
        else:
            # No more notes to review
            dialog.accept()
            mw.reset()

    def cancel_handler() -> None:
        # Discard any changes made to the note in the current editing session
        editor_state.restore_current_note()

        # Then close editor
        dialog.reject()
        mw.reset()

    # Connect the signals
    save_button.clicked.connect(save_handler)
    save_keep_flag_button.clicked.connect(save_keep_flag_handler)
    skip_button.clicked.connect(skip_handler)
    cancel_button.clicked.connect(cancel_handler)

    # Run as a "modal" dialog
    dialog.exec()


def add_custom_button(buttons, editor: Editor):
    """Add button to retrieve AI suggestions to Editor."""
    addon_dir = Path(__file__).parents[2]
    icon_path = os.path.join(addon_dir, "imgs", "ai-icon.png")
    button = editor.addButton(
        icon=icon_path,
        cmd="myCustomAction",
        func=lambda editor=editor: on_custom_action(editor),
        tip="Format with AI",
        keys="Ctrl+Alt+M",  # Optional keyboard shortcut
    )
    buttons.insert(5, button)  # Media buttons usually start around index 4-5
    return buttons


def on_custom_action(editor: Editor):
    from aqt import mw
    from aqt.utils import askUser, tooltip

    note = ensure_note(editor.note)
    original_fields = {}

    for field_name in note.keys():
        original_fields[field_name] = note[field_name]

    # NOTE: At the moment, we are only using the LLM to convert the front and
    # back of the note to lowercase
    # TODO: instantiate OpenAI and completer only once, and outside of this
    # function
    config = AddonConfig.create(mw)
    openai = OpenAIClient.create(config)
    formatter = NoteFormatter(openai)
    note = format_note_workflow(note, formatter)

    # Update the editor display to show the changes
    editor.loadNote()

    # Ask the user if they want to keep the changes
    if askUser("Apply changes?"):
        col = ensure_collection(editor.mw.col)
        col.update_note(note)
        tooltip("Changes applied")
    else:
        # User rejected changes, restore original content
        for field_name, original_content in original_fields.items():
            note[field_name] = original_content
        editor.loadNote()
