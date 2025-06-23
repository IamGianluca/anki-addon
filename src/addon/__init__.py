from aqt import gui_hooks, mw, qconnect
from PyQt6.QtGui import QAction, QKeySequence

from .application.use_cases.duplicate_detector import (
    display_duplicate_notes_count,
    show_duplicate_notes_report,
)
from .application.use_cases.note_counter import (
    display_notes_marked_for_review_count,
)
from .application.use_cases.note_formatter import (
    add_custom_button,
    open_standalone_editor,
)


def setup_addon():
    # Add option in "Tools" to count notes that require formatting changes
    action = QAction("Count notes marked for review", mw)
    action.setShortcut(QKeySequence("c"))
    qconnect(action.triggered, display_notes_marked_for_review_count)
    mw.form.menuTools.addAction(action)

    # Add option in "Tools" to format notes using AI
    action = QAction("Improve note using AI", mw)
    action.setShortcut(QKeySequence("r"))
    qconnect(action.triggered, open_standalone_editor)
    mw.form.menuTools.addAction(action)

    # Add option in "Tools" to count duplicate notes
    action = QAction("Count duplicate notes", mw)
    action.setShortcut(QKeySequence("d"))
    qconnect(action.triggered, display_duplicate_notes_count)
    mw.form.menuTools.addAction(action)

    # Add option in "Tools" to show detailed duplicate report
    action = QAction("Show duplicate notes report", mw)
    action.setShortcut(QKeySequence("Ctrl+d"))
    qconnect(action.triggered, show_duplicate_notes_report)
    mw.form.menuTools.addAction(action)

    # Add button in Browser view to format notes using AI
    gui_hooks.editor_did_init_buttons.append(add_custom_button)
