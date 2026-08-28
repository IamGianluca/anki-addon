"""Unit tests for the standing formatting-rule checker.

LLM-free, like test_graders: proposals are constructed in code and
checked directly. Runs in make test_slow.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

from tests.evals.formatting import (
    FormattingViolation,
    WrittenField,
    check_formatting,
    written_fields,
    written_fields_from_record,
)

from addon.domain.entities.note import AddonNote
from addon.domain.entities.proposals import CreateProposal, EditProposal


def _edit(
    before_back: str,
    after_back: str,
    before_extra: dict[str, str] | None = None,
    after_extra: dict[str, str] | None = None,
) -> EditProposal:
    before = AddonNote(
        front="Q?", back=before_back, extra_fields=before_extra or {}
    )
    after = AddonNote(
        front="In math, what is Q?",
        back=after_back,
        extra_fields=after_extra or {},
    )
    return EditProposal(note_id=1, before=before, after=after, rationale="r")


def _create(back: str, extra: dict[str, str] | None = None) -> CreateProposal:
    note = AddonNote(front="Q?", back=back, extra_fields=extra or {})
    return CreateProposal(note, "r")


def _rules_of(violations: list[FormattingViolation]) -> list[str]:
    return [v.rule for v in violations]


def test_created_note_ending_with_period_is_flagged():
    # Given a created note whose back ends with a full stop
    proposal = _create("The mitochondria produce ATP.")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then a no_trailing_period violation is recorded against the back
    assert len(violations) == 1
    violation = violations[0]
    assert violation.rule == "no_trailing_period"
    assert violation.field == "back"
    assert violation.note_id is None
    assert "ATP." in violation.snippet


def test_created_note_without_trailing_period_passes():
    # Given a created note whose back ends with a word
    # When it is checked
    violations = check_formatting(
        written_fields([_create("The mitochondria produce ATP")])
    )

    # Then no violation is recorded
    assert violations == []


def test_edited_note_that_adds_a_trailing_period_is_flagged():
    # Given an edit that changes the back and ends it with a full stop
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("The answer", "The answer.")])
    )

    # Then the violation carries the edited note's id
    assert _rules_of(violations) == ["no_trailing_period"]
    assert violations[0].note_id == 1


def test_edited_note_that_leaves_a_dirty_back_untouched_is_flagged():
    # Given an edit that only changes the front, while the back keeps
    # its pre-existing full stop
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("The answer.", "The answer.")])
    )

    # Then the violation is recorded — the agent edited the note, so
    # the final card is its responsibility
    assert _rules_of(violations) == ["no_trailing_period"]
    assert violations[0].note_id == 1


def test_edited_note_that_removes_the_period_passes():
    # Given an edit that rewrites the back without the trailing stop
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("The answer.", "The answer")])
    )

    # Then no violation is recorded
    assert violations == []


def test_trailing_period_in_extra_field_is_flagged():
    # Given an edit that writes an Extra field ending with a full stop
    # When it is checked
    violations = check_formatting(
        written_fields(
            [
                _edit(
                    "A",
                    "A",
                    before_extra={"Extra": "Context"},
                    after_extra={"Extra": "Context."},
                )
            ]
        )
    )

    # Then the violation names the Extra field
    assert len(violations) == 1
    assert violations[0].field == "Extra"


def test_untouched_extra_field_with_trailing_stop_is_flagged():
    # Given an edit that preserves an Extra field ending with a full stop
    # When it is checked
    violations = check_formatting(
        written_fields(
            [
                _edit(
                    "A",
                    "A",
                    before_extra={"Extra": "Context."},
                    after_extra={"Extra": "Context."},
                )
            ]
        )
    )

    # Then the violation is recorded — the final Extra text still
    # ends with a stop
    assert _rules_of(violations) == ["no_trailing_period"]
    assert violations[0].field == "Extra"


def test_wrapping_a_dirty_back_in_html_is_still_flagged():
    # Given an edit that only wraps the back in HTML, changing nothing visible
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("The answer.", "<div>The answer.</div>")])
    )

    # Then the violation is recorded — the final text still ends with
    # a stop, and the agent edited the note
    assert _rules_of(violations) == ["no_trailing_period"]


def test_html_tags_and_entities_are_stripped_before_checking():
    # Given a back whose trailing period is hidden behind markup and an entity
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("A", "<div>The answer.&nbsp;</div>")])
    )

    # Then the plain text still ends with a full stop and is flagged
    assert _rules_of(violations) == ["no_trailing_period"]


def test_plain_rewrite_keeping_the_period_is_flagged():
    # Given an edit that rewrites the wording but keeps the trailing stop
    # When it is checked
    violations = check_formatting(
        written_fields([_edit("It relies on the ETC.", "It uses the ETC.")])
    )

    # Then the violation is recorded — the agent wrote this ending
    assert _rules_of(violations) == ["no_trailing_period"]


def test_naive_check_flags_abbreviation_endings():
    # Given a back whose final token is an abbreviation with its own period
    # When it is checked
    violations = check_formatting(written_fields([_create("Uses the ETC.")]))

    # Then it is flagged — the checker is deliberately naive; the
    # edge-case tasks pin down the rule's precise semantics
    assert _rules_of(violations) == ["no_trailing_period"]


def test_written_fields_from_record_parses_persisted_change_sets():
    # Given a trial record with an edit and a create in its change set
    record = {
        "change_set": [
            {
                "type": "edit",
                "note_id": 7,
                "before": {"back": "old.", "extra_fields": {"Extra": "x"}},
                "after": {"back": "new", "extra_fields": {"Extra": "y."}},
            },
            {
                "type": "create",
                "note": {"back": "created.", "extra_fields": {"Extra": "z"}},
            },
        ]
    }

    # When the record's written fields are extracted and checked
    violations = check_formatting(written_fields_from_record(record))

    # Then both period endings are caught, with the edit's note id
    assert _rules_of(violations) == [
        "no_trailing_period",
        "no_trailing_period",
    ]
    assert [v.note_id for v in violations] == [7, None]
    assert [v.field for v in violations] == ["Extra", "back"]


def test_written_fields_preserve_extra_field_names():
    # Given an edit that keeps one extra field and rewrites another
    # When its written fields are extracted and checked
    fields = written_fields(
        [
            _edit(
                "A",
                "A",
                before_extra={"Extra": "kept", "Difficulty": "hard"},
                after_extra={"Extra": "kept", "Difficulty": "harder"},
            )
        ]
    )

    # Then every final field is listed under its own name
    assert [(f.field, f.after) for f in fields] == [
        ("back", "A"),
        ("Difficulty", "harder"),
        ("Extra", "kept"),
    ]
    assert check_formatting(fields) == []


def test_empty_change_set_has_no_violations():
    # Given an empty change set
    # When it is checked
    violations = check_formatting(written_fields([]))

    # Then there is nothing to flag
    assert violations == []


def test_written_field_is_frozen():
    # Given a WrittenField instance
    field = WrittenField(note_id=1, field="back", after="b")

    # Then it is immutable — value objects have no identity
    try:
        field.after = "c"
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("WrittenField should be immutable")
