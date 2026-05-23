"""Test doubles for Qdrant interactions.

Two fakes at different levels:

- FakeSentenceTransformer: fakes the embedding model. Avoids 20+ second library
  loading overhead caused by SentenceTransformer during test execution.
- FakeQdrantClient: fakes the Qdrant client. Enables testing without running
  an actual Qdrant server.
"""

from __future__ import annotations

from typing import Any

from addon.infrastructure.protocols import EmbeddingModel, QdrantDriver


class FakeSentenceTransformer(EmbeddingModel):
    """Fake embedding model for tests.

    Returns a fixed 7-dimensional embedding regardless of input.
    """

    def __init__(self, model_name_or_path: str = "fake") -> None:
        self._embedding = [0, 0, 0, 0, 0, 0, 0]

    def encode(self, text: str) -> list[int]:
        return self._embedding

    def get_sentence_embedding_dimension(self) -> int:
        return len(self._embedding)


class FakeQdrantClient(QdrantDriver):
    """Fake Qdrant client for unit tests.

    Accepts pre-configured search responses (as mock point dicts) and tracks
    stored documents.
    """

    def __init__(
        self,
        search_responses: list[list[dict[str, Any]]] | None = None,
        stored_documents: list[object] | None = None,
    ) -> None:
        self._search_responses = (search_responses or []).copy()
        self._stored_docs: dict[str, object] = {}
        if stored_documents:
            self._stored_docs = {doc.id: doc for doc in stored_documents}
        self._points: dict[str, _MockPoint] = {}

    def get_collection(self, collection_name: str, **kwargs: object) -> dict:
        return {"status": "green"}

    def create_collection(
        self, collection_name: str, vectors_config: object, **kwargs: object
    ) -> None:
        pass

    def upsert(
        self, collection_name: str, points: object, **kwargs: object
    ) -> None:
        for point in points:  # type: ignore[misc]
            self._points[str(point.id)] = _MockPoint(
                id=point.id, payload=point.payload
            )

    def query_points(
        self, collection_name: str, query: object, limit: int, **kwargs: object
    ) -> _MockQueryResponse:
        if not self._search_responses:
            return _MockQueryResponse([])

        results = self._search_responses.pop(0)
        mock_points = [
            _MockScoredPoint(p["id"], p["score"], p["payload"])
            for p in results[:limit]
        ]
        return _MockQueryResponse(mock_points)

    def retrieve(
        self, collection_name: str, ids: list[str], **kwargs: object
    ) -> list[object]:
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

    def __init__(self, id: str, score: float, payload: dict) -> None:
        self.id = id
        self.score = score
        self.payload = payload


class _MockQueryResponse:
    """Minimal QueryResponse stand-in."""

    def __init__(self, points: list[_MockScoredPoint]) -> None:
        self.points = points
