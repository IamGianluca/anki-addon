from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ...domain.repositories.document_repository import (
    Document,
    DocumentNotFoundError,
    DocumentRepository,
    SearchQuery,
    SearchResult,
)
from ...infrastructure.protocols import EmbeddingModel, QdrantDriver

if TYPE_CHECKING:
    # These dependencies are needed for type checking. We do not import these
    # dependencies at the top of file because they have slow side effects that
    # significantly increase the test suite execution time.
    from qdrant_client.models import PointStruct


class QdrantDocumentRepository(DocumentRepository):
    """Vector database adapter using Qdrant."""

    def __init__(
        self,
        encoder: EmbeddingModel,
        client: QdrantDriver | None = None,
        collection_name: str = "docs",
    ) -> None:
        self._collection_name = collection_name
        self._encoder = encoder
        self._client: QdrantDriver
        if client is None:
            from qdrant_client import QdrantClient as _QdrantClient

            self._client = cast(QdrantDriver, _QdrantClient(":memory:"))
        else:
            self._client = client

    def _create_point(self, document: Document) -> "PointStruct":
        from qdrant_client.models import PointStruct

        return PointStruct(
            id=document.id,
            vector=cast(list[float], self._vectorize(document.content)),
            payload={
                "content": document.content,
                "source": document.source,
                "metadata": document.metadata,
            },
        )

    def store(self, document: Document) -> None:
        point = self._create_point(document)
        self._client.upsert(
            collection_name=self._collection_name, points=[point]
        )

    def store_batch(self, documents: list[Document]) -> None:
        if not documents:
            return
        points = [self._create_point(doc) for doc in documents]
        self._client.upsert(
            collection_name=self._collection_name, points=points
        )

    def find_similar(self, query: SearchQuery) -> list[SearchResult]:
        results = self._client.query_points(
            collection_name=self._collection_name,
            query=self._vectorize(query.text),
            limit=query.max_results,
        )
        return [
            self._qdrant_hit_to_search_result(hit) for hit in results.points
        ]

    def find_by_id(self, doc_id: str) -> Document:
        result = self._client.retrieve(
            collection_name=self._collection_name, ids=[doc_id]
        )
        if not result:
            raise DocumentNotFoundError(
                f"Document with id '{doc_id}' not found"
            )
        return self._qdrant_point_to_document(result[0])

    def _vectorize(self, text: str) -> list[int]:
        return self._encoder.encode(text)

    def _qdrant_hit_to_search_result(self, hit) -> SearchResult:
        """Handles both dict and object formats from different Qdrant
        client versions.
        """
        # Handle both dict and object formats from Qdrant
        if isinstance(hit, dict):
            doc_id = str(hit.get("id", ""))
            score = hit.get("score", 0.0)
            payload = hit.get("payload", {})
        else:
            doc_id = str(hit.id)
            score = hit.score
            payload = hit.payload

        doc = Document(
            id=doc_id,
            content=payload.get("content", ""),
            source=payload.get("source", ""),
            metadata=payload.get("metadata", {}),
        )
        return SearchResult(doc, score)

    def _qdrant_point_to_document(self, point) -> Document:
        """Handles both dict and object formats from different Qdrant
        client versions.
        """
        # Handle both dict and object formats from Qdrant
        if isinstance(point, dict):
            doc_id = str(point.get("id", ""))
            payload = point.get("payload", {})
        else:
            doc_id = str(point.id)
            payload = point.payload

        return Document(
            id=doc_id,
            content=payload.get("content", ""),
            source=payload.get("source", ""),
            metadata=payload.get("metadata", {}),
        )
