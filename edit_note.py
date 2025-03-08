from anki.collection import Collection
from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.qt import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

from .count_notes import is_note_marked_for_review
from .utils import ensure_collection, ensure_deck


def open_standalone_editor() -> None:
    # Create a new window that appears on top of other windows with vertical layout
    dialog = QDialog(mw)
    dialog.setWindowTitle("Standalone Editor")
    dialog.resize(800, 600)
    layout = QVBoxLayout()
    dialog.setLayout(layout)

    # Create a temporary note. Later on, we will replace it with a real note
    col = ensure_collection(mw.col)
    note = get_notes_to_review(col)

    # Load an Editor widget
    editor = Editor(mw, QWidget(dialog), dialog)
    editor.setNote(note)
    layout.addWidget(editor.widget)

    # Add a button to save the changes and one to exit the widget
    button_box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
    )
    layout.addWidget(button_box)
    button_box.accepted.connect(lambda: save_note(note, editor, dialog))
    button_box.rejected.connect(dialog.reject)

    # Run as a "modal" dialog (block interactions with other windows in the application)
    dialog.exec()


def get_notes_to_review(col: Collection) -> Note:
    deck_id = col.decks.current()["id"]
    query = f"did:{deck_id}"
    note_ids = col.find_notes(query)

    for note_id in note_ids:
        if is_note_marked_for_review(note_id):
            return col.get_note(note_id)
    raise ValueError("No notes marked for review")


def save_note(note, editor, dialog):
    """Update note with current editor content"""
    editor.saveNow(lambda: on_save_complete(note, dialog))


def on_save_complete(note, dialog):
    """Add the note to collection and close dialog"""
    col = ensure_collection(mw.col)
    deck = ensure_deck(col.decks.id("Default"))
    col.add_note(note, deck)
    mw.reset()  # Refresh main window to show new card
    dialog.accept()
