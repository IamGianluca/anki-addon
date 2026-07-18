def setup_addon() -> None:
    # Imports deferred into this function: importing any addon submodule
    # (e.g. from tests) executes this package's __init__, and aqt/PyQt6
    # add seconds of startup overhead.
    from aqt import gui_hooks, mw, qconnect
    from PyQt6.QtGui import QAction, QKeySequence

    from .application.use_cases.note_counter import (
        display_notes_marked_for_review_count,
    )
    from .application.use_cases.note_formatter import (
        add_custom_button,
        open_review_editor,
    )

    # Add option in "Tools" to count notes that require formatting changes
    action = QAction("Count notes marked for review", mw)
    action.setShortcut(QKeySequence("c"))
    qconnect(action.triggered, display_notes_marked_for_review_count)
    mw.form.menuTools.addAction(action)

    # Add option in "Tools" to format notes using AI
    action = QAction("Improve note using AI", mw)
    action.setShortcut(QKeySequence("r"))
    qconnect(action.triggered, open_review_editor)
    mw.form.menuTools.addAction(action)

    # Add button in Browser view to format notes using AI
    gui_hooks.editor_did_init_buttons.append(add_custom_button)
