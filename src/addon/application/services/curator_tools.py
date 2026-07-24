from __future__ import annotations

import dataclasses
import html
import re

from ...domain.entities.note import AddonNote, AddonNoteType, NoteId
from ...domain.entities.proposals import (
    ConflictingProposalError,
    CreateProposal,
    DeleteProposal,
    EditProposal,
    ProposedChangeSet,
)
from ...domain.repositories.note_repository import (
    InvalidSearchQueryError,
    NoteNotFoundError,
    NoteRepository,
)

_TAG_RE = re.compile(r"<[^>]+>")


class CuratorTools:
    """The tool surface exposed to the curation agent.

    Read tools query the NoteRepository directly; mutation tools only
    record proposals in the ProposedChangeSet — the agent has no write
    access to the collection, so nothing changes until the user reviews
    and approves the change set.

    Every tool returns a string observation and never raises: invalid
    input (unknown ids, bad notetypes, conflicting proposals) comes back
    as an "error: ..." observation so the agent can recover instead of
    crashing the loop on bad model output.
    """

    def __init__(
        self,
        repository: NoteRepository,
        change_set: ProposedChangeSet | None = None,
        snippet_length: int = 120,
    ) -> None:
        self._repository = repository
        self.change_set = change_set or ProposedChangeSet()
        self._snippet_length = snippet_length

    def search_notes(self, query: str, limit: int = 10) -> str:
        """Search the collection; return one line per hit with the note
        id and a plain-text front snippet."""
        try:
            note_ids = self._repository.search(query, limit)
        except InvalidSearchQueryError as e:
            return f"error: invalid search query {query!r}: {e}"
        if not note_ids:
            return f"No notes found for query: {query!r}"
        lines = []
        for note_id in note_ids:
            note = self._repository.get(note_id)
            lines.append(f"{note_id}: {self._snippet(note.front)}")
        return "\n".join(lines)

    def read_note(self, note_id: NoteId) -> str:
        """Return the full content of a note (fields are raw HTML, as
        stored)."""
        try:
            note = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._not_found(note_id)
        tags = " ".join(note.tags) if note.tags else ""
        return (
            f"Note {note_id}\n"
            f"Type: {note.notetype.value}\n"
            f"Front: {note.front}\n"
            f"Back: {note.back}\n"
            f"Tags: {tags}"
        )

    def propose_edit(
        self,
        note_id: NoteId,
        front: str,
        back: str,
        tags: list[str],
        rationale: str,
    ) -> str:
        """Record a proposal to replace a note's fields and tags."""
        try:
            before = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._not_found(note_id)
        after = dataclasses.replace(before, front=front, back=back, tags=tags)
        try:
            self.change_set.add_edit(
                EditProposal(note_id, before, after, rationale)
            )
        except ConflictingProposalError as e:
            return f"error: {e}"
        return f"Edit proposal recorded for note {note_id}."

    def propose_create(
        self,
        front: str,
        back: str,
        tags: list[str],
        notetype: str,
        rationale: str,
    ) -> str:
        """Record a proposal to create a new note."""
        try:
            note_type = AddonNoteType(notetype.lower())
        except ValueError:
            return (
                f"error: invalid notetype {notetype!r}; "
                "expected 'basic' or 'cloze'"
            )
        self.change_set.add_create(
            CreateProposal(
                AddonNote(
                    front=front, back=back, tags=tags, notetype=note_type
                ),
                rationale,
            )
        )
        return "Create proposal recorded."

    def propose_delete(self, note_id: NoteId, rationale: str) -> str:
        """Record a proposal to delete a note and its cards."""
        try:
            before = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._not_found(note_id)
        try:
            self.change_set.add_delete(
                DeleteProposal(note_id, before, rationale)
            )
        except ConflictingProposalError as e:
            return f"error: {e}"
        return f"Delete proposal recorded for note {note_id}."

    def propose_split(
        self,
        note_id: NoteId,
        kept_front: str,
        kept_back: str,
        kept_tags: list[str],
        new_notes: list[dict],
        rationale: str,
    ) -> str:
        """Record a proposal to split a note: the original is edited
        down to one facet (preserving its scheduling history) and each
        entry in `new_notes` becomes a create proposal.

        Each new_notes entry needs "front" and "back"; "tags" defaults
        to [] and "notetype" to the original note's type.
        """
        try:
            before = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._not_found(note_id)
        if not new_notes:
            return "error: split requires at least one new note"

        creates = []
        for i, fields in enumerate(new_notes):
            if "front" not in fields or "back" not in fields:
                return f"error: new_notes[{i}] must include 'front' and 'back'"
            try:
                note_type = AddonNoteType(
                    fields.get("notetype", before.notetype.value).lower()
                )
            except ValueError:
                return f"error: invalid notetype in new_notes[{i}]"
            creates.append(
                CreateProposal(
                    AddonNote(
                        front=fields["front"],
                        back=fields["back"],
                        tags=fields.get("tags", []),
                        notetype=note_type,
                    ),
                    rationale,
                )
            )

        after = dataclasses.replace(
            before, front=kept_front, back=kept_back, tags=kept_tags
        )
        try:
            self.change_set.add_edit(
                EditProposal(note_id, before, after, rationale)
            )
        except ConflictingProposalError as e:
            return f"error: {e}"
        for create in creates:
            self.change_set.add_create(create)
        return (
            f"Split proposal recorded for note {note_id}: "
            f"original edited down, {len(creates)} new note(s) proposed."
        )

    def _snippet(self, text: str) -> str:
        plain = _TAG_RE.sub("", html.unescape(text))
        plain = " ".join(plain.split())
        if len(plain) > self._snippet_length:
            return plain[: self._snippet_length] + "…"
        return plain

    @staticmethod
    def _not_found(note_id: NoteId) -> str:
        return f"error: note {note_id} not found"
