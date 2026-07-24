"""In-memory fake of the NoteRepository port for unit tests."""

from __future__ import annotations

from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.repositories.note_repository import (
    NoteNotFoundError,
    NoteRepository,
)


class FakeNoteRepository(NoteRepository):
    """Dict-backed NoteRepository fake.

    Search does case-insensitive substring matching over front, back and
    tags (all terms must appear) — a predictable stand-in for Anki's
    search grammar.
    """

    def __init__(self, notes: dict[int, AddonNote] | None = None) -> None:
        self._notes: dict[int, AddonNote] = dict(notes or {})
        self._next_id = max(self._notes, default=0) + 1

    def search(self, query: str, limit: int = 10) -> list[NoteId]:
        terms = query.lower().split()
        matches = [
            NoteId(note_id)
            for note_id, note in self._notes.items()
            if all(term in _haystack(note) for term in terms)
        ]
        return matches[:limit]

    def get(self, note_id: NoteId) -> AddonNote:
        try:
            return self._notes[note_id]
        except KeyError:
            raise NoteNotFoundError(f"note {note_id} not found")

    def update(self, note_id: NoteId, note: AddonNote) -> None:
        self.get(note_id)
        self._notes[note_id] = note

    def add(self, note: AddonNote, deck_name: str) -> NoteId:
        note_id = NoteId(self._next_id)
        self._next_id += 1
        self._notes[note_id] = note
        return note_id

    def remove(self, note_ids: list[NoteId]) -> None:
        for note_id in note_ids:
            self.get(note_id)
            del self._notes[note_id]


def _haystack(note: AddonNote) -> str:
    tags = " ".join(note.tags) if note.tags else ""
    return f"{note.front} {note.back} {tags}".lower()
