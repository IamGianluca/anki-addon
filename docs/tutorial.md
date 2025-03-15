# Understanding the AnkiConnect Python Client (aqt)

The `aqt` package is Anki's Python client library, which allows you to interact with and extend Anki programmatically. Here's a concise guide to its main components:

## Core Components

1. **`mw` (Main Window)**: The central object that provides access to the Anki application state
   ```python
   from aqt import mw
   ```

2. **Collection (`col`)**: Access to your cards, notes, decks and models
   ```python
   collection = mw.col
   ```

3. **Editor**: The interface for editing notes
   ```python
   from aqt.editor import Editor
   ```

4. **Reviewer**: Controls the card review process
   ```python
   from aqt.reviewer import Reviewer
   ```

5. **Browser**: For searching and managing cards
   ```python
   from aqt.browser import Browser
   ```

## Common Operations

### Working with Notes and Cards
```python
# Get all note IDs from a deck
deck_name = "MyDeck"
query = f"deck:{deck_name}"
note_ids = mw.col.find_notes(query)

# Get note data
note = mw.col.get_note(note_ids[0])
print(note.fields)  # Access fields
```

### Creating New Cards
```python
# Create a new note
model = mw.col.models.by_name("Basic")
note = mw.col.new_note(model)
note.fields[0] = "Front text"
note.fields[1] = "Back text"
mw.col.add_note(note, mw.col.decks.id("MyDeck"))
```

### Modifying the UI
```python
from aqt.utils import showInfo
from aqt.qt import QAction, qconnect

# Add a menu item
action = QAction("My Add-on Action", mw)
qconnect(action.triggered, lambda: showInfo("Hello from my add-on!"))
mw.form.menuTools.addAction(action)
```

## Add-on Development Pattern
```python
from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *

def my_function():
    # Your add-on functionality here
    showInfo("Add-on was triggered!")

# Create a menu action
action = QAction("My Add-on", mw)
qconnect(action.triggered, my_function)
mw.form.menuTools.addAction(action)
```

Remember that Anki operations should be performed within Anki's thread and UI modifications should respect Qt's event loop. The `aqt` library works closely with `anki`, which handles the core functionality, while `aqt` focuses on the UI components.
