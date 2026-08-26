"""Unit tests for the deterministic outcome graders.

LLM-free, like test_task_files: tasks are constructed in code and
without a judge, so no model calls are made. Includes the transcript
rule checks (read-before-propose), which are pure string/int logic.
Runs in make test_slow.
"""

import json

from tests.evals.graders import GradeResult, grade_outcome, grade_transcript
from tests.evals.harness import EvalTask, Expectation, TaskNote

from addon.application.services.curator_agent import CurationSession
from addon.domain.entities.note import AddonNote
from addon.domain.entities.proposals import (
    EditProposal,
    ProposedChangeSet,
)


def _grade_facts(backs: list[str], facts: list[str]) -> GradeResult:
    """Grade a seeded cluster as-is (no proposals) for the given facts."""
    task = EvalTask(
        id="fact_boundaries",
        desc="fact matching semantics",
        seed_note_id=1,
        notes=[
            TaskNote(id=i + 1, front=f"Q{i + 1}?", back=back)
            for i, back in enumerate(backs)
        ],
        expect=Expectation(facts=facts),
    )
    return grade_outcome(task, [])


def _verdict(result: GradeResult, fact: str) -> str:
    return next(c for c in result.checks if c.name == f"fact_{fact}").verdict


def test_fact_does_not_match_inside_a_longer_number():
    # Given a cluster whose only value is the overlapping "0.999"
    # When it is graded for the fact "0.9"
    result = _grade_facts(["0.999."], ["0.9"])

    # Then the fact is reported missing — plain substring matching
    # used to pass this vacuously ("0.9" is a substring of "0.999")
    assert _verdict(result, "0.9") == "fail"


def test_fact_matches_as_a_standalone_token():
    # Given a note carrying the value as its own token
    # When it is graded for that value
    result = _grade_facts(["0.9."], ["0.9"])

    # Then the check passes
    assert _verdict(result, "0.9") == "pass"


def test_overlapping_facts_are_checked_independently():
    # Given a cluster carrying both overlapping values (the
    # split_compound reference outcome)
    # When it is graded for both facts
    result = _grade_facts(["0.9.", "0.999."], ["0.9", "0.999"])

    # Then both pass — the boundary rule must not overcorrect
    assert _verdict(result, "0.9") == "pass"
    assert _verdict(result, "0.999") == "pass"


def test_fact_does_not_match_inside_a_longer_word():
    # Given a note that mentions "length" but never the len() fact
    # When it is graded for the fact "len"
    result = _grade_facts(["Returns the length of an object."], ["len"])

    # Then the fact is reported missing
    assert _verdict(result, "len") == "fail"


def test_fact_matches_across_punctuation():
    # Given a note carrying the term glued to punctuation
    # When it is graded for the bare term
    result = _grade_facts(
        ["len() returns the number of items in an object."], ["len"]
    )

    # Then the check passes — boundaries are word characters, not spaces
    assert _verdict(result, "len") == "pass"


def _grade_banned(proposals: list, banned: list[str]) -> GradeResult:
    """Grade a change set against must_not_contain words."""
    task = EvalTask(
        id="banned_words",
        desc="must-not-contain semantics",
        seed_note_id=1,
        notes=[TaskNote(id=1, front="Q?", back="A")],
        expect=Expectation(must_not_contain=banned),
    )
    return grade_outcome(task, proposals)


def _edit_proposal(front: str, back: str) -> EditProposal:
    before = AddonNote(front="Q?", back="A")
    after = AddonNote(front=front, back=back)
    return EditProposal(note_id=1, before=before, after=after, rationale="r")


def _verdict_banned(result: GradeResult, word: str) -> str:
    return next(
        c for c in result.checks if c.name == f"must_not_contain_{word}"
    ).verdict


def test_banned_word_in_proposed_note_fails():
    # Given a proposal that uses the banned word "you"
    proposals = [_edit_proposal("How do you find the maximum?", "A")]

    # When it is graded against the ban
    result = _grade_banned(proposals, ["you", "i", "we"])

    # Then the "you" check fails while the others pass
    assert _verdict_banned(result, "you") == "fail"
    assert _verdict_banned(result, "i") == "pass"
    assert _verdict_banned(result, "we") == "pass"


def test_banned_word_in_unchanged_note_is_ignored():
    # Given a proposal whose text is clean, while a pre-existing note
    # (not part of any proposal) contains the banned word
    proposals = [_edit_proposal("How is the maximum found?", "A")]

    # When it is graded against the ban
    result = _grade_banned(proposals, ["you"])

    # Then the ban passes — the agent is not responsible for
    # pre-existing note content
    assert _verdict_banned(result, "you") == "pass"


def _grade_transcript(
    actions: list[dict],
    seed_note_id: int = 1,
) -> GradeResult:
    """Grade an agent transcript built from the given raw action
    payloads (each wrapped with a thought, as the agent emits)."""
    task = EvalTask(
        id="read_rule",
        desc="read-before-propose rule",
        seed_note_id=seed_note_id,
        notes=[TaskNote(id=1, front="Q", back="A")],
        expect=Expectation(finish=True),
    )
    transcript = [
        {
            "role": "assistant",
            "content": json.dumps({"thought": "t", "action": action}),
        }
        for action in actions
    ]
    session = CurationSession(
        change_set=ProposedChangeSet(),
        transcript=transcript,
        summary="done",
    )
    return grade_transcript(task, session)


def test_editing_a_collection_note_without_reading_it_fails():
    # When the agent edits a note it never read
    result = _grade_transcript([{"action": "propose_edit", "note_id": 5}])

    # Then a read-before-edit violation is recorded
    assert not result.passed
    assert any(c.name == "read_before_propose_edit_5" for c in result.checks)


def test_editing_a_note_after_reading_it_passes():
    # Given the agent reads note 5 first
    # When it then edits the note
    result = _grade_transcript(
        [
            {"action": "read_note", "note_id": 5},
            {"action": "propose_edit", "note_id": 5},
        ]
    )

    # Then no read-before violation is recorded
    assert result.passed


def test_editing_a_self_created_note_without_reading_it_passes():
    # When the agent edits a provisional id (a note it created itself)
    result = _grade_transcript([{"action": "propose_edit", "note_id": -2}])

    # Then no read-before violation is recorded — the agent authored
    # the pending note, so re-reading it would be ceremony
    assert result.passed


def test_seed_note_is_exempt_from_read_before_edit():
    # When the agent edits the seed note without reading it
    result = _grade_transcript([{"action": "propose_edit", "note_id": 1}])

    # Then no read-before violation is recorded — the seed's content
    # is already in the first user message
    assert result.passed
