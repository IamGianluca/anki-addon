from __future__ import annotations

from addon.domain.entities.note import AddonCollection, AddonNote
from addon.domain.repositories.document_repository import (
    DocumentRepository,
    SearchQuery,
    convert_addon_note_to_document,
    convert_document_to_addon_note,
)


class SimilarNoteFinder:
    """Application service for finding duplicate notes using semantic similarity search.

    This class implements the core use case of identifying potentially duplicate
    notes within a collection by leveraging vector embeddings and similarity
    search. It bridges the gap between domain entities (AddonNote/AddonCollection)
    and infrastructure concerns (document repository and vector storage).

    The service initializes by bulk-loading all notes from a collection into
    the vector database, then provides similarity search functionality to find
    potential duplicates based on semantic content rather than exact text matching.
    This enables detection of duplicates even when wording differs slightly.

    Key responsibilities:
    - Converting domain entities to searchable document representations
    - Bulk loading note collections into the vector database for indexing
    - Performing semantic similarity searches to identify potential duplicates
    - Converting search results back to domain entities for application use

    The similarity search combines front, back, and tag content to create a
    comprehensive query that captures the full semantic meaning of a note,
    improving duplicate detection accuracy.

    Attributes:
        _collection: The collection of notes being searched for duplicates.
        _repository: Vector database repository for storing and searching documents.
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

    def find_duplicates(self, note: AddonNote) -> list[AddonNote]:
        if note.tags:
            tags = " ".join([t for t in note.tags])
        else:
            tags = ""
        query = SearchQuery(f"{note.front} {note.back} {tags}", max_results=1)
        results = self._repository.find_similar(query)
        if results:
            return [
                convert_document_to_addon_note(d.document) for d in results
            ]
        else:
            return []
