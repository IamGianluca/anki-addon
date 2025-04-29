from typing import Optional

from anki.collection import Collection
from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.qt import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from .note_counter import is_note_marked_for_review
from .utils import ensure_collection


class EditorDialog:
    """The EditorDialog class manages the state of editing sessions:

    - It retrieves all notes from the current deck that are marked for review
    - It keeps track of which note is currently being edited
    - It provides methods to navigate between notes, backup original content,
      and restore notes to their original state
    """

    def __init__(self, collection: Collection) -> None:
        self.col = collection
        self.review_notes = self.get_all_notes_to_review()
        self._current_index = 0

        if not self.review_notes:
            raise ValueError("No notes marked for review")

    def get_all_notes_to_review(self) -> list[Note]:
        """Retrieve all notes marked for review."""
        deck_id = self.col.decks.current()["id"]
        query = f"did:{deck_id}"
        note_ids = self.col.find_notes(query)

        review_notes = []
        for note_id in note_ids:
            if is_note_marked_for_review(note_id):
                review_notes.append(self.col.get_note(note_id))

        return review_notes

    def current_note(self) -> Note:
        note = self.review_notes[self._current_index]

        # Store fields and content for possible backup needs
        self.original_fields = {}
        for field_name in note.keys():
            self.original_fields[field_name] = note[field_name]

        return note

    def current_note_backup(self) -> Note:
        note = self.review_notes[self._current_index]
        for field_name, original_content in self.original_fields.items():
            note[field_name] = original_content
        return note

    def has_next_note(self) -> bool:
        return self._current_index < len(self.review_notes) - 1

    def next_note(self) -> Optional[Note]:
        if self.has_next_note():
            self._current_index += 1
            return self.review_notes[self._current_index]
        return None

    def restore_note_to_original(self) -> None:
        reloaded_note = self.current_note_backup()
        reloaded_note.flush()

    def strip_orange_flag(self, current_note: Note) -> Note:
        card_ids = self.col.find_cards(f"nid:{current_note.id}")
        for card_id in card_ids:
            card = self.col.get_card(card_id)
            if card.flags == 2:
                card.flags = 0
                card.flush()
        return current_note


def open_standalone_editor() -> None:
    """The open_standalone_editor() function creates the actual user interface:

    - It creates a dialog window with an Anki editor widget
    - It adds buttons for saving changes, skipping to the next note, or
      canceling the editing session
    - It implements handlers for each button's functionality
    """
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
    skip_button = QPushButton("Skip")
    cancel_button = QPushButton("Cancel")

    button_layout.addWidget(save_button)
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
            next_note = editor_state.next_note()
            editor.setNote(next_note)
        else:
            # No more notes to review
            dialog.accept()
            mw.reset()

    def skip_handler() -> None:
        # Discard any changes made to the note in the current editing session
        editor_state.restore_note_to_original()

        # Then handle navigation to next note
        if editor_state.has_next_note():
            next_note = editor_state.next_note()
            editor.setNote(next_note)
        else:
            # No more notes to review
            dialog.accept()
            mw.reset()

    def cancel_handler() -> None:
        # Discard any changes made to the note in the current editing session
        editor_state.restore_note_to_original()

        # Then close editor
        dialog.reject()
        mw.reset()

    # Connect the signals
    save_button.clicked.connect(save_handler)
    skip_button.clicked.connect(skip_handler)
    cancel_button.clicked.connect(cancel_handler)

    # Run as a "modal" dialog
    dialog.exec()
