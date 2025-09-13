from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List
from uuid import uuid4

from addon.domain.entities.note import AddonNote


@dataclass
class Document:
    """Represents a document in the domain model.

    A document is a core domain entity that encapsulates textual content
    along with its metadata for storage and retrieval operations.

    Attributes:
        id: Unique identifier for the document
        content: The main textual content of the document
        source: Origin or source of the document content
        metadata: Additional key-value pairs containing document metadata
    """

    id: str
    content: str
    source: str
    metadata: dict[str, Any]


@dataclass
class SearchQuery:
    """Represents a search query for finding similar documents.

    This value object encapsulates the parameters needed to perform
    a similarity search across the document collection.

    Attributes:
        text: The query text to search for
        max_results: Maximum number of results to return (default: 5)
    """

    text: str
    max_results: int = 5


@dataclass
class SearchResult:
    """Represents a single result from a document search operation.

    Contains a document that matched the search query along with
    its relevance score indicating how well it matches.

    Attributes:
        document: The matching document
        relevance_score: Numeric score indicating relevance (higher = more relevant)
    """

    document: Document
    relevance_score: float


class DocumentRepository(ABC):
    """Abstract repository interface for document storage and retrieval.

    This repository defines the domain's requirements for document persistence
    and search operations. Implementations should provide concrete storage
    mechanisms (e.g., vector databases, search engines).
    """

    @abstractmethod
    def store(self, document: Document) -> None:
        pass

    @abstractmethod
    def store_batch(self, documents: List[Document]) -> None:
        """Should be more efficient than individual store() calls."""
        pass

    @abstractmethod
    def find_similar(self, query: SearchQuery) -> List[SearchResult]:
        """Returns results ordered by relevance score (descending)."""
        pass


def convert_addon_note_to_document(note: AddonNote) -> Document:
    """Combines front/back/tags into searchable content; preserves original in metadata."""
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
    """Reconstructs from metadata - assumes document was created via convert_addon_note_to_document."""
    return AddonNote(**document.metadata)  # type: ignore[missing-argument]


def convert_result_to_document(result: SearchResult) -> Document:
    return result.document


def convert_result_to_addon_note(result: SearchResult) -> AddonNote:
    doc = convert_result_to_document(result)
    return convert_document_to_addon_note(doc)
