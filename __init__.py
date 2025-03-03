from aqt import QAction, gui_hooks, mw, qconnect

from . import utils
from .count_notes import (
    display_notes_marked_for_review_count,
)
from .edit_note import open_standalone_editor
from .format_notes import add_custom_button

action = QAction("Count notes marked for review", mw)
qconnect(action.triggered, display_notes_marked_for_review_count)
mw.form.menuTools.addAction(action)

action = QAction("Improve note using AI", mw)
qconnect(action.triggered, open_standalone_editor)
mw.form.menuTools.addAction(action)

gui_hooks.editor_did_init_buttons.append(add_custom_button)
