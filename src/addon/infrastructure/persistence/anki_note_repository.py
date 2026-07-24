from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ...application.services.formatter_service import AnkiNoteMapper
from ...domain.entities.note import AddonNote, AddonNoteType, NoteId
from ...domain.repositories.note_repository import (
    InvalidSearchQueryError,
    NoteNotFoundError,
)

if TYPE_CHECKING:
    from anki.collection import Collection
    from anki.notes import Note
    from anki.notes import NoteId as AnkiNoteId


class AnkiNoteRepository:
    """NoteRepository adapter over a live Anki collection.

    Search queries are passed through to Anki's search grammar, so
    callers (e.g. the curation agent) can use field scopes, tags, decks,
    negation and `or`. Note creation resolves the abstract notetype
    (basic/cloze) to a concrete Anki notetype via the configured names;
    those notetypes must use the standard field names ("Front"/"Back"
    resp. "Text"/"Back Extra"), as AnkiNoteMapper assumes them.
    """

    def __init__(
        self,
        col: Collection,
        basic_notetype: str = "Basic",
        cloze_notetype: str = "Cloze",
    ) -> None:
        self._col = col
        self._basic_notetype = basic_notetype
        self._cloze_notetype = cloze_notetype

    def search(self, query: str, limit: int = 10) -> list[NoteId]:
        try:
            note_ids = self._col.find_notes(query)
        except Exception as e:
            # Imported here so the import only runs when a query actually
            # failed: importing anki costs ~1s, which unit tests would
            # otherwise pay on every search.
            from anki.errors import SearchError

            if isinstance(e, SearchError):
                raise InvalidSearchQueryError(str(e)) from e
            raise
        return [NoteId(int(nid)) for nid in note_ids[:limit]]

    def get(self, note_id: NoteId) -> AddonNote:
        return AnkiNoteMapper.to_addon_note(self._get_anki_note(note_id))

    def update(self, note_id: NoteId, note: AddonNote) -> None:
        anki_note = self._get_anki_note(note_id)
        AnkiNoteMapper.merge_addon_changes(anki_note, note, include_tags=True)
        self._col.update_note(anki_note)

    def add(self, note: AddonNote, deck_name: str) -> NoteId:
        notetype_name = (
            self._cloze_notetype
            if note.notetype == AddonNoteType.CLOZE
            else self._basic_notetype
        )
        notetype = self._col.models.by_name(notetype_name)
        if notetype is None:
            raise RuntimeError(
                f"Notetype {notetype_name!r} not found in the collection. "
                "Check the addon's notetype configuration."
            )
        deck_id = self._col.decks.id_for_name(deck_name)
        if deck_id is None:
            raise RuntimeError(f"Deck {deck_name!r} not found.")
        anki_note = self._col.new_note(notetype)
        AnkiNoteMapper.merge_addon_changes(anki_note, note, include_tags=True)
        self._col.add_note(anki_note, deck_id)
        return NoteId(anki_note.id)

    def remove(self, note_ids: list[NoteId]) -> None:
        for note_id in note_ids:
            self._ensure_exists(note_id)
        # cast: anki's NoteId/DeckId are NewTypes over int; the cast is
        # free at runtime and avoids importing anki for the conversion.
        self._col.remove_notes(cast("list[AnkiNoteId]", note_ids))

    def _get_anki_note(self, note_id: NoteId) -> Note:
        self._ensure_exists(note_id)
        return self._col.get_note(cast("AnkiNoteId", note_id))

    def _ensure_exists(self, note_id: NoteId) -> None:
        # Existence check via search instead of catching anki's
        # NotFoundError: it only uses the Collection search surface and
        # avoids importing anki.errors in the happy path.
        if not self._col.find_notes(f"nid:{note_id}"):
            raise NoteNotFoundError(f"note {note_id} not found")
