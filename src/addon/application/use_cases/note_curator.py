from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ...application.services.curator_agent import (
    CurationSession,
    CuratorAgent,
)
from ...application.services.curator_tools import CuratorTools
from ...application.use_cases.apply_curation import apply_proposals
from ...domain.entities.note import NoteId
from ...infrastructure.configuration.settings import AddonConfig
from ...infrastructure.external_services.openai import OpenAIClient
from ...infrastructure.persistence.anki_note_repository import (
    AnkiNoteRepository,
)
from ...infrastructure.ui.curation_review import review_proposals
from ...utils import ensure_collection, ensure_note

if TYPE_CHECKING:
    from anki.collection import Collection
    from aqt.editor import Editor


def add_curator_button(buttons: list, editor: Editor) -> None:
    """Add the 'Curate cluster with AI' button to the editor."""
    addon_dir = Path(__file__).parents[2]
    icon_path = os.path.join(addon_dir, "imgs", "ai-icon.png")
    button = editor.addButton(
        icon=icon_path,
        cmd="curateCluster",
        func=lambda editor=editor: on_curator_action(editor),  # type: ignore[misc]
        tip="Curate cluster with AI",
        keys="Ctrl+Alt+K",
    )
    buttons.insert(6, button)


def on_curator_action(editor: Editor) -> None:
    """Run the curator agent on the editor's note in the background,
    then let the user review and apply the proposed changes."""
    from aqt import mw
    from aqt.operations import QueryOp
    from aqt.utils import showInfo, showWarning, tooltip
    from PyQt6.QtWidgets import QInputDialog

    note = ensure_note(editor.note)
    col = ensure_collection(mw.col)

    text, ok = QInputDialog.getMultiLineText(
        editor.widget,
        "Curate cluster with AI",
        "Optional instruction for the agent\n"
        "(e.g. 'focus on removing duplication'):",
    )
    if not ok:
        return
    instruction = text.strip() or None

    config = AddonConfig(mw.addonManager)
    repository = AnkiNoteRepository(
        col, config.basic_notetype, config.cloze_notetype
    )
    tools = CuratorTools(repository)
    agent = CuratorAgent(OpenAIClient(config), tools)
    seed_note_id = NoteId(note.id)

    def on_success(session: CurationSession) -> None:
        if len(session.change_set) == 0:
            showInfo(
                "The agent proposed no changes.\n\n"
                f"{session.summary or '(no summary)'}"
            )
            return
        approved = review_proposals(list(session.change_set), parent=mw)
        if approved is None:
            tooltip("Curation cancelled")
            return
        if not approved:
            tooltip("No proposals approved")
            return
        try:
            report = apply_proposals(
                repository,
                approved,
                deck_name=col.decks.current()["name"],
            )
        except Exception as e:
            showWarning(f"Failed to apply changes: {e}")
            return
        # The seed note may have been edited under the open editor
        try:
            editor.loadNote()
        except Exception:
            pass
        mw.reset()
        tooltip(str(report))

    def on_failure(error: Exception) -> None:
        showWarning(f"Curation failed: {error}")

    def op(col: Collection) -> CurationSession:
        # Runs on a background thread; only reads the collection and
        # calls the LLM — all proposals wait for user review.
        return agent.run(seed_note_id, instruction)

    QueryOp(parent=mw, op=op, success=on_success).failure(  # type: ignore[misc]
        on_failure
    ).with_progress("Curating cluster with AI...").run_in_background()
