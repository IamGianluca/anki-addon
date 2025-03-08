import os

from anki.notes import Note
from aqt.editor import Editor
from aqt.utils import showInfo


def add_custom_button(buttons, editor: Editor):
    """Add button to retrieve AI suggestions to Editor."""
    addon_dir = os.path.dirname(__file__)
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


def on_custom_action(editor):
    note_id = editor.note.id
    showInfo(f"Stay tuned... we will be use Ollama to edit note {note_id}")


def format_one_note(note: Note) -> Note:
    return note
