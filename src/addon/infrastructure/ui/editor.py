from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...application.use_cases.note_counter import is_note_marked_for_review

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.notes import Note


class EditorDialog:
    """UI state manager for batch note editing sessions within Anki.

    This class orchestrates the editing workflow for notes that have been flagged
    for review (typically with an orange flag). It provides navigation between notes,
    tracks editing state, and enables rollback of changes to preserve data integrity
    during the editing process.

    The dialog manages the complete editing session lifecycle: discovering notes
    that need review, maintaining current position in the editing sequence,
    backing up original content before modifications, and providing restoration
    capabilities if users want to undo changes.

    Key responsibilities:
    - Filtering notes in the current deck that are marked for review
    - Managing navigation state through the collection of notes to edit
    - Preserving original note content for backup/restore operations
    - Handling Anki card flags to mark completion of editing tasks
    - Providing safe note persistence that maintains editing flags

    Attributes:
        col: Reference to Anki's collection for note and card operations.
        review_notes: List of all notes that need to be reviewed/edited.
        _current_index: Private tracker of which note is currently being edited (internal).
        _original_fields: Private backup of original field content for current note (internal).

    Raises:
        ValueError: When no notes are found that are marked for review
    """

    def __init__(self, collection: Collection) -> None:
        """Initialize the editor dialog with an Anki collection.

        Args:
            collection: Anki's collection object for database operations.

        Raises:
            ValueError: When no notes are found that are marked for review.
        """
        self.col = collection
        self.review_notes = self._get_all_notes_to_review()
        self._current_index = 0
        self._original_fields = {}

        if not self.review_notes:
            raise ValueError("No notes marked for review")

    def __len__(self) -> int:
        return len(self.review_notes)

    def _get_all_notes_to_review(self) -> list[Note]:
        """Retrieve all notes marked for review."""
        deck_id = self.col.decks.current()["id"]
        query = f"did:{deck_id}"
        note_ids = self.col.find_notes(query)

        review_notes = []
        for note_id in note_ids:
            if is_note_marked_for_review(self.col, note_id):
                review_notes.append(self.col.get_note(note_id))

        return review_notes

    def get_note_fields_with_tags(self, note: Note) -> dict[str, str]:
        """Extract all fields and tags from note.

        Tags stored as __tags__ to avoid conflicts with user-defined field names
        (Anki note types can have arbitrary field names including "Tags").
        """
        fields = {field_name: note[field_name] for field_name in note.keys()}
        fields["__tags__"] = " ".join(note.tags)
        return fields

    def current_note(self) -> Note:
        note = self.review_notes[self._current_index]
        # Store fields and content for possible backup needs
        self._original_fields = self.get_note_fields_with_tags(note)
        return note

    def backup_current_note(self) -> Note:
        note = self.review_notes[self._current_index]
        for field_name, original_content in self._original_fields.items():
            if field_name == "__tags__":
                # Tags are not a field, restore them separately
                note.tags = (
                    original_content.split() if original_content else []
                )
            else:
                note[field_name] = original_content
        return note

    def restore_current_note(self) -> None:
        reloaded_note = self.backup_current_note()
        reloaded_note.flush()

    def has_next_note(self) -> bool:
        return self._current_index < len(self.review_notes) - 1

    def move_to_next_note(self) -> Optional[Note]:
        if self.has_next_note():
            self._current_index += 1
            # NOTE: It's important to execute the `current_note()` method
            # because it also updates the backup for the current note
            current_note = self.current_note()
            return current_note
        return None

    def strip_orange_flag(self, current_note: Note) -> Note:
        card_ids = self.col.find_cards(f"nid:{current_note.id}")
        for card_id in card_ids:
            card = self.col.get_card(card_id)
            if card.flags == 2:
                card.flags = 0
                card.flush()
        return current_note

    def save_note_keep_flag(self, current_note: Note) -> Note:
        """Save note without removing the orange flag."""
        # Just flush the note, keeping flags intact
        current_note.flush()
        return current_note
