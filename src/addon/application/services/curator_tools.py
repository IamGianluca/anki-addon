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

    Pending create proposals get provisional ids (-1, -2, ...) —
    negative ints cannot collide with Anki's positive note ids. Every
    action that takes a note_id accepts them, so the agent can read,
    revise, split, or withdraw notes it proposed but that are not in
    the collection yet. The ids live here (not on CreateProposal)
    because they are an agent-facing session concern: once the user
    approves, creates are inserted and get real ids from Anki.
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
        self._creates_by_id: dict[int, CreateProposal] = {}
        self._next_provisional_id = -1
        # Split lineage: parent note id -> provisional ids of the new
        # notes born from its splits. Guards against re-splitting a
        # note (which would duplicate the children) and against
        # deleting a parent while its children are still pending.
        self._split_children: dict[int, list[int]] = {}

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
        stored). A provisional id reads the pending create proposal."""
        pending = self._creates_by_id.get(note_id)
        if pending is not None:
            note = pending.note
            header = (
                f"Note {note_id} "
                "(proposed new note, not yet in the collection)"
            )
        else:
            try:
                note = self._repository.get(note_id)
            except NoteNotFoundError:
                return self._unknown_id(note_id)
            header = f"Note {note_id}"
        tags = " ".join(note.tags) if note.tags else ""
        extras = "".join(
            f"{name}: {value}\n" for name, value in note.extra_fields.items()
        )
        return (
            f"{header}\n"
            f"Type: {note.notetype.value}\n"
            f"Front: {note.front}\n"
            f"Back: {note.back}\n"
            f"{extras}"
            f"Tags: {tags}"
        )

    def propose_edit(
        self,
        note_id: NoteId,
        front: str,
        back: str,
        tags: list[str],
        rationale: str,
        extra_fields: dict[str, str] | None = None,
    ) -> str:
        """Record a proposal to replace a note's fields and tags.

        extra_fields uses merge semantics: provided keys override the
        current values, unmentioned keys are preserved, and an empty
        string clears a field.

        A provisional id revises that pending create proposal instead.
        Either way, the newer proposal replaces the older one.
        """
        pending = self._creates_by_id.get(note_id)
        if pending is not None:
            merged = {**pending.note.extra_fields, **(extra_fields or {})}
            revised = CreateProposal(
                dataclasses.replace(
                    pending.note,
                    front=front,
                    back=back,
                    tags=tags,
                    extra_fields=merged,
                ),
                rationale,
            )
            self.change_set.replace_create(pending, revised)
            self._creates_by_id[note_id] = revised
            return f"Create proposal {note_id} updated."
        try:
            before = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._unknown_id(note_id)
        merged_extra = {**before.extra_fields, **(extra_fields or {})}
        after = dataclasses.replace(
            before,
            front=front,
            back=back,
            tags=tags,
            extra_fields=merged_extra,
        )
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
        extra_fields: dict[str, str] | None = None,
    ) -> str:
        """Record a proposal to create a new note; return its
        provisional id so the agent can reference it later."""
        try:
            note_type = AddonNoteType(notetype.lower())
        except ValueError:
            return (
                f"error: invalid notetype {notetype!r}; "
                "expected 'basic' or 'cloze'"
            )
        proposal = CreateProposal(
            AddonNote(
                front=front,
                back=back,
                tags=tags,
                notetype=note_type,
                extra_fields=extra_fields or {},
            ),
            rationale,
        )
        self.change_set.add_create(proposal)
        provisional_id = self._register_create(proposal)
        return (
            f"Create proposal recorded (id {provisional_id}). Use this "
            "id with propose_edit, propose_split, or propose_delete to "
            "revise, split, or withdraw it."
        )

    def propose_delete(self, note_id: NoteId, rationale: str) -> str:
        """Record a proposal to delete a note and its cards. On a
        provisional id, withdraws that pending create proposal instead
        — the collection is not affected."""
        if note_id in self._creates_by_id:
            children = self._live_split_children(note_id)
            if children:
                return self._pending_children_error(note_id, children)
            self.change_set.remove_create(self._creates_by_id.pop(note_id))
            return (
                f"Create proposal {note_id} withdrawn; "
                "the collection is unchanged."
            )
        children = self._live_split_children(note_id)
        if children:
            return self._pending_children_error(note_id, children)
        try:
            before = self._repository.get(note_id)
        except NoteNotFoundError:
            return self._unknown_id(note_id)
        try:
            self.change_set.add_delete(
                DeleteProposal(note_id, before, rationale)
            )
        except ConflictingProposalError as e:
            return f"error: {e}"
        return f"Delete proposal recorded for note {note_id}."

    def review_changeset(self) -> str:
        """Render the after-state of every note affected by the change
        set, so the agent can review atomicity before finishing.

        Returns a formatted block showing each note's effective content
        after applying all proposals. Notes not in the change set are
        omitted — the agent only needs to review what changed.
        """
        if not self.change_set:
            return "No changes proposed."

        # Build the effective "after" state for each affected note.
        # Edits replace, creates add, deletes remove. New notes appear
        # under their provisional ids so the agent can reference them.
        after_notes: dict[int, AddonNote] = {}
        for proposal in self.change_set:
            if isinstance(proposal, EditProposal):
                after_notes[proposal.note_id] = proposal.after
            elif isinstance(proposal, CreateProposal):
                after_notes[self._provisional_id_of(proposal)] = proposal.note
            # Deletes: note is removed, so don't include it.

        lines = ["Proposed notes after applying changes:"]
        for note_id, note in sorted(
            after_notes.items(), key=lambda kv: (kv[0] < 0, abs(kv[0]))
        ):
            label = f"Note {note_id} (new)" if note_id < 0 else f"Note {note_id}"
            tags = ", ".join(note.tags) if note.tags else "(none)"
            lines.append(
                f"{label} [tags: {tags}]\n"
                f"  Front: {note.front}\n"
                f"  Back:  {note.back}"
            )
            if note.extra_fields:
                lines.append(
                    "  Extra: "
                    + ", ".join(
                        f"{k}={v}" for k, v in note.extra_fields.items()
                    )
                )
        return "\n".join(lines)

    def propose_split(
        self,
        note_id: NoteId,
        kept_front: str,
        kept_back: str,
        kept_tags: list[str],
        new_notes: list[dict],
        rationale: str,
        kept_extra_fields: dict[str, str] | None = None,
    ) -> str:
        """Record a proposal to split a note: the original is edited
        down to one facet (preserving its scheduling history) and each
        entry in `new_notes` becomes a create proposal.

        Each new_notes entry needs "front" and "back"; "tags" defaults
        to [] and "notetype" to the original note's type.

        A provisional id splits a pending create instead: the kept part
        revises it, and each new_notes entry becomes its own pending
        create with a fresh provisional id. A note cannot be split
        again while new notes from an earlier split are still pending.
        """
        pending = self._creates_by_id.get(note_id)
        if pending is not None:
            before = pending.note
        else:
            try:
                before = self._repository.get(note_id)
            except NoteNotFoundError:
                return self._unknown_id(note_id)
        children = self._live_split_children(note_id)
        if children:
            return self._pending_children_error(note_id, children)
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
                        extra_fields=fields.get("extra_fields", {}),
                    ),
                    rationale,
                )
            )

        merged_extra = {**before.extra_fields, **(kept_extra_fields or {})}
        after = dataclasses.replace(
            before,
            front=kept_front,
            back=kept_back,
            tags=kept_tags,
            extra_fields=merged_extra,
        )
        if pending is not None:
            revised = CreateProposal(after, rationale)
            self.change_set.replace_create(pending, revised)
            self._creates_by_id[note_id] = revised
        else:
            try:
                self.change_set.add_edit(
                    EditProposal(note_id, before, after, rationale)
                )
            except ConflictingProposalError as e:
                return f"error: {e}"
        child_ids = []
        for create in creates:
            self.change_set.add_create(create)
            child_ids.append(self._register_create(create))
        self._split_children.setdefault(note_id, []).extend(child_ids)
        return (
            f"Split proposal recorded for note {note_id}: original "
            f"edited down, {len(creates)} new note(s) proposed "
            f"(ids {', '.join(map(str, child_ids))})."
        )

    def _register_create(self, proposal: CreateProposal) -> int:
        """Assign a fresh provisional id to a pending create."""
        provisional_id = self._next_provisional_id
        self._next_provisional_id -= 1
        self._creates_by_id[provisional_id] = proposal
        return provisional_id

    def _provisional_id_of(self, proposal: CreateProposal) -> int:
        """The provisional id of a pending create; registers it if it
        somehow bypassed propose_create/propose_split."""
        for provisional_id, p in self._creates_by_id.items():
            if p is proposal:
                return provisional_id
        return self._register_create(proposal)

    def _live_split_children(self, note_id: NoteId) -> list[int]:
        """Provisional ids of this note's split children that are still
        pending (withdrawn children no longer block re-splitting)."""
        return [
            child
            for child in self._split_children.get(note_id, [])
            if child in self._creates_by_id
        ]

    @staticmethod
    def _pending_children_error(note_id: NoteId, children: list[int]) -> str:
        return (
            f"error: note {note_id} has pending new notes {children} "
            "from an earlier split; revise or withdraw them first"
        )

    def _snippet(self, text: str) -> str:
        plain = _TAG_RE.sub("", html.unescape(text))
        plain = " ".join(plain.split())
        if len(plain) > self._snippet_length:
            return plain[: self._snippet_length] + "…"
        return plain

    @staticmethod
    def _unknown_id(note_id: NoteId) -> str:
        if note_id < 0:
            return (
                f"error: no pending create proposal with id {note_id} "
                "(it may have been withdrawn)"
            )
        return f"error: note {note_id} not found"
