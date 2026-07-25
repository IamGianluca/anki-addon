from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
)
from addon.infrastructure.ui.curation_review import (
    proposal_detail,
    proposal_title,
)

_BEFORE = AddonNote(
    front="What does beta_2 control in Adam?",
    back="Decay rate of the second moment estimate.",
    tags=["ml"],
)


def test_edit_title_includes_note_id() -> None:
    # Given
    proposal = EditProposal(NoteId(42), _BEFORE, _BEFORE, "r")

    # When / Then
    assert proposal_title(proposal) == "Edit note 42"


def test_create_title_includes_notetype() -> None:
    # Given
    proposal = CreateProposal(_BEFORE, "r")

    # When / Then
    assert proposal_title(proposal) == "Create note (basic)"


def test_delete_title_includes_note_id() -> None:
    # Given
    proposal = DeleteProposal(NoteId(42), _BEFORE, "r")

    # When / Then
    assert proposal_title(proposal) == "Delete note 42"


def test_edit_detail_shows_diff_of_changed_fields_only() -> None:
    # Given
    after = AddonNote(
        front=_BEFORE.front,
        back="Decay rate of the second moment estimate. Default: 0.999.",
        tags=["ml"],
    )
    proposal = EditProposal(NoteId(1), _BEFORE, after, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert "Back (before)" in detail
    assert "+Decay rate of the second moment estimate. Default: 0.999." in (
        detail
    )
    assert "-Decay rate of the second moment estimate." in detail
    # unchanged fields are omitted
    assert "Front (before)" not in detail
    assert "Tags (before)" not in detail


def test_edit_detail_marks_tag_changes() -> None:
    # Given
    after = AddonNote(
        front=_BEFORE.front, back=_BEFORE.back, tags=["ml", "optimizers"]
    )
    proposal = EditProposal(NoteId(1), _BEFORE, after, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert "Tags (before)" in detail
    assert "+ml optimizers" in detail


def test_edit_detail_without_changes_says_so() -> None:
    # Given
    proposal = EditProposal(NoteId(1), _BEFORE, _BEFORE, "r")

    # When / Then
    assert proposal_detail(proposal) == "(no changes)"


def test_create_detail_shows_full_content() -> None:
    # Given
    proposal = CreateProposal(_BEFORE, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert f"Front: {_BEFORE.front}" in detail
    assert f"Back: {_BEFORE.back}" in detail
    assert "Tags: ml" in detail


def test_delete_detail_shows_content_to_be_lost() -> None:
    # Given
    proposal = DeleteProposal(NoteId(1), _BEFORE, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert f"Front: {_BEFORE.front}" in detail


def test_edit_detail_diffs_changed_extra_fields() -> None:
    # Given
    before = AddonNote(
        front="Q",
        back="A",
        extra_fields={"Extra": "old example", "Difficulty": "2"},
    )
    after = AddonNote(
        front="Q",
        back="A",
        extra_fields={"Extra": "new example", "Difficulty": "2"},
    )
    proposal = EditProposal(NoteId(1), before, after, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert "Extra (before)" in detail
    assert "-old example" in detail
    assert "+new example" in detail
    # unchanged extra field is omitted
    assert "Difficulty (before)" not in detail


def test_create_detail_shows_extra_fields() -> None:
    # Given
    note = AddonNote(front="Q", back="A", extra_fields={"Extra": "E"})
    proposal = CreateProposal(note, "r")

    # When
    detail = proposal_detail(proposal)

    # Then
    assert "Extra: E" in detail
