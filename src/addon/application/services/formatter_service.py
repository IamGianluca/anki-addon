import html
import os
import re
from copy import deepcopy

from anki.notes import Note
from jinja2 import Template

from ...domain.entities.note import AddonNote, AddonNoteChanges, AddonNoteType
from ...infrastructure.external_services.openai import OpenAIClient
from ...utils import is_cloze_note


class NoteFormatter:
    def __init__(self, llm_client: OpenAIClient) -> None:
        self._completion = llm_client

    def format(self, note: AddonNote) -> AddonNote:
        def _format_note_content(note):
            return f"""Front: {remove_html_tags(note.front)}\nBack: {remove_html_tags(note.back)}\nTags: {note.tags}\n"""

        def _create_system_msg(note):
            return system_msg_tmpl.render(note=note)

        note_content = _format_note_content(note)
        prompt = _create_system_msg(note=note_content)

        schema = AddonNoteChanges.model_json_schema()
        response = self._completion.run(
            model=os.environ.get("OPENAI_MODEL"),
            prompt=prompt,
            max_tokens=200,
            temperature=0,
            guided_json=schema,
        )

        suggested_changes = AddonNoteChanges.model_validate_json(response)

        new_note = deepcopy(note)
        new_note.front = suggested_changes.front
        new_note.back = suggested_changes.back
        return new_note


def format_note_workflow(note: Note, formatter: NoteFormatter) -> Note:
    addon_note = convert_note_to_addon_note(note)
    addon_note = _format_note(addon_note, formatter)
    addon_note = _remove_alt_tags(addon_note)
    note = update_note(note, addon_note)
    return note


def convert_note_to_addon_note(note: Note) -> AddonNote:
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


def update_note(note: Note, addon_note: AddonNote) -> Note:
    if is_cloze_note(note):
        note["Text"] = addon_note.front
        note["Back Extra"] = addon_note.back
    else:
        note["Front"] = addon_note.front
        note["Back"] = addon_note.back
    # NOTE: we are intentionally not updating the tags, and keeping the
    # original ones
    return note


def _format_note(note: AddonNote, formatter: NoteFormatter) -> AddonNote:
    new_note = formatter.format(note)
    return new_note


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


def _remove_alt_tags(note: AddonNote) -> AddonNote:
    note.front = re.sub(r'<img\s+alt="+[^"]*"+', "<img ", note.front)
    note.back = re.sub(r'<img\s+alt="+[^"]*"+', "<img ", note.back)
    return note


def add_html_tags(s: str) -> str:
    return html.escape(s).replace("\n", "<br>")


def remove_html_tags(s: str) -> str:
    return html.unescape(s).replace("<br>", "\n")
