Your job is to optimize Anki notes, and particularly to make each note:
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
Output: 
