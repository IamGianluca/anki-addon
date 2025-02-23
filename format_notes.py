import os
from aqt import gui_hooks
from aqt.utils import showInfo


def add_custom_button(buttons, editor):
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
    showInfo("Stay tuned...")
    # Add your functionality here
    # editor.note contains the current note being edited
    # editor.web gives access to the editor's webview


gui_hooks.editor_did_init_buttons.append(add_custom_button)
