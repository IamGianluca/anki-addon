"""Deterministic house-style checks on the notes an agent proposes to write.

These checks are standing requirements: they apply to every trial of
every task, independent of the task's own expectations, and post hoc
to production traces. The checker is a pure function over the fields a
change set would write, and eval records and traces share the same
record shape (`render_proposal`), so both can be audited without
re-running anything.

The agent is responsible for the final text of every card it proposes
to write: edited notes must comply in every field, created notes are
entirely written. There is no pass-through exemption — under the
house-style rule a trailing full stop is itself a defect, so a note
the agent edits must not keep one.

Rules live here as one function per rule, aggregated by
`check_formatting` — the cross-cutting metric in graders.py and the
audit section in summarize.py are the only consumers.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from addon.application.services.curation_trace import render_note
from addon.domain.entities.proposals import (
    CreateProposal,
    EditProposal,
    Proposal,
)

_TAG_RE = re.compile(r"<[^>]+>")
_SNIPPET_LEN = 60


@dataclass(frozen=True)
class WrittenField:
    """One field of a note the change set proposes to write.

    note_id is None for created notes.
    """

    note_id: int | None
    field: str  # "back" or an extra-field name such as "Extra"
    after: str


@dataclass(frozen=True)
class FormattingViolation:
    """One formatting rule broken by one written field."""

    rule: str
    note_id: int | None
    field: str
    snippet: str  # tail of the plain field text, for transcript reading


def written_fields(proposals: list[Proposal]) -> list[WrittenField]:
    """The back and extra fields of the notes a change set writes."""
    entries: list[dict] = []
    for proposal in proposals:
        if isinstance(proposal, EditProposal):
            entries.append(
                {
                    "type": "edit",
                    "note_id": proposal.note_id,
                    "before": render_note(proposal.before),
                    "after": render_note(proposal.after),
                }
            )
        elif isinstance(proposal, CreateProposal):
            entries.append(
                {"type": "create", "note": render_note(proposal.note)}
            )
    return _fields_from_entries(entries)


def written_fields_from_record(record: dict) -> list[WrittenField]:
    """The written fields of a persisted record's change set.

    Works on eval records and production traces alike — both render
    proposals through the same shape.
    """
    return _fields_from_entries(record.get("change_set", []))


def check_formatting(fields: list[WrittenField]) -> list[FormattingViolation]:
    """All formatting violations across the fields of a change set."""
    violations: list[FormattingViolation] = []
    for field in fields:
        violations.extend(_check_no_trailing_period(field))
    return violations


def _check_no_trailing_period(
    field: WrittenField,
) -> list[FormattingViolation]:
    """The last sentence of a written field does not end with a full stop.

    Naive by design: an abbreviation such as "etc." is still flagged.
    The edge-case task family pins down the rule's precise semantics;
    here a flag carries its snippet so the transcript settles the case.
    """
    text = _plain_text(field.after)
    if text.endswith("."):
        return [
            FormattingViolation(
                rule="no_trailing_period",
                note_id=field.note_id,
                field=field.field,
                snippet=f"…{text[-_SNIPPET_LEN:]}",
            )
        ]
    return []


def _fields_from_entries(entries: list[dict]) -> list[WrittenField]:
    fields: list[WrittenField] = []
    for entry in entries:
        kind = entry.get("type")
        if kind == "edit":
            after = entry["after"]
            fields.append(
                WrittenField(entry["note_id"], "back", after["back"])
            )
            for name in sorted(after.get("extra_fields", {})):
                fields.append(
                    WrittenField(
                        entry["note_id"],
                        name,
                        after["extra_fields"].get(name, ""),
                    )
                )
        elif kind == "create":
            note = entry["note"]
            fields.append(WrittenField(None, "back", note["back"]))
            for name, value in sorted(note.get("extra_fields", {}).items()):
                fields.append(WrittenField(None, name, value))
    return fields


def _plain_text(text: str) -> str:
    """Visible text of a raw HTML field: tags stripped, entities decoded."""
    return html.unescape(_TAG_RE.sub("", text)).strip()
