from __future__ import annotations

from typing import Protocol

from ..entities.note import AddonNote, NoteId


class NoteNotFoundError(Exception):
    """Raised when a note lookup by ID fails."""


class InvalidSearchQueryError(Exception):
    """Raised when the backend cannot parse a search query."""


class NoteRepository(Protocol):
    """Repository port for notes in the user's collection.

    Defines the domain's requirements for note persistence and
    retrieval. The Anki adapter implements this over a live Collection;
    tests use an in-memory fake.

    The query syntax accepted by `search` is implementation-defined
    (the Anki adapter passes it through to Anki's search grammar).
    """

    def search(self, query: str, limit: int = 10) -> list[NoteId]:
        """Return ids of notes matching the query, at most `limit`."""
        ...

    def get(self, note_id: NoteId) -> AddonNote:
        """Retrieve a note by id.

        Raises:
            NoteNotFoundError: If no note exists with the given id.
        """
        ...

    def update(self, note_id: NoteId, note: AddonNote) -> None:
        """Replace the content of an existing note (fields and tags).

        Raises:
            NoteNotFoundError: If no note exists with the given id.
        """
        ...

    def add(self, note: AddonNote, deck_name: str) -> NoteId:
        """Store a new note in the given deck; return its id."""
        ...

    def remove(self, note_ids: list[NoteId]) -> None:
        """Delete notes (and their cards) from the collection.

        Raises:
            NoteNotFoundError: If any id does not exist.
        """
        ...
