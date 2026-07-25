import pytest
from tests.fakes.note_fakes import FakeNoteRepository

from addon.application.use_cases.apply_curation import apply_proposals
from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
    ProposedChangeSet,
)


@pytest.fixture
def repository() -> FakeNoteRepository:
    return FakeNoteRepository(
        {
            1: AddonNote(
                front="What does beta_2 control in Adam?",
                back="Decay rate of the second moment estimate.",
                tags=["ml"],
            ),
            2: AddonNote(front="Redundant note", back="dup", tags=["ml"]),
        }
    )


def _change_set(repository: FakeNoteRepository) -> ProposedChangeSet:
    change_set = ProposedChangeSet()
    before_1 = repository.get(NoteId(1))
    change_set.add_edit(
        EditProposal(
            NoteId(1),
            before=before_1,
            after=AddonNote(
                front="What does beta_2 control in Adam?",
                back="Decay rate of the second moment estimate. "
                "Typical value: 0.999.",
                tags=["ml", "optimizers"],
            ),
            rationale="add typical value",
        )
    )
    change_set.add_create(
        CreateProposal(
            AddonNote(front="Default beta_2?", back="0.999", tags=["ml"]),
            rationale="gap in cluster",
        )
    )
    change_set.add_delete(
        DeleteProposal(
            NoteId(2),
            before=repository.get(NoteId(2)),
            rationale="covered by note 1",
        )
    )
    return change_set


def test_apply_edit_updates_fields_and_tags(
    repository: FakeNoteRepository,
) -> None:
    # Given
    proposals = list(_change_set(repository))

    # When
    report = apply_proposals(repository, proposals, deck_name="Default")

    # Then
    updated = repository.get(NoteId(1))
    assert "0.999" in updated.back
    assert updated.tags == ["ml", "optimizers"]
    assert report.edits == 1


def test_apply_create_adds_note_to_deck(
    repository: FakeNoteRepository,
) -> None:
    # Given
    proposals = list(_change_set(repository))

    # When
    report = apply_proposals(repository, proposals, deck_name="Default")

    # Then
    created_ids = repository.search("Default beta_2")
    assert len(created_ids) == 1
    assert repository.get(created_ids[0]).deck_name == "Default"
    assert report.creates == 1


def test_apply_delete_removes_note(
    repository: FakeNoteRepository,
) -> None:
    # Given
    proposals = list(_change_set(repository))

    # When
    report = apply_proposals(repository, proposals, deck_name="Default")

    # Then
    assert repository.search("Redundant") == []
    assert report.deletes == 1


def test_apply_empty_list_reports_zero(
    repository: FakeNoteRepository,
) -> None:
    # When
    report = apply_proposals(repository, [], deck_name="Default")

    # Then
    assert str(report) == "Applied 0 edit(s), 0 create(s), 0 delete(s)"
