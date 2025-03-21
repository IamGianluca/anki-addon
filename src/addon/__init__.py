from aqt import QAction, gui_hooks, mw, qconnect

from .count_notes import (
    display_notes_marked_for_review_count,
)
from .edit_note import open_standalone_editor
from .format_notes import add_custom_button


def setup_addon():
    # Add option in "Tools" to count notes that require formatting changes
    action = QAction("Count notes marked for review", mw)
    qconnect(action.triggered, display_notes_marked_for_review_count)
    mw.form.menuTools.addAction(action)

    # Add option in "Tools" to format notes using AI
    action = QAction("Improve note using AI", mw)
    qconnect(action.triggered, open_standalone_editor)
    mw.form.menuTools.addAction(action)

    # Add button in Browser view to format notes using AI
    gui_hooks.editor_did_init_buttons.append(add_custom_button)
