from __future__ import annotations

from addon.domain.entities.note import AddonCollection, AddonNote
from addon.domain.repositories.document_repository import (
    DocumentRepository,
    SearchQuery,
    convert_addon_note_to_document,
    convert_document_to_addon_note,
)


class SimilarNoteFinder:
    """The main purpose of this class is to load data into Qdrant (AddonNone or
    AddonCollection to List[Documents], and take care of generating the needed
    queries and processing responses.
    """

    def __init__(
        self, collection: AddonCollection, repository: DocumentRepository
    ) -> None:
        self._collection = collection
        self._repository = repository

        # Load notes in repository
        documents = []
        for note in self._collection:
            documents.append(convert_addon_note_to_document(note))
        self._repository.store_batch(documents)

    def find_duplicates(self, note: AddonNote) -> list[AddonNote] | None:
        if note.tags:
            tags = "".join([t for t in note.tags])
        else:
            tags = ""
        query = SearchQuery(f"{note.front} {note.back} {tags}", max_results=1)
        results = self._repository.find_similar(query)
        if results:
            return [
                convert_document_to_addon_note(d.document) for d in results
            ]
        else:
            return None
