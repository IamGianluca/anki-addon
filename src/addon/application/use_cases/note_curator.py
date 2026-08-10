from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ...application.services.curation_trace import (
    CurationTraceStore,
    TraceOutcome,
)
from ...application.services.curator_agent import (
    CurationSession,
    CuratorAgent,
)
from ...application.services.curator_tools import CuratorTools
from ...application.use_cases.apply_curation import apply_proposals
from ...domain.entities.note import AddonNote, NoteId
from ...infrastructure.configuration.settings import (
    AddonConfig,
    load_raw_config,
)
from ...infrastructure.persistence.anki_note_repository import (
    AnkiNoteRepository,
)
from ...infrastructure.services.completion_provider_factory import (
    create_completion_provider,
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

    raw = load_raw_config(mw.addonManager)
    traces = CurationTraceStore(
        _addon_root() / "traces",
        model=raw.get("openai_model")
        or raw.get("opencode_go_model")
        or "unknown",
        provider=raw.get("llm_provider", "openai"),
    )
    config = AddonConfig(mw.addonManager)
    repository = AnkiNoteRepository(
        col, config.basic_notetype, config.cloze_notetype
    )
    tools = CuratorTools(repository)
    agent = CuratorAgent(create_completion_provider(mw.addonManager), tools)
    seed_note_id = NoteId(note.id)

    def on_success(result: tuple[CurationSession, AddonNote]) -> None:
        session, seed_note = result
        if len(session.change_set) == 0:
            traces.save(
                session,
                seed_note,
                seed_note_id,
                instruction,
                TraceOutcome(status="no_changes"),
            )
            showInfo(
                "The agent proposed no changes.\n\n"
                f"{session.summary or '(no summary)'}"
            )
            return
        approved = review_proposals(list(session.change_set), parent=mw)
        if approved is None:
            traces.save(
                session,
                seed_note,
                seed_note_id,
                instruction,
                TraceOutcome(status="cancelled"),
            )
            tooltip("Curation cancelled")
            return
        rejected = [p for p in session.change_set if p not in approved]
        if not approved:
            traces.save(
                session,
                seed_note,
                seed_note_id,
                instruction,
                TraceOutcome(status="rejected", rejected=tuple(rejected)),
            )
            tooltip("No proposals approved")
            return
        try:
            report = apply_proposals(
                repository,
                approved,
                deck_name=col.decks.current()["name"],
            )
        except Exception as e:
            traces.save(
                session,
                seed_note,
                seed_note_id,
                instruction,
                TraceOutcome(status="failed", error=str(e)),
            )
            showWarning(f"Failed to apply changes: {e}")
            return
        traces.save(
            session,
            seed_note,
            seed_note_id,
            instruction,
            TraceOutcome(
                status="applied",
                approved=tuple(approved),
                rejected=tuple(rejected),
            ),
        )
        # Reload the editor's note in place: apply_proposals wrote
        # through freshly-fetched note objects, so the object the editor
        # holds (and anything aliasing it, like EditorDialog.review_notes
        # in the 'Improve note with AI' window) is still the pre-curation
        # copy. Re-rendering or saving from that stale object would
        # silently revert the applied edits.
        try:
            ensure_note(editor.note).load()
            editor.loadNote()
        except Exception:
            pass
        mw.reset()
        tooltip(str(report))

    def on_failure(error: Exception) -> None:
        traces.save_failure(seed_note_id, instruction, str(error))
        showWarning(f"Curation failed: {error}")

    def op(col: Collection) -> tuple[CurationSession, AddonNote]:
        # Runs on a background thread; only reads the collection and
        # calls the LLM — all proposals wait for user review. The seed
        # note is captured before the run so the trace shows what the
        # agent saw, not the post-apply state.
        seed_note = repository.get(seed_note_id)
        return agent.run(seed_note_id, instruction), seed_note

    QueryOp(parent=mw, op=op, success=on_success).failure(  # type: ignore[misc]
        on_failure
    ).with_progress("Curating cluster with AI...").run_in_background()


def _addon_root() -> Path:
    """The addon's root folder (where meta.json and config.json live)."""
    return Path(__file__).parents[4]
