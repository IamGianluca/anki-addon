from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Document:
    """Domain entity"""

    id: str
    content: str
    source: str
    metadata: dict


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
