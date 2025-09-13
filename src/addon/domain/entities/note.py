from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from uuid import uuid4


class AddonNoteType(str, Enum):
    """Defines abstract note formats used by the addon.

    This enum abstracts away Anki's specific note type templates (like "Basic",
    "Basic (and reversed card)", "Better Markdown : Basic", etc.) into broader
    conceptual categories. While Anki may have dozens of note type variants,
    this addon works with just two fundamental study formats:

    Attributes:
        BASIC: Traditional front/back flashcards (regardless of template)
        CLOZE: Fill-in-the-blank style cards (regardless of template)
    """

    BASIC = "basic"
    CLOZE = "cloze"


@dataclass
class AddonNote:
    """Represents a single note in the addon's domain model.

    A note contains the content and metadata for creating flashcards in Anki.
    Each note has front/back content, optional tags, and is categorized by
    its abstract note type (BASIC or CLOZE).

    For CLOZE notes: the front field contains the text with cloze deletions
    (e.g., "The capital of {{c1::France}} is {{c1::Paris}}"), while the back
    field maps to Anki's "Back Extra" field for additional context.

    Attributes:
        guid: Unique identifier for the note (auto-generated UUID)
        front: Front side content of the flashcard
        back: Back side content of the flashcard
        tags: Optional list of tags for categorization
        notetype: The abstract note type (BASIC or CLOZE)
        deck_name: Optional target deck name in Anki
    """

    front: str
    back: str
    guid: str = field(default_factory=lambda: str(uuid4()))
    tags: Optional[List[str]] = None
    notetype: AddonNoteType = AddonNoteType.BASIC
    deck_name: Optional[str] = None



class AddonCollection:
    """A collection of notes with basic management operations.

    Provides functionality to store, retrieve, and manage AddonNote instances.
    Acts as an in-memory repository for notes within the addon's domain.

    Attributes:
        name: Name identifier for this collection
        notes: Internal list storing the AddonNote instances
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.notes = []

    def add(self, notes: List[AddonNote]) -> None:
        for note in notes:
            self.notes.append(note)

    def get(self, note_guid: str) -> Optional[AddonNote]:
        # Linear search - consider indexing if collection grows large
        for note in self.notes:
            if note.guid == note_guid:
                return note

    def __iter__(self):
        return iter(self.notes)
