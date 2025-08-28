from typing import Optional

from anki.collection import Collection
from anki.notes import Note

from ...application.use_cases.note_counter import is_note_marked_for_review


class EditorDialog:
    """The EditorDialog class manages the state of editing sessions:

    - It retrieves all notes from the current deck that are marked for review
    - It keeps track of which note is currently being edited
    - It provides methods to navigate between notes, backup original content,
      and restore notes to their original state
    """

    def __init__(self, collection: Collection) -> None:
        self.col = collection
        self.review_notes = self._get_all_notes_to_review()
        self.__current_index = 0
        self.__original_fields = {}

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
            if is_note_marked_for_review(note_id):
                review_notes.append(self.col.get_note(note_id))

        return review_notes

    def current_note(self) -> Note:
        note = self.review_notes[self.__current_index]

        # Store fields and content for possible backup needs
        self.__original_fields = {}
        for field_name in note.keys():
            self.__original_fields[field_name] = note[field_name]

        return note

    def backup_current_note(self) -> Note:
        note = self.review_notes[self.__current_index]
        for field_name, original_content in self.__original_fields.items():
            note[field_name] = original_content
        return note

    def restore_current_note(self) -> None:
        reloaded_note = self.backup_current_note()
        reloaded_note.flush()

    def has_next_note(self) -> bool:
        return self.__current_index < len(self.review_notes) - 1

    def move_to_next_note(self) -> Optional[Note]:
        if self.has_next_note():
            self.__current_index += 1
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
