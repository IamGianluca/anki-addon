"""Test doubles for domain ports."""

from __future__ import annotations

from addon.domain.repositories.document_repository import (
    Document,
    DocumentNotFoundError,
    DocumentRepository,
    SearchQuery,
    SearchResult,
)


class FakeDocumentRepository(DocumentRepository):
    """Fake document repository for domain-level tests.

    Records search queries for verification and always returns empty results.
    """

    def __init__(self) -> None:
        self.captured_queries: list[str] = []

    def store(self, document: Document) -> None:
        pass

    def store_batch(self, documents: list[Document]) -> None:
        pass

    def find_similar(self, query: SearchQuery) -> list[SearchResult]:
        self.captured_queries.append(query.text)
        return []

    def find_by_id(self, doc_id: str) -> Document:
        raise DocumentNotFoundError(f"Document with id '{doc_id}' not found")
