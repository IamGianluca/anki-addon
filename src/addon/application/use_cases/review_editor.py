from __future__ import annotations

from ...infrastructure.persistence.training_dataset import (
    create_training_dataset,
)
from ...infrastructure.ui.editor import EditorDialog
from ...utils import ensure_collection


def open_review_editor() -> None:
    """Open the batch review editor for notes flagged with the orange flag.

    Creates a dialog window with an Anki editor widget plus buttons for
    saving changes, skipping to the next note, or canceling the editing
    session. Saving records a training example and strips the flag;
    skipping or canceling restores the note's original content.
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
        showInfo(str(e))
        return

    # Initialize training dataset for storing examples
    training_dataset = create_training_dataset()

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

        # Store training example: capture updated fields before saving
        updated_fields = editor_state.get_note_fields_with_tags(current_note)
        training_dataset.save_example(
            note_id=current_note.id,
            original_fields=editor_state._original_fields,
            updated_fields=updated_fields,
        )

        current_note = editor_state.strip_orange_flag(current_note)
        col.update_note(current_note)

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
