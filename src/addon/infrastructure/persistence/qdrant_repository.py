from __future__ import (
    annotations,  # Avoid slow import of torch.Tensor, which is only required for type hint
)

from typing import TYPE_CHECKING, Protocol, cast

from ...domain.repositories.document_repository import (
    Document,
    DocumentNotFoundError,
    DocumentRepository,
    SearchQuery,
    SearchResult,
)

if TYPE_CHECKING:
    # These dependencies are needed for type checking. We do not import these
    # dependencies at the top of file because they have slow side effects that
    # significantly increase the test suite execution time.
    from qdrant_client.models import PointStruct
    from torch import Tensor


class EmbeddingModel(Protocol):
    def encode(self, text: str) -> list[int]: ...

    def get_sentence_embedding_dimension(self) -> int:
        """Required to create a new Qdrant collection."""
        ...


class QdrantDocumentRepository(DocumentRepository):
    """Vector database adapter using Qdrant."""

    @staticmethod
    def create(
        encoder: EmbeddingModel,
        client: object | None = None,
    ) -> QdrantDocumentRepository:
        if client is None:
            from qdrant_client import QdrantClient

            client = QdrantClient(":memory:")
        repo = QdrantDocumentRepository(client, encoder=encoder)
        repo._ensure_collection_exists()
        return repo

    def __init__(
        self,
        client,
        encoder: EmbeddingModel,
        collection_name: str = "docs",
    ):
        self._client = client
        self._collection_name = collection_name
        self._encoder = encoder

    def _ensure_collection_exists(self) -> None:
        try:
            _ = self._client.get_collection(self._collection_name)
            return
        except Exception:
            pass

        try:
            from qdrant_client.models import Distance, VectorParams

            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(
                    size=self._encoder.get_sentence_embedding_dimension(),
                    distance=Distance.DOT,
                ),
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create Qdrant collection '{self._collection_name}': {e}"
            )

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
        self._ensure_collection_exists()
        point = self._create_point(document)
        self._client.upsert(
            collection_name=self._collection_name, points=[point]
        )

    def store_batch(self, documents: list[Document]) -> None:
        if not documents:
            return
        self._ensure_collection_exists()
        points = [self._create_point(doc) for doc in documents]
        self._client.upsert(
            collection_name=self._collection_name, points=points
        )

    def find_similar(self, query: SearchQuery) -> list[SearchResult]:
        # Ensure collection exists before searching
        self._ensure_collection_exists()

        results = self._client.query_points(
            collection_name=self._collection_name,
            query=self._vectorize(query.text),
            limit=query.max_results,
        )
        return [
            self._qdrant_hit_to_search_result(hit) for hit in results.points
        ]

    def find_by_id(self, doc_id: str) -> Document:
        # Ensure collection exists before retrieving
        self._ensure_collection_exists()

        result = self._client.retrieve(
            collection_name=self._collection_name, ids=[doc_id]
        )
        if not result:
            raise DocumentNotFoundError(
                f"Document with id '{doc_id}' not found"
            )
        return self._qdrant_point_to_document(result[0])

    def _vectorize(
        self, text: str
    ) -> Tensor | list[int]:  # Not imported since it has slow side effects
        return self._encoder.encode(text)

    def _qdrant_hit_to_search_result(self, hit) -> SearchResult:
        """Handles both dict and object formats from different Qdrant client versions."""
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
        """Handles both dict and object formats from different Qdrant client versions."""
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
