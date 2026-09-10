from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.entities.proposals import (
    CreateProposal,
    DeleteProposal,
    EditProposal,
)
from addon.infrastructure.ui.curation_review import (
    display_text,
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


def test_display_text_decodes_br_as_newline() -> None:
    # Given an HTML field with <br> line breaks
    # When / Then
    assert display_text("First line<br>Second line") == (
        "First line\nSecond line"
    )
    assert display_text("A<br/>B<br />C") == "A\nB\nC"


def test_display_text_decodes_entities() -> None:
    # Given a field with escaped characters and placeholders
    # When / Then
    assert display_text("jj squash -r &lt;rev&gt; &lt;path&gt;") == (
        "jj squash -r <rev> <path>"
    )
    assert display_text("&gt;&gt;&gt; grad.std()") == ">>> grad.std()"
    assert display_text("AT&amp;T") == "AT&T"


def test_display_text_strips_inline_tags_keeps_text() -> None:
    # Given a field with inline markup and a code block
    # When / Then
    assert display_text("what does the <code>print</code> function do?") == (
        "what does the print function do?"
    )
    assert (
        display_text('<pre><code>{name = "Ada"}</code></pre>')
        == '{name = "Ada"}'
    )


def test_display_text_turns_block_elements_into_lines() -> None:
    # Given a field structured with block elements
    # When / Then
    assert display_text("<div>one</div><div>two</div>") == "one\ntwo"
    assert (
        display_text("<pre><code>grad.std()<br>t.clamp(0, 1)</code></pre>")
        == "grad.std()\nt.clamp(0, 1)"
    )


def test_display_text_keeps_fenced_code_verbatim() -> None:
    # Given a markdown field whose back is a fenced command with
    # angle-bracket placeholders — the angles are code content, not
    # markup, so decoding must not strip them
    # When / Then
    assert display_text("```bash\njj squash -r <rev> <path>\n```") == (
        "```bash\njj squash -r <rev> <path>\n```"
    )


def test_display_text_normalizes_html_flavoured_code() -> None:
    # Given a fence stored Anki-style: <br> for its lines, &nbsp; for
    # its indentation, entities for its characters
    stored = (
        "```rust<br>impl Point {<br>"
        "&nbsp;&nbsp;&nbsp;&nbsp;fn x(&amp;self) -&gt; u8 { 1 }<br>"
        "}<br>```"
    )

    # When it is decoded for review
    shown = display_text(stored)

    # Then it reads as the rendered code
    assert shown == (
        "```rust\nimpl Point {\n    fn x(&self) -> u8 { 1 }\n}\n```"
    )


def test_display_text_decodes_entities_inside_fence() -> None:
    # Given a fenced command stored the Anki-safe way, with the angle
    # brackets escaped as entities
    stored = "```bash\njj squash -r &lt;rev&gt; &lt;path&gt;\n```"

    # When it is decoded for review
    shown = display_text(stored)

    # Then the placeholders read as characters, not entity symbols
    assert shown == "```bash\njj squash -r <rev> <path>\n```"


def test_display_text_keeps_angles_inside_fence_and_code_span() -> None:
    # Given a fenced Rust block with generics and an inline code span
    # holding comparison operators
    text = (
        "```rust\nlet v: Vec<i32> = vec![1, 2];\n"
        'if a < b && c > d {\n    println!("big");\n}\n```\n'
        "what does `a < b` mean?"
    )

    # When it is decoded
    shown = display_text(text)

    # Then the code keeps its angle brackets and ampersands verbatim
    assert "Vec<i32>" in shown
    assert "a < b && c > d" in shown
    assert "`a < b`" in shown


def test_edit_diff_shows_br_as_line_breaks() -> None:
    # Given an edit that adds a line to a <br>-separated back
    before = AddonNote(
        front="Q", back="<pre><code>grad.std()</code></pre>", tags=[]
    )
    after = AddonNote(
        front="Q",
        back="<pre><code>grad.std()<br>t.clamp(0, 1)</code></pre>",
        tags=[],
    )
    proposal = EditProposal(NoteId(1), before, after, "r")

    # When
    detail = proposal_detail(proposal)

    # Then the diff lines are the decoded code, not the raw <pre>/<br>
    # symbols
    assert "<br>" not in detail
    assert "<pre>" not in detail
    assert " grad.std()" in detail  # unchanged context line
    assert "+t.clamp(0, 1)" in detail


def test_edit_diff_decodes_placeholders() -> None:
    # Given an edit whose back gains an escaped placeholder
    before = AddonNote(front="Q", back="lua game.lua", tags=[])
    after = AddonNote(
        front="Q",
        back="jj squash -r &lt;rev&gt; &lt;path&gt;",
        tags=[],
    )
    proposal = EditProposal(NoteId(1), before, after, "r")

    # When
    detail = proposal_detail(proposal)

    # Then the diff shows the placeholder as angle brackets, not as
    # the entity symbol soup
    assert "&lt;rev&gt;" not in detail
    assert "+jj squash -r <rev> <path>" in detail
