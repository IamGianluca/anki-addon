from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Union

from .note import AddonNote, NoteId


@dataclass(frozen=True)
class EditProposal:
    """Proposed modification of an existing note.

    Stores a snapshot of the note at proposal time (`before`) so the
    change can be reviewed as a diff and stale proposals detected.
    """

    note_id: NoteId
    before: AddonNote
    after: AddonNote
    rationale: str


@dataclass(frozen=True)
class CreateProposal:
    """Proposed new note."""

    note: AddonNote
    rationale: str


@dataclass(frozen=True)
class DeleteProposal:
    """Proposed deletion of an existing note (`before` is the snapshot
    at proposal time)."""

    note_id: NoteId
    before: AddonNote
    rationale: str


Proposal = Union[EditProposal, CreateProposal, DeleteProposal]


class ConflictingProposalError(Exception):
    """Raised when a proposal conflicts with one already recorded
    (e.g. editing a note that is already proposed for deletion)."""


class ProposedChangeSet:
    """The set of changes a curation session proposes to the user.

    Aggregate protecting the proposal invariants:
    - a newer edit proposal for a note replaces the older one
    - a delete proposal supersedes pending edits for that note
    - editing or re-deleting a note already proposed for deletion is
      rejected with ConflictingProposalError

    Proposals carry no effect on the collection until the user approves
    them and they are applied through a NoteRepository.
    """

    def __init__(self) -> None:
        self._proposals: list[Proposal] = []

    def add_edit(self, proposal: EditProposal) -> None:
        self._ensure_not_deleted(proposal.note_id)
        self._remove_pending_edits(proposal.note_id)
        self._proposals.append(proposal)

    def add_create(self, proposal: CreateProposal) -> None:
        self._proposals.append(proposal)

    def add_delete(self, proposal: DeleteProposal) -> None:
        self._ensure_not_deleted(proposal.note_id)
        self._remove_pending_edits(proposal.note_id)
        self._proposals.append(proposal)

    def _ensure_not_deleted(self, note_id: NoteId) -> None:
        if any(
            isinstance(p, DeleteProposal) and p.note_id == note_id
            for p in self._proposals
        ):
            raise ConflictingProposalError(
                f"note {note_id} is already proposed for deletion"
            )

    def _remove_pending_edits(self, note_id: NoteId) -> None:
        self._proposals = [
            p
            for p in self._proposals
            if not (isinstance(p, EditProposal) and p.note_id == note_id)
        ]

    def __iter__(self) -> Iterator[Proposal]:
        return iter(self._proposals)

    def __len__(self) -> int:
        return len(self._proposals)
