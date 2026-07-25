"""Review dialog for the curation agent's proposed changes.

The pure rendering helpers (proposal_title / proposal_detail) are
module-level and Qt-free so unit tests can import them without paying
the PyQt import cost; Qt imports happen lazily inside review_proposals.
"""

from __future__ import annotations

import difflib

from ...domain.entities.note import AddonNote
from ...domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
    Proposal,
)


def proposal_title(proposal: Proposal) -> str:
    if isinstance(proposal, EditProposal):
        return f"Edit note {proposal.note_id}"
    if isinstance(proposal, CreateProposal):
        return f"Create note ({proposal.note.notetype.value})"
    if isinstance(proposal, DeleteProposal):
        return f"Delete note {proposal.note_id}"
    raise ValueError(f"unexpected proposal: {proposal}")


def proposal_detail(proposal: Proposal) -> str:
    """Plain-text rendering of a proposal: unified diff of the changed
    fields for edits, full content for creates and deletes."""
    if isinstance(proposal, EditProposal):
        return _edit_diff(proposal)
    if isinstance(proposal, CreateProposal):
        return _note_content(proposal.note)
    if isinstance(proposal, DeleteProposal):
        return _note_content(proposal.before)
    raise ValueError(f"unexpected proposal: {proposal}")


def review_proposals(
    proposals: list[Proposal], parent=None
) -> list[Proposal] | None:
    """Show a modal review of the proposed changes.

    Each proposal gets a checkable group box (checked = approved) with
    the agent's rationale and a diff/content view. Returns the approved
    proposals, or None if the user cancelled the dialog.
    """
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QGroupBox,
        QLabel,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    dialog = QDialog(parent)
    dialog.setWindowTitle("Review proposed changes")
    dialog.resize(700, 600)
    dialog_layout = QVBoxLayout(dialog)

    scroll = QScrollArea(dialog)
    scroll.setWidgetResizable(True)
    container = QWidget()
    proposals_layout = QVBoxLayout(container)

    boxes = []
    for proposal in proposals:
        box = QGroupBox(proposal_title(proposal))
        box.setCheckable(True)
        box.setChecked(True)
        box_layout = QVBoxLayout(box)

        rationale = QLabel(f"<i>{proposal.rationale}</i>")
        rationale.setWordWrap(True)
        box_layout.addWidget(rationale)

        detail = QTextEdit()
        detail.setReadOnly(True)
        detail.setFont(QFont("monospace"))
        detail.setPlainText(proposal_detail(proposal))
        detail.setMaximumHeight(160)
        box_layout.addWidget(detail)

        proposals_layout.addWidget(box)
        boxes.append(box)

    scroll.setWidget(container)
    dialog_layout.addWidget(scroll)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )
    ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    if ok_button is not None:
        ok_button.setText("Apply selected")
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    dialog_layout.addWidget(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return [p for p, box in zip(proposals, boxes) if box.isChecked()]
    return None


def _edit_diff(proposal: EditProposal) -> str:
    sections = []
    for label, before, after in [
        ("Front", proposal.before.front, proposal.after.front),
        ("Back", proposal.before.back, proposal.after.back),
        ("Tags", _tags(proposal.before), _tags(proposal.after)),
    ]:
        if before != after:
            sections.append(
                "\n".join(
                    difflib.unified_diff(
                        before.splitlines(),
                        after.splitlines(),
                        fromfile=f"{label} (before)",
                        tofile=f"{label} (after)",
                        lineterm="",
                    )
                )
            )
    return "\n\n".join(sections) or "(no changes)"


def _note_content(note: AddonNote) -> str:
    return f"Front: {note.front}\nBack: {note.back}\nTags: {_tags(note)}"


def _tags(note: AddonNote) -> str:
    return " ".join(note.tags) if note.tags else ""
