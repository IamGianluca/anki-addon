"""Test doubles for Qdrant interactions.

Two fakes at different levels:

- FakeSentenceTransformer: fakes the embedding model. Avoids 20+ second library
  loading overhead caused by SentenceTransformer during test execution.
- FakeQdrantClient: fakes the Qdrant client. Enables testing without running
  an actual Qdrant server.
"""

from __future__ import annotations

from addon.domain.repositories.document_repository import (
    Document,
    SearchResult,
)


class FakeSentenceTransformer:
    """Fake embedding model for tests.

    Returns a fixed 7-dimensional embedding regardless of input.
    """

    def __init__(self, model_name_or_path: str = "fake") -> None:
        self._embedding = [0, 0, 0, 0, 0, 0, 0]

    def encode(self, text: str) -> list[int]:
        return self._embedding

    def get_sentence_embedding_dimension(self) -> int:
        return len(self._embedding)


class FakeQdrantClient:
    """Fake Qdrant client for unit tests.

    Accepts pre-configured search responses and tracks stored documents.
    """

    def __init__(
        self,
        search_responses: list[list[SearchResult]] | None = None,
        stored_documents: list[Document] | None = None,
    ) -> None:
        self._search_responses = (search_responses or []).copy()
        self._stored_docs = {doc.id: doc for doc in stored_documents or []}
        self._points: dict[str, _MockPoint] = {}

    def get_collection(self, collection_name: str) -> dict:
        return {"status": "green"}

    def create_collection(
        self, collection_name: str, vectors_config: object
    ) -> None:
        pass

    def upsert(self, collection_name: str, points: list[object]) -> None:
        for point in points:
            self._points[str(point.id)] = _MockPoint(
                id=point.id, payload=point.payload
            )

    def query_points(
        self, collection_name: str, query: list[float], limit: int
    ) -> _MockQueryResponse:
        if not self._search_responses:
            return _MockQueryResponse([])

        results = self._search_responses.pop(0)
        mock_points = [_MockScoredPoint(r) for r in results[:limit]]
        return _MockQueryResponse(mock_points)

    def retrieve(self, collection_name: str, ids: list[str]) -> list:
        return [
            self._points[doc_id] for doc_id in ids if doc_id in self._points
        ]


class _MockPoint:
    """Minimal PointStruct stand-in."""

    def __init__(self, id: str, payload: dict) -> None:
        self.id = id
        self.payload = payload


class _MockScoredPoint:
    """Minimal ScoredPoint stand-in for query results."""

    def __init__(self, result: SearchResult) -> None:
        self.id = result.document.id
        self.score = result.relevance_score
        self.payload = {
            "content": result.document.content,
            "source": result.document.source,
            "metadata": result.document.metadata,
        }


class _MockQueryResponse:
    """Minimal QueryResponse stand-in."""

    def __init__(self, points: list[_MockScoredPoint]) -> None:
        self.points = points
