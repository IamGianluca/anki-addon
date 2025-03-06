from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.qt import QDialog, QDialogButtonBox, QVBoxLayout, QWidget

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
    model = col.models.by_name("Basic")  # model is the note type
    note = Note(col, model)

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
