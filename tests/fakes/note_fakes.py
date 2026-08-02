"""In-memory fake of the NoteRepository port for unit tests."""

from __future__ import annotations

import dataclasses

from addon.domain.entities.note import AddonNote, NoteId
from addon.domain.repositories.note_repository import (
    InvalidSearchQueryError,
    NoteNotFoundError,
    NoteRepository,
)


class FakeNoteRepository(NoteRepository):
    """Dict-backed NoteRepository fake.

    Search does case-insensitive substring matching over front, back and
    tags — a predictable stand-in for Anki's search grammar.

    Supports `or` to combine clauses (note matches if any clause matches)
    and strips field prefixes (`tag:`, `front:`, `back:`, `deck:`) since
    the haystack already contains tag text. Quoted phrases are treated as
    single terms. Queries with unbalanced quotes raise
    InvalidSearchQueryError, mimicking Anki's parser.
    """

    def __init__(self, notes: dict[int, AddonNote] | None = None) -> None:
        self._notes: dict[int, AddonNote] = dict(notes or {})
        self._next_id = max(self._notes, default=0) + 1

    def search(self, query: str, limit: int = 10) -> list[NoteId]:
        clauses = _parse_query(query)
        haystacks = {
            note_id: _haystack(note) for note_id, note in self._notes.items()
        }
        matching_ids = {
            note_id
            for note_id, text in haystacks.items()
            if any(all(term in text for term in clause) for clause in clauses)
        }
        # Return in stable (insertion) order, respecting limit.
        return [
            NoteId(note_id)
            for note_id in self._notes
            if note_id in matching_ids
        ][:limit]

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
        self._notes[note_id] = dataclasses.replace(note, deck_name=deck_name)
        return note_id

    def remove(self, note_ids: list[NoteId]) -> None:
        for note_id in note_ids:
            self.get(note_id)
            del self._notes[note_id]


def _haystack(note: AddonNote) -> str:
    tags = " ".join(note.tags) if note.tags else ""
    return f"{note.front} {note.back} {tags}".lower()


def _parse_query(query: str) -> list[list[str]]:
    """Parse a search query into a list of clauses (OR of ANDs).

    Each clause is a list of terms that must all match (AND).
    Clauses are separated by `or` (OR — any clause can match).
    Field prefixes (`tag:`, `front:`, etc.) are stripped.
    Quoted phrases are kept as single terms.
    """
    if query.count('"') % 2:
        raise InvalidSearchQueryError("unbalanced quotes")

    raw = query.lower()
    # Split on ` or ` to get clauses.
    clause_strs = [c.strip() for c in raw.split(" or ") if c.strip()]
    return [_extract_terms(cs) for cs in clause_strs]


def _extract_terms(clause: str) -> list[str]:
    """Extract search terms from a single clause, stripping field
    prefixes and negation markers."""
    terms: list[str] = []
    # Handle quoted phrases and bare words.
    i = 0
    while i < len(clause):
        if clause[i] == '"':
            # Find closing quote.
            end = clause.index('"', i + 1)
            terms.append(clause[i + 1:end])
            i = end + 1
        elif clause[i].isspace():
            i += 1
        else:
            # Read until next space or quote.
            end = i
            while end < len(clause) and not clause[end].isspace() and clause[end] != '"':
                end += 1
            word = clause[i:end]
            # Strip negation prefix.
            if word.startswith("-"):
                word = word[1:]
            # Strip field prefix (e.g. "tag:", "front:", "back:", "deck:").
            if ":" in word:
                word = word.split(":", 1)[1]
            # Strip wildcards.
            word = word.rstrip("*")
            if word:
                terms.append(word)
            i = end
    return terms
