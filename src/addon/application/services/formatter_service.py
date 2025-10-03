from __future__ import annotations

import html
import re
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Template

from ...domain.entities.note import AddonNote, AddonNoteType
from ...infrastructure.external_services.openai import OpenAIClient
from ...infrastructure.llm.schemas import AddonNoteChanges
from ...utils import is_cloze_note

if TYPE_CHECKING:
    from anki.notes import Note


def format_note_workflow(note: Note, formatter: NoteFormatter) -> Note:
    """Complete workflow for AI-powered note formatting.

    Orchestrates the conversion from Anki's Note format to our domain model,
    applies LLM-based formatting, and converts back to Anki's format.
    """
    addon_note = AnkiNoteAdapter.to_addon_note(note)
    addon_note = formatter.format(addon_note)
    # TODO: Maybe I should rename this to `apply_note_changes` and
    # pass a AddonNoteChange object to the signature
    note = AnkiNoteAdapter.merge_addon_changes(note, addon_note)
    return note


class AnkiNoteAdapter:
    """Adapter between Anki's Note object and AddonNote domain entity."""

    @staticmethod
    def to_addon_note(note: Note) -> AddonNote:
        """Convert an Anki Note to an AddonNote entity in our domain.

        Differently from Anki, we do not differentiate between Basic
        and Cloze notes. We have one AddonNote class, with a "front"
        and "back" field.

        Basic notes map:
        - "front" -> "front"
        - "back"  -> "back"

        Cloze notes map:
        - "Text" -> "front"
        - "Back Extra" to "back"
        """
        if is_cloze_note(note):
            front, back = note["Text"], note["Back Extra"]
            notetype = AddonNoteType.CLOZE
        else:
            front, back = note["Front"], note["Back"]
            notetype = AddonNoteType.BASIC
        addon_note = AddonNote(
            guid=note.guid,
            front=front,
            back=back,
            tags=note.tags,
            notetype=notetype,
        )
        return addon_note

    @staticmethod
    def merge_addon_changes(note: Note, addon_note: AddonNote) -> Note:
        if is_cloze_note(note):
            note["Text"] = addon_note.front
            note["Back Extra"] = addon_note.back
        else:
            note["Front"] = addon_note.front
            note["Back"] = addon_note.back
        # NOTE: we are intentionally not updating the tags, and keeping the
        # original ones
        return note


class NoteFormatter:
    """Application service for AI-powered note formatting and optimization.

    This service orchestrates the process of improving Anki note quality through
    large language model (LLM) assistance. It takes existing notes and applies
    consistent formatting rules, markdown standards, and content optimization
    to make them more effective for spaced repetition learning.

    The formatter handles the complete workflow of note improvement: extracting
    content from domain entities, preparing prompts with formatting guidelines,
    interfacing with the LLM for content generation, parsing structured responses,
    and reconstructing optimized notes while preserving essential elements like
    images, code blocks, and mathematical expressions.

    Key responsibilities:
    - Converting domain notes to LLM-compatible text format
    - Generating comprehensive prompts with formatting rules and examples
    - Managing LLM interactions with proper schema validation
    - Parsing and validating LLM responses for note reconstruction
    - Preserving critical content (images, code, math) during optimization

    The service uses structured output (JSON schema) to ensure reliable parsing
    of LLM responses and maintains consistency in note formatting across the
    entire collection.

    Attributes:
        _completion: OpenAI-compatible client for language model interactions.
    """

    def __init__(self, completion_client: OpenAIClient) -> None:
        self._completion = completion_client

    def format(self, note: AddonNote) -> AddonNote:
        """Apply AI-powered formatting to improve note quality.

        Converts HTML to plain text, generates an LLM prompt with formatting
        guidelines, processes the response, and returns an optimized note while
        preserving images and code blocks.
        """
        # Create a deep copy to prevent changing the original
        # object as a side effect.
        new_note = deepcopy(note)

        new_note = self._convert_br_tag_to_newline(new_note)

        note_content = f"""Front: {new_note.front}\nBack: {new_note.back}\nTags: {note.tags}\n"""
        system_msg_tmpl = get_prompt_template()
        prompt = system_msg_tmpl.render(note=note_content)

        response = self._completion.run(
            prompt=prompt,
            guided_json=AddonNoteChanges.model_json_schema(),
        )
        suggested_changes = AddonNoteChanges.model_validate_json(response)

        new_note.front = suggested_changes.front
        new_note.back = suggested_changes.back

        new_note = self._remove_alt_tags(new_note)
        return new_note

    def _convert_br_tag_to_newline(self, note: AddonNote) -> AddonNote:
        note.front = html.unescape(note.front).replace("<br>", "\n")
        note.back = html.unescape(note.back).replace("<br>", "\n")
        return note

    def _remove_alt_tags(self, note: AddonNote) -> AddonNote:
        note.front = re.sub(r'<img\s+alt="+[^"]*"+', "<img ", note.front)
        note.back = re.sub(r'<img\s+alt="+[^"]*"+', "<img ", note.back)
        return note


def get_prompt_template() -> Template:
    path = Path(__file__).parent
    fpath = path / "prompt_format_note.md"
    try:
        prompt_template_str = fpath.read_text()
    except FileNotFoundError:
        raise RuntimeError(f"Prompt template not found: {fpath}")
    return Template(prompt_template_str)


def add_html_tags(s: str) -> str:
    return html.escape(s).replace("\n", "<br>")
