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

If the front does not already include domain context, use the tags to infer the domain and prefix the question with "In <domain>, ...".

No explanations.

### Examples

Example 1: Code block
Input: Front: What command does extract files from a zip archive?
Back: ```bash
$ unzip <file>
```
Tags: ['linux']
Output: Front: In Linux, what command extracts files from a zip archive?
Back: ```bash<br>$ unzip <file><br>```

Example 2: Cloze completion
Input: Front: What type of memory do GPUs come equipped with?
* \{\{c1::Dynamic RAM (HBM)\}\}
* \{\{c2::Static RAM (L1 + L2 + Registers)\}\}
Back:
Tags: ['ml']
Output: Front: In ML, what types of memory does a GPU have?<br>* \{\{c1::Dynamic RAM (HBM)\}\}<br>* \{\{c2::Static RAM (L1 + L2 + Registers)\}\}
Back:

Example 3: Cloze completion
Input: Front: \{\{c1::Dropout\}\} is a regularization technique that randomly sets a fraction of input units to 0 at each update during training time
Back:
Tags: ['dl']
Output: Front: In deep learning, \{\{c1::dropout\}\} is a regularization technique that randomly deactivates neurons during training
Back:

Example 4: Code block with placeholders
Input: Front: What command creates a soft link?
Back: ```bash
$ ln -s <file_name> <link_name>
```
Tags: ['linux']
Output: Front: In Linux, what command creates a soft link?
Back: ```bash<br>$ ln -s <file> <link><br>```

Example 5: Code block and inline code block
Input: Front: In the `ln -s` command, what is the order of file name and link name?
Back: ```bash
$ ln -s <file_name> <link_name>
```
Tags: ['linux']
Output: Front: In Linux, in `ln -s`, what is the argument order?
Back: <file> then <link>

Example 6: Math
Input: Front: What is the range of the Leaky ReLU function?
Back: $ [ -0.01, + \infty ] $
Tags: ['dl']
Output: Front: In deep learning, what is the range of the Leaky ReLU function?
Back: $ [-0.01, +\infty] $

Example 7: Inline code block
Input: Front: What key returns the `^` in the shifted state?
Back: "`6`"
Tags: ['keyboard']
Output: Front: On the keyboard, which key produces `^` in shifted state?
Back: `6`

Example 8: Domain context already present
Input: Front: In Python, what does the enumerate() function return?
Back: Tuples of (index, value) for each element in the iterable
Tags: ['python']
Output: Front: In Python, what does the `enumerate()` function return?
Back: Tuples of (index, value) for each element in the iterable


Input: {{ note }}
Output: 
