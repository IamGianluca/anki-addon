"""Review dialog for the curation agent's proposed changes.

The pure rendering helpers (proposal_title / proposal_detail) are
module-level and Qt-free so unit tests can import them without paying
the PyQt import cost; Qt imports happen lazily inside review_proposals.
"""

from __future__ import annotations

import difflib
import html
import re

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


# Block-level elements become newlines in the review text; inline
# tags are dropped, their text kept.
_BLOCK_TAGS = "div|p|pre|li|h[1-6]|ul|ol|table|thead|tbody|tr|td|th|blockquote"

# Fields on Better Markdown note types are Markdown: fenced blocks and
# backtick spans are code, where `<rev>`/`Vec<i32>`/`&&` are content,
# not markup, and must survive review decoding verbatim.
_FENCE_RE = re.compile(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$")
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


def display_text(field_html: str) -> str:
    """Review-display text of an HTML/Markdown field.

    Prose is decoded: `<br>` and block-level tags become newlines,
    entities are decoded (`&lt;rev&gt;` shows as `<rev>`), and remaining
    tags are dropped keeping their text. Code — fenced blocks and
    backtick spans — keeps its characters verbatim, with `<br>` lines,
    `&nbsp;` spaces, and entities decoded the way the addon does, so a
    field whose back is ```` ```bash<br>jj squash -r &lt;rev&gt;\n``` ````
    reads as exactly that command, not as a run of markup. This is
    display only: the applied change keeps the exact stored text.
    """

    def _decode_chunk(chunk: str) -> str:
        chunk = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.IGNORECASE)
        chunk = re.sub(
            rf"</?(?:{_BLOCK_TAGS})[^>]*>", "\n", chunk, flags=re.IGNORECASE
        )
        chunk = re.sub(r"<[^>]+>", "", chunk)
        chunk = html.unescape(chunk)
        return chunk.replace("\xa0", " ")

    def _decode_code_chunk(chunk: str) -> str:
        # Code is stored in Anki's HTML flavour: <br> and <div> are its
        # lines and &nbsp; its spaces. The addon normalizes both back
        # before rendering, so the review mirrors the card.
        chunk = re.sub(r"<br\s*/?>", "\n", chunk, flags=re.IGNORECASE)
        chunk = re.sub(
            r"</div>\s*<div[^>]*>", "\n", chunk, flags=re.IGNORECASE
        )
        chunk = re.sub(r"</?div[^>]*>", "\n", chunk, flags=re.IGNORECASE)
        return html.unescape(chunk).replace("\xa0", " ")

    code = re.compile(
        rf"{_FENCE_RE.pattern}|{_INLINE_CODE_RE.pattern}",
        flags=re.MULTILINE | re.DOTALL,
    )
    parts: list[str] = []
    pos = 0
    for match in code.finditer(field_html):
        parts.append(_decode_chunk(field_html[pos : match.start()]))
        parts.append(_decode_code_chunk(match.group(0)))
        pos = match.end()
    parts.append(_decode_chunk(field_html[pos:]))
    text = "".join(parts)
    return re.sub(r"\n{2,}", "\n", text).strip("\n")


def proposal_detail(proposal: Proposal) -> str:
    """Plain-text rendering of a proposal: unified diff of the changed
    fields for edits, full content for creates and deletes. Field
    content is decoded for review (`display_text`); the byte-exact HTML
    lives in the note itself."""
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
    fields = [
        ("Front", proposal.before.front, proposal.after.front),
        ("Back", proposal.before.back, proposal.after.back),
        ("Tags", _tags(proposal.before), _tags(proposal.after)),
    ]
    extra_names = set(proposal.before.extra_fields) | set(
        proposal.after.extra_fields
    )
    for name in sorted(extra_names):
        fields.append(
            (
                name,
                proposal.before.extra_fields.get(name, ""),
                proposal.after.extra_fields.get(name, ""),
            )
        )
    sections = [
        _field_diff(label, before, after)
        for label, before, after in fields
        if before != after
    ]
    return "\n\n".join(sections) or "(no changes)"


def _field_diff(label: str, before: str, after: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            display_text(before).splitlines(),
            display_text(after).splitlines(),
            fromfile=f"{label} (before)",
            tofile=f"{label} (after)",
            lineterm="",
        )
    )


def _note_content(note: AddonNote) -> str:
    lines = [
        f"Front: {display_text(note.front)}",
        f"Back: {display_text(note.back)}",
    ]
    lines.extend(
        f"{name}: {display_text(value)}"
        for name, value in note.extra_fields.items()
    )
    lines.append(f"Tags: {_tags(note)}")
    return "\n".join(lines)


def _tags(note: AddonNote) -> str:
    return " ".join(note.tags) if note.tags else ""
