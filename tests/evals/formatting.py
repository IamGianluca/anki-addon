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

The notation the rules assume follows the user's real pipeline: cards
on the Better Markdown note types render fields as Markdown
(ReactMarkdown, KaTeX, react-syntax-highlighter), and the addon
normalizes Anki's HTML flavour back to Markdown before parsing —
`<br>` becomes a newline, `&nbsp;` becomes a space, and entities are
decoded. Fields therefore store `<br>` for every line break,
`&nbsp;` for every extra space, and `&lt;`/`&gt;`/`&amp;` for `<`/`>`/
`&`: written that way, the field reads correctly in Anki's editor and
renders identically on the card.

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

# HTML tags Anki fields legitimately carry; anything else that looks
# like a tag (`<rev>`, `<foo>`) is text that was not escaped.
_ALLOWED_TAGS = frozenset(
    {
        "a",
        "abbr",
        "b",
        "big",
        "blockquote",
        "br",
        "cite",
        "code",
        "del",
        "div",
        "em",
        "font",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "i",
        "img",
        "ins",
        "kbd",
        "li",
        "mark",
        "ol",
        "p",
        "pre",
        "q",
        "s",
        "samp",
        "small",
        "span",
        "strike",
        "strong",
        "sub",
        "sup",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "tt",
        "u",
        "ul",
        "var",
    }
)
_ENTITY_RE = re.compile(
    r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);"
)
_TAG_WITH_NAME_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_RUN_OF_SPACES_RE = re.compile(r" {2,}|\t")


@dataclass(frozen=True)
class WrittenField:
    """One field of a note the change set proposes to write.

    note_id is None for created notes.
    """

    note_id: int | None
    field: str  # "front", "back", or an extra-field name such as "Extra"
    after: str


@dataclass(frozen=True)
class FormattingViolation:
    """One formatting rule broken by one written field."""

    rule: str
    note_id: int | None
    field: str
    snippet: str  # tail of the plain field text, for transcript reading


def written_fields(proposals: list[Proposal]) -> list[WrittenField]:
    """The front, back, and extra fields of the notes a change set
    writes."""
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
        violations.extend(_check_raw_newline(field))
        violations.extend(_check_raw_spaces(field))
        violations.extend(_check_unescaped_html(field))
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


def _check_raw_newline(
    field: WrittenField,
) -> list[FormattingViolation]:
    """A written field contains a literal newline.

    Anki's editor renders the field as HTML, so a `\n` is one more
    whitespace character: it folds to a space in the editor and the
    line structure is lost (and the note cannot be re-edited safely).
    A line break is written `<br>` everywhere — prose, code fences,
    and math alike; the addon turns `<br>` back into a newline before
    it parses the markdown, so the card is unaffected. A blank line
    between paragraphs is `<br><br>`.
    """
    if "\n" in field.after or "\r" in field.after:
        return [
            FormattingViolation(
                rule="raw_newline",
                note_id=field.note_id,
                field=field.field,
                snippet=_escaped_snippet(field.after),
            )
        ]
    return []


def _check_raw_spaces(
    field: WrittenField,
) -> list[FormattingViolation]:
    """A written field contains a run of raw spaces (or a tab).

    HTML collapses a run of spaces to one, in the editor and on the
    card, so indentation and alignment written as raw spaces read
    wrong wherever Anki shows the field as HTML. Every space beyond a
    single one is `&nbsp;`, which the addon turns back into a space
    before it renders. The check ignores markup: tags and entities
    are removed before the runs are looked for.
    """
    text = _HTML_COMMENT_RE.sub("", field.after)
    # Tags and entities become a marker, not nothing: deleting them
    # would fuse the spaces around them into a false run.
    text = _ENTITY_RE.sub("x", text)
    text = _TAG_WITH_NAME_RE.sub("x", text)
    if _RUN_OF_SPACES_RE.search(text):
        return [
            FormattingViolation(
                rule="raw_spaces",
                note_id=field.note_id,
                field=field.field,
                snippet=_escaped_snippet(field.after),
            )
        ]
    return []


def _check_unescaped_html(
    field: WrittenField,
) -> list[FormattingViolation]:
    """A written field carries a raw `<`, `>`, or `&` outside markup.

    The addon decodes HTML entities before it parses the markdown, so
    the field stores HTML-significant characters as entities — `&lt;`,
    `&gt;`, `&amp;` — and the renderer sees the decoded characters
    again. A raw `<` never reaches the renderer: Anki reads it as an
    HTML tag first, the tag swallows the text after it, and the note
    is corrupted (a code fence holding `<rev>` loses the placeholder
    and gains a stray closing tag). The check therefore runs on the
    whole field, code and math included, not just the prose.
    """
    text = _HTML_COMMENT_RE.sub("", field.after)
    text = _ENTITY_RE.sub("", text)

    def _drop_allowed(match: re.Match) -> str:
        name = match.group(1).lower()
        return "" if name in _ALLOWED_TAGS else match.group(0)

    text = _TAG_WITH_NAME_RE.sub(_drop_allowed, text)
    if "<" in text or ">" in text or "&" in text:
        return [
            FormattingViolation(
                rule="unescaped_html",
                note_id=field.note_id,
                field=field.field,
                snippet=_escaped_snippet(field.after),
            )
        ]
    return []


def _escaped_snippet(text: str) -> str:
    """Tail of the raw field, with newlines escaped so summaries stay
    one line per violation."""
    return text[-_SNIPPET_LEN:].replace("\n", "\\n").replace("\r", "\\r")


def _fields_from_entries(entries: list[dict]) -> list[WrittenField]:
    fields: list[WrittenField] = []
    for entry in entries:
        kind = entry.get("type")
        if kind == "edit":
            after = entry["after"]
            fields.append(
                WrittenField(entry["note_id"], "front", after.get("front", ""))
            )
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
            fields.append(WrittenField(None, "front", note.get("front", "")))
            fields.append(WrittenField(None, "back", note["back"]))
            for name, value in sorted(note.get("extra_fields", {}).items()):
                fields.append(WrittenField(None, name, value))
    return fields


def _plain_text(text: str) -> str:
    """Visible text of a raw HTML field: break tags become spaces,
    remaining tags stripped, entities decoded."""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?div[^>]*>", " ", text, flags=re.IGNORECASE)
    return html.unescape(_TAG_RE.sub("", text)).strip()
