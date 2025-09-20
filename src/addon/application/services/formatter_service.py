from __future__ import annotations

import html
import os
import re
from copy import deepcopy

from anki.notes import Note
from jinja2 import Template

from ...domain.entities.note import AddonNote, AddonNoteType
from ...infrastructure.external_services.openai import OpenAIClient
from ...infrastructure.llm.schemas import AddonNoteChanges
from ...utils import is_cloze_note


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
        prompt = system_msg_tmpl.render(note=note_content)

        response = self._completion.run(
            model=os.environ.get("OPENAI_MODEL"),
            prompt=prompt,
            max_tokens=200,
            temperature=0,
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


system_msg_tmpl = Template(r"""Your job is to optimize Anki notes, and particularly to make each note:
- Concise, simple, distinct
- Follow formatting rules
- Use valid Markdown syntax

You will be present with an existing note, including front, back, and tags. You must create a new note preserving its original meaning, and preserving any image, code block, and math block.

### Formatting rules

The following rules apply to both front and back of each note.

Terminal commands must follow this format:
```bash
$ command <placeholder>
```

Code snippets must follow this format:
```language
code here
```

Name of programs, utilities, and tools like nvim, systemctl, pandas, grep, etc. must follow this format:
`nvim`, `systemctl`, `pandas`, `grep`

Keyboard keys and keymaps must follow this format:
`<C-aa>`, `x`, `J`, `gg`, `<S-p>`

In code blocks, use only the following placeholders: <file>, <path>, <link>, <command>.

Represent newlines with the `<br>` tag instead of `\n`.

### Other rules

Always copy to the new note, without any modification, code blocks and images from the original note.

Wrap back of a note within double quotes.

No explanations.

Return results using this JSON schema:
{
    "title": "Note",
    "type": "object",
    "properties": {
        "front": {"type": "string"},
        "back": {"type": "string"},
        "tags": {"type": "string"},
    },
    "required": ["front", "back", "tags"]
}

### Examples

Example 1: Code block
Input: Front: What command does extract files from a zip archive?
Back: ```bash
$ unzip <file>
Tags: ['linux']
```
Output: { "front": "Extract zip files", "back": "```bash<br>$ unzip <file><br>```", "tags": ['linux'] }

Example 2: Cloze completion
Input: Front: What type of memory do GPUs come equipped with?
* \{\{c1::Dynamic RAM (HBM)\}\}
* \{\{c2::Static RAM (L1 + L2 + Registers)\}\}
Back:
Tags: ['recsys']
```
Output: { "front": "Type of memory on a GPU:<br>* \{\{c1::Dynamic RAM (HBM)\}\}<br>* \{\{c2::Static RAM (L1 + L2 + Registers)\}\}", "back": "", "tags": ['linux'] }

Example 3: Cloze completion
Input: Front:  \{\{c1::Jensen Huang\}\} is the co-founder and CEO of NVIDIA Corporation
Back:
Tags: ['recsys']
```
Output: { "front": "NVIDIA CEO: \{\{c1::Jensen Huang\}\}", "back": "", "tags": ['nvidia'] }

Example 4: Code block with placeholders
Input: Front: What command creates a soft link?
Back: ```bash
$ ln -s <file_name> <link_name>
```
Tags: ['linux']
Output: { "front": "Create soft link", "back": "```bash<br>$ ln -s <file> <link><br>```", "tags": ['linux'] }

Example 5: Code block and inline code block
Input: Front: In the `ln -s` command, what is the order of file name and link name?
Back: ```bash
$ ln -s <file_name> <link_name>
```
Tags: ['linux']
Output: { "front": "`ln -s` argument order", "back": "<file> then <link>", "tags": ['linux'] }

Example 6: Math
Input: Front: What is the range of the Leaky ReLU function?
Back: $ [ -0.01, + \infty ] $
Tags: ['dl']
Output: { "front": "Leaky ReLU range", "back": "$ [-0.01, +\infty] $", "tags": ['dl'] }

Example 7: Inline code block
Input: Front: What key returns the `^` in the shifted state?
Back: "`6`"
Tags: ['keyboard']
Output: { "front": "Keyboard key for `^` in shifted state", "back": "`6`", "tags": ['keyboard'] }


Input: {{ note }}
Output: """)


def add_html_tags(s: str) -> str:
    return html.escape(s).replace("\n", "<br>")
