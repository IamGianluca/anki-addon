import pytest
from tests.fakes.note_fakes import FakeNoteRepository

from addon.application.services.curator_tools import CuratorTools
from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
)


@pytest.fixture
def adam_cluster() -> dict[int, AddonNote]:
    return {
        1: AddonNote(
            front="What does beta_2 control in Adam?",
            back="The exponential decay rate of the second moment "
            "estimate. Typical value: 0.999.",
            tags=["ml", "optimizers"],
        ),
        2: AddonNote(
            front="What does beta_1 control in Adam?",
            back="The exponential decay rate of the first moment "
            "estimate. Typical value: 0.9.",
            tags=["ml", "optimizers"],
        ),
        3: AddonNote(
            front="How do beta_1 and beta_2 work together in Adam?",
            back="beta_1 smooths the gradient signal; beta_2 scales "
            "the step size per parameter.",
            tags=["ml", "optimizers"],
        ),
        4: AddonNote(
            front="What is the capital of France?",
            back="Paris",
            tags=["geography"],
        ),
    }


@pytest.fixture
def tools(adam_cluster: dict[int, AddonNote]) -> CuratorTools:
    return CuratorTools(FakeNoteRepository(adam_cluster))


def _edits(tools: CuratorTools) -> list[EditProposal]:
    return [p for p in tools.change_set if isinstance(p, EditProposal)]


def _creates(tools: CuratorTools) -> list[CreateProposal]:
    return [p for p in tools.change_set if isinstance(p, CreateProposal)]


def _deletes(tools: CuratorTools) -> list[DeleteProposal]:
    return [p for p in tools.change_set if isinstance(p, DeleteProposal)]


def test_search_returns_matching_notes_with_snippets(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.search_notes("beta")

    # Then
    assert "1:" in result
    assert "2:" in result
    assert "3:" in result
    assert "4:" not in result
    assert "beta_2 control in Adam" in result


def test_search_reports_invalid_query(tools: CuratorTools) -> None:
    # When
    result = tools.search_notes('"unbalanced')

    # Then
    assert result.startswith("error: invalid search query")


def test_search_reports_when_nothing_matches(tools: CuratorTools) -> None:
    # When
    result = tools.search_notes("kubernetes")

    # Then
    assert result == "No notes found for query: 'kubernetes'"


def test_search_snippets_are_plain_text_and_truncated() -> None:
    # Given
    long_html_front = "<b>Bold</b><br>" + "x" * 200
    repo = FakeNoteRepository({1: AddonNote(front=long_html_front, back="")})
    tools = CuratorTools(repo)

    # When
    result = tools.search_notes("bold")

    # Then
    snippet_line = result.strip()
    assert "<b>" not in snippet_line
    assert snippet_line.endswith("…")
    assert len(snippet_line) < 140


def test_read_note_returns_full_content(tools: CuratorTools) -> None:
    # When
    result = tools.read_note(NoteId(1))

    # Then
    assert "Note 1" in result
    assert "Type: basic" in result
    assert "Front: What does beta_2 control in Adam?" in result
    assert "second moment" in result
    assert "Tags: ml optimizers" in result


def test_read_note_reports_unknown_id(tools: CuratorTools) -> None:
    # When
    result = tools.read_note(NoteId(999))

    # Then
    assert result == "error: note 999 not found"


def test_propose_edit_records_before_and_after(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_edit(
        NoteId(1),
        front="New front",
        back="New back",
        tags=["ml"],
        rationale="tighter wording",
    )

    # Then
    assert result == "Edit proposal recorded for note 1."
    (edit,) = _edits(tools)
    assert edit.before.front == "What does beta_2 control in Adam?"
    assert edit.after.front == "New front"
    assert edit.after.tags == ["ml"]
    assert edit.rationale == "tighter wording"


def test_propose_edit_reports_unknown_note(tools: CuratorTools) -> None:
    # When
    result = tools.propose_edit(
        NoteId(999),
        front="x",
        back="y",
        tags=[],
        rationale="r",
    )

    # Then
    assert result == "error: note 999 not found"
    assert len(tools.change_set) == 0


def test_second_edit_for_same_note_replaces_the_first(
    tools: CuratorTools,
) -> None:
    # Given
    tools.propose_edit(NoteId(1), "first", "back", [], "r1")

    # When
    tools.propose_edit(NoteId(1), "second", "back", [], "r2")

    # Then
    (edit,) = _edits(tools)
    assert edit.after.front == "second"
    assert edit.rationale == "r2"


def test_propose_edit_rejected_when_note_proposed_for_deletion(
    tools: CuratorTools,
) -> None:
    # Given
    tools.propose_delete(NoteId(1), "not useful")

    # When
    result = tools.propose_edit(NoteId(1), "x", "y", [], "r")

    # Then
    assert result.startswith("error:")
    assert _edits(tools) == []


def test_propose_create_records_new_note(tools: CuratorTools) -> None:
    # When
    result = tools.propose_create(
        front="What is the typical value of epsilon in Adam?",
        back="1e-8",
        tags=["ml", "optimizers"],
        notetype="basic",
        rationale="cluster lacks epsilon coverage",
    )

    # Then
    assert result == "Create proposal recorded."
    (create,) = _creates(tools)
    assert create.note.back == "1e-8"
    assert create.note.notetype.value == "basic"
    assert create.rationale == "cluster lacks epsilon coverage"


def test_propose_create_rejects_invalid_notetype(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_create("f", "b", [], "markdown", "r")

    # Then
    assert result.startswith("error: invalid notetype")
    assert _creates(tools) == []


def test_propose_delete_records_before_snapshot(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_delete(NoteId(4), "off-topic for this deck")

    # Then
    assert result == "Delete proposal recorded for note 4."
    (delete,) = _deletes(tools)
    assert delete.note_id == 4
    assert delete.before.back == "Paris"


def test_propose_delete_supersedes_pending_edit(
    tools: CuratorTools,
) -> None:
    # Given
    tools.propose_edit(NoteId(1), "x", "y", [], "r")

    # When
    tools.propose_delete(NoteId(1), "redundant")

    # Then
    assert _edits(tools) == []
    assert len(_deletes(tools)) == 1


def test_propose_split_records_edit_and_creates(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_split(
        NoteId(3),
        kept_front="What does beta_1 do in Adam?",
        kept_back="Smooths the gradient signal.",
        kept_tags=["ml", "optimizers"],
        new_notes=[
            {
                "front": "What does beta_2 do in Adam?",
                "back": "Scales the step size per parameter.",
                "tags": ["ml", "optimizers"],
            },
            {
                "front": "Adam: typical beta_1/beta_2 values?",
                "back": "0.9 / 0.999",
            },
        ],
        rationale="note covers two ideas",
    )

    # Then
    assert "Split proposal recorded for note 3" in result
    (edit,) = _edits(tools)
    assert edit.after.back == "Smooths the gradient signal."
    creates = _creates(tools)
    assert len(creates) == 2
    assert creates[0].note.tags == ["ml", "optimizers"]
    # notetype not given: inherits the original note's type
    assert creates[1].note.notetype == edit.before.notetype


def test_propose_split_reports_unknown_note_and_records_nothing(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_split(
        NoteId(999),
        kept_front="f",
        kept_back="b",
        kept_tags=[],
        new_notes=[{"front": "a", "back": "b"}],
        rationale="r",
    )

    # Then
    assert result == "error: note 999 not found"
    assert len(tools.change_set) == 0


def test_propose_split_requires_at_least_one_new_note(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.propose_split(
        NoteId(1),
        kept_front="f",
        kept_back="b",
        kept_tags=[],
        new_notes=[],
        rationale="r",
    )

    # Then
    assert result.startswith("error:")
    assert len(tools.change_set) == 0


def test_read_note_shows_extra_fields() -> None:
    # Given
    repo = FakeNoteRepository(
        {
            1: AddonNote(
                front="Q",
                back="A",
                tags=["ml"],
                extra_fields={"Extra": "an example", "Difficulty": "2"},
            )
        }
    )
    tools = CuratorTools(repo)

    # When
    result = tools.read_note(NoteId(1))

    # Then
    assert "Extra: an example" in result
    assert "Difficulty: 2" in result
    assert result.index("Extra:") < result.index("Tags:")


def test_propose_edit_merges_extra_fields_with_stored_note() -> None:
    # Given: the stored note already has extra fields
    repo = FakeNoteRepository(
        {
            1: AddonNote(
                front="Q",
                back="A",
                extra_fields={"Extra": "old", "Difficulty": "1"},
            )
        }
    )
    tools = CuratorTools(repo)

    # When: the edit only mentions one of them
    result = tools.propose_edit(
        NoteId(1), "f", "b", [], "r", extra_fields={"Extra": "new"}
    )

    # Then
    assert result == "Edit proposal recorded for note 1."
    (edit,) = _edits(tools)
    assert edit.after.extra_fields == {"Extra": "new", "Difficulty": "1"}


def test_second_edit_replaces_first_wholesale(
    tools: CuratorTools,
) -> None:
    # Given
    tools.propose_edit(
        NoteId(1), "f", "b", [], "first", extra_fields={"Extra": "E1"}
    )

    # When: a second edit on the same note does not mention Extra
    tools.propose_edit(
        NoteId(1),
        "f",
        "b",
        [],
        "second",
        extra_fields={"Difficulty": "2"},
    )

    # Then: the newer edit replaces the older one entirely, merging
    # extra fields against the stored note (as front/back/tags do)
    (edit,) = _edits(tools)
    assert edit.after.extra_fields == {"Difficulty": "2"}


def test_propose_edit_can_clear_an_extra_field() -> None:
    # Given
    repo = FakeNoteRepository(
        {1: AddonNote(front="Q", back="A", extra_fields={"Extra": "E"})}
    )
    tools = CuratorTools(repo)

    # When
    tools.propose_edit(
        NoteId(1), "Q", "A", [], "r", extra_fields={"Extra": ""}
    )

    # Then
    (edit,) = _edits(tools)
    assert edit.after.extra_fields == {"Extra": ""}


def test_propose_edit_preserves_extra_fields_when_omitted() -> None:
    # Given
    repo = FakeNoteRepository(
        {1: AddonNote(front="Q", back="A", extra_fields={"Extra": "E"})}
    )
    tools = CuratorTools(repo)

    # When
    tools.propose_edit(NoteId(1), "new front", "A", [], "r")

    # Then
    (edit,) = _edits(tools)
    assert edit.after.extra_fields == {"Extra": "E"}


def test_propose_create_with_extra_fields(tools: CuratorTools) -> None:
    # When
    result = tools.propose_create(
        "f", "b", [], "basic", "r", extra_fields={"Extra": "E"}
    )

    # Then
    assert result == "Create proposal recorded."
    (create,) = _creates(tools)
    assert create.note.extra_fields == {"Extra": "E"}


def test_review_changeset_returns_no_changes_when_empty(
    tools: CuratorTools,
) -> None:
    # When
    result = tools.review_changeset()

    # Then
    assert result == "No changes proposed."


def test_review_changeset_renders_edits_and_creates(
    tools: CuratorTools,
) -> None:
    # Given
    tools.propose_edit(
        NoteId(1),
        front="What is beta_2 in Adam?",
        back="Decay rate of the second moment estimate.",
        tags=["ml"],
        rationale="tighter wording",
    )
    tools.propose_create(
        front="Typical value of beta_2?",
        back="0.999",
        tags=["ml"],
        notetype="basic",
        rationale="split out the value",
    )

    # When
    result = tools.review_changeset()

    # Then
    assert "What is beta_2 in Adam?" in result
    assert "Decay rate of the second moment estimate" in result
    assert "Typical value of beta_2?" in result
    assert "0.999" in result
    # Deleted notes are not shown
    tools.propose_delete(NoteId(4), "off-topic")
    result = tools.review_changeset()
    assert "capital of France" not in result
