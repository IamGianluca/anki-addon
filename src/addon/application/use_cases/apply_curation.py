from __future__ import annotations

from dataclasses import dataclass

from ...domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
    Proposal,
)
from ...domain.repositories.note_repository import NoteRepository


@dataclass(frozen=True)
class ApplyReport:
    """Counts of proposals applied to the collection."""

    edits: int
    creates: int
    deletes: int

    def __str__(self) -> str:
        return (
            f"Applied {self.edits} edit(s), {self.creates} create(s), "
            f"{self.deletes} delete(s)"
        )


def apply_proposals(
    repository: NoteRepository,
    proposals: list[Proposal],
    deck_name: str,
) -> ApplyReport:
    """Apply approved proposals to the collection.

    Only call this with proposals the user has approved — the function
    applies everything it is given. New notes are created in
    `deck_name`. Deletions run last so a failure mid-way cannot leave a
    note both edited and deleted.
    """
    edits = creates = deletes = 0
    for proposal in proposals:
        if isinstance(proposal, EditProposal):
            repository.update(proposal.note_id, proposal.after)
            edits += 1
        elif isinstance(proposal, CreateProposal):
            repository.add(proposal.note, deck_name)
            creates += 1
    for proposal in proposals:
        if isinstance(proposal, DeleteProposal):
            repository.remove([proposal.note_id])
            deletes += 1
    return ApplyReport(edits, creates, deletes)
