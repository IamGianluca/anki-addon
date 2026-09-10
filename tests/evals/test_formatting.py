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


def test_written_fields_cover_the_front_field():
    # Given a created note
    proposal = _create("The answer")

    # When its written fields are extracted
    fields = written_fields([proposal])

    # Then the front is among them — the agent is responsible for
    # every field it writes, not just the back
    assert [(f.field, f.after) for f in fields] == [
        ("front", "Q?"),
        ("back", "The answer"),
    ]


def test_literal_newline_in_field_is_flagged():
    # Given a created note whose back uses a raw newline instead of <br>
    proposal = _create("First line\nSecond line")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then a raw_newline violation is recorded — a raw \n collapses
    # to a space when Anki renders the card
    assert _rules_of(violations) == ["raw_newline"]
    assert violations[0].field == "back"


def test_br_line_break_passes():
    # Given a created note whose lines are separated the HTML way
    # When it is checked
    violations = check_formatting(
        written_fields([_create("First line<br>Second line")])
    )

    # Then no violation is recorded
    assert violations == []


def test_paragraph_break_stored_as_two_brs_passes():
    # Given a created note whose paragraphs are separated the HTML way
    proposal = _create("First paragraph<br><br>Second paragraph")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


def test_blank_line_in_prose_is_flagged():
    # Given a created note whose prose is split by a raw blank line
    proposal = _create("First paragraph\n\nSecond paragraph")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then the raw newline is flagged — the editor collapses it and
    # the paragraph structure is lost from the stored field
    assert _rules_of(violations) == ["raw_newline"]


def test_raw_run_of_spaces_in_prose_is_flagged():
    # Given a created note whose prose aligns text with raw spaces
    proposal = _create("before   after")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then a raw_spaces violation is recorded — HTML collapses the run
    assert _rules_of(violations) == ["raw_spaces"]


def test_nbsp_run_in_prose_passes():
    # Given a created note whose extra spaces are non-breaking
    proposal = _create("before&nbsp;&nbsp;&nbsp;after")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


def test_tab_is_flagged_as_raw_spaces():
    # Given a created note that indents with a tab
    proposal = _create("line one<br>&nbsp;&nbsp;&nbsp;&nbsp;indented")
    tabbed = WrittenField(note_id=None, field="back", after="a\tb")

    # When both are checked
    clean = check_formatting(written_fields([proposal]))
    violations = check_formatting([tabbed])

    # Then the nbsp indentation passes while the tab is flagged
    assert clean == []
    assert _rules_of(violations) == ["raw_spaces"]


def test_raw_newline_in_front_is_flagged():
    # Given an edit whose front keeps a literal newline
    # When it is checked
    violations = check_formatting(
        [
            WrittenField(
                note_id=1, field="front", after="In math, what is Q?\nA"
            )
        ]
    )

    # Then the violation names the front field
    assert _rules_of(violations) == ["raw_newline"]
    assert violations[0].field == "front"


def test_unescaped_angle_bracket_is_flagged():
    # Given a created note whose prose carries a raw <rev> placeholder
    proposal = _create("jj squash -r <rev> <path>")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then an unescaped_html violation is recorded — markdown passes
    # raw HTML through, so the browser swallows <rev> as a broken tag
    assert _rules_of(violations) == ["unescaped_html"]
    assert "<rev>" in violations[0].snippet


def test_raw_placeholders_inside_fence_are_flagged():
    # Given a created note whose fenced code block holds a raw <rev>
    # placeholder — Anki parses it as an HTML tag before the markdown
    # renderer runs, so the placeholder and the text it swallows
    # disappear from the card (and a stray closing tag lands after
    # the fence)
    proposal = _create("```bash<br>jj squash -r <rev> <path><br>```")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then an unescaped_html violation is recorded, code included
    assert _rules_of(violations) == ["unescaped_html"]


def test_escaped_placeholders_inside_fence_pass():
    # Given a created note whose fenced code block stores the
    # placeholders as entities and its lines as <br> — the addon
    # decodes both before it parses the markdown, so the code renders
    # as the command and the field survives Anki's HTML layer
    proposal = _create(
        "```bash<br>jj squash -r &lt;rev&gt; &lt;path&gt;<br>```"
    )

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


def test_raw_newline_inside_fence_is_flagged():
    # Given a created note whose fenced code block uses literal
    # newlines for its lines — the editor collapses them, so the
    # stored block no longer reads as code
    proposal = _create("```bash\njj squash -r list\n```")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then the literal newlines are flagged
    assert _rules_of(violations) == ["raw_newline"]


def test_raw_indentation_inside_fence_is_flagged():
    # Given a created note whose fenced code indents with raw spaces
    proposal = _create("```rust<br>impl Point {<br>    fn x() {}<br>}<br>```")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then the raw indentation is flagged
    assert _rules_of(violations) == ["raw_spaces"]


def test_raw_angles_inside_inline_code_are_flagged():
    # Given a created note whose inline code span holds raw comparison
    # operators
    proposal = _create("what does `a < b && c > d` mean?")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then the raw characters are flagged even inside the span
    assert _rules_of(violations) == ["unescaped_html"]


def test_escaped_angles_inside_inline_code_pass():
    # Given a created note whose inline code span stores the operators
    # as entities
    proposal = _create("what does `a &lt; b &amp;&amp; c &gt; d` mean?")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


def test_math_keeps_multiline_display_with_escaped_ampersands():
    # Given a created note whose back holds \\(...\\)/\\[...\\] math —
    # multi-line display blocks keep literal newlines, and LaTeX's &
    # (matrix columns) is stored escaped like everywhere else; the
    # addon decodes it inside math before KaTeX sees it
    proposal = _create(
        r"the diagonal is \(\begin{matrix} a &amp; b \\ "
        r"c &amp; d \end{matrix}\)<br><br>"
        r"\[<br>\frac{d}{dx} x^2 = 2x<br>\]"
    )

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


def test_raw_ampersand_in_math_is_flagged():
    # Given a created note whose math holds a raw matrix ampersand
    proposal = _create(r"\(\begin{matrix} a & b \\ c & d \end{matrix}\)")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then the raw ampersand is flagged
    assert _rules_of(violations) == ["unescaped_html"]


def test_escaped_placeholders_pass():
    # Given a created note that escapes its placeholders
    # When it is checked
    violations = check_formatting(
        written_fields([_create("jj squash -r &lt;rev&gt; &lt;path&gt;")])
    )

    # Then no violation is recorded
    assert violations == []


def test_bare_ampersand_is_flagged():
    # Given a created note whose text uses a raw & outside an entity
    proposal = _create("AT&T and AT&amp;T")

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then only the bare ampersand is flagged, once per field
    assert _rules_of(violations) == ["unescaped_html"]


def test_raw_ampersand_inside_fence_is_flagged():
    # Given a created note whose fenced code holds a raw &&
    # When it is checked
    violations = check_formatting(
        written_fields([_create("```bash<br>echo a && echo b<br>```")])
    )

    # Then the raw ampersand is flagged
    assert _rules_of(violations) == ["unescaped_html"]


def test_escaped_prompt_markers_inside_fence_pass():
    # Given a created note that stores a >>> marker inside a fenced
    # Python block as entities — the addon decodes them before parsing
    # When it is checked
    violations = check_formatting(
        written_fields(
            [
                _create(
                    "```python<br>&gt;&gt;&gt; grad.std() / param.std()<br>```"
                )
            ]
        )
    )

    # Then no violation is recorded
    assert violations == []


def test_raw_prompt_markers_inside_fence_are_flagged():
    # Given a created note that stores a >>> marker raw inside a fence
    # When it is checked
    violations = check_formatting(
        written_fields(
            [_create("```python<br>>>> grad.std() / param.std()<br>```")]
        )
    )

    # Then the raw > is flagged like any other unescaped character
    assert _rules_of(violations) == ["unescaped_html"]


def test_escaped_prompt_markers_pass():
    # Given a created note that stores a >>> marker as its entities
    # When it is checked
    violations = check_formatting(
        written_fields([_create("&gt;&gt;&gt; grad.std() / param.std()")])
    )

    # Then no violation is recorded
    assert violations == []


def test_anki_html_markup_passes():
    # Given a created note written with the tags and entities Anki
    # fields legitimately carry, including a language class on <code>
    proposal = _create(
        '<pre><code class="language-rust">let a = 1;<br>'
        "fn main() {}</code></pre>"
    )

    # When it is checked
    violations = check_formatting(written_fields([proposal]))

    # Then no violation is recorded
    assert violations == []


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
        ("front", "In math, what is Q?"),
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
