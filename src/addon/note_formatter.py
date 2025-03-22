import os

from aqt.editor import Editor
from aqt.utils import askUser, tooltip

from .utils import ensure_collection, ensure_note


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


def on_custom_action(editor: Editor):
    note = ensure_note(editor.note)
    original_fields = {}

    for field_name in note.keys():
        original_fields[field_name] = note[field_name]

    # Convert front and back of the note to lowercase
    # TODO: Call LLM to improve note
    for field_name in note.keys():
        current_content = note[field_name]
        transformed_content = current_content.lower()
        note[field_name] = transformed_content

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
