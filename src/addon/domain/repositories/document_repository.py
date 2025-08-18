from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List
from uuid import uuid4

from addon.domain.entities.note import AddonNote


@dataclass
class Document:
    """Domain entity"""

    id: str
    content: str
    source: str
    metadata: dict[str, Any]


@dataclass
class SearchQuery:
    """Domain value object"""

    text: str
    max_results: int = 5


@dataclass
class SearchResult:
    """Domain value object"""

    document: Document
    relevance_score: float


class DocumentRepository(ABC):
    """Domain port - defines what the domain needs"""

    @abstractmethod
    def store(self, document: Document) -> None:
        """Store a single document"""
        pass

    @abstractmethod
    def store_batch(self, documents: List[Document]) -> None:
        """Store multiple documents efficiently"""
        pass

    @abstractmethod
    def find_similar(self, query: SearchQuery) -> List[SearchResult]:
        """Find documents similar to the query"""
        pass


def convert_addon_note_to_document(note: AddonNote) -> Document:
    tags = ""
    if note.tags:
        tags = "".join([t for t in note.tags])
    return Document(
        id=str(uuid4()),
        content=f"{note.front} {note.back} {tags}",
        source="",
        metadata=note.__dict__,
    )


def convert_document_to_addon_note(document: Document) -> AddonNote:
    return AddonNote(**document.metadata)  # type: ignore[missing-argument]


def convert_result_to_document(result: SearchResult) -> Document:
    return result.document


def convert_result_to_addon_note(result: SearchResult) -> AddonNote:
    doc = convert_result_to_document(result)
    return convert_document_to_addon_note(doc)
