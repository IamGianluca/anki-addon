from __future__ import (
    annotations,  # Avoid slow import of torch.Tensor, which is only required for type hint
)

from typing import TYPE_CHECKING, Protocol

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
        """Do not remove. This method is required to create a new Qdrant
        collection.
        """
        ...


class FakeSentenceTransformer:
    """Avoids 20+ second library loading overhead caused by SentenceTransformer
    during test execution.
    """

    def __init__(self, model_name_or_path: str) -> None:
        self._embedding = [0, 0, 0, 0, 0, 0, 0]
        pass

    def encode(self, text: str) -> list[int]:
        return self._embedding

    def get_sentence_embedding_dimension(self) -> int:
        return len(self._embedding)


class QdrantDocumentRepository(DocumentRepository):
    """Vector database using Qdrant with Null Object pattern for testability."""

    @staticmethod
    def create(encoder: EmbeddingModel):
        from qdrant_client import QdrantClient

        client = QdrantClient(":memory:")
        repo = QdrantDocumentRepository(client, encoder=encoder)
        repo._ensure_collection_exists()  # Create collection on startup
        return repo

    @staticmethod
    def create_null(
        search_responses: Optional[list[list[SearchResult]]] = None,
        stored_documents: Optional[list[Document]] = None,
    ):
        # Create default responses if none provided
        if search_responses is None:
            default_doc = Document(
                id="null_doc_1",
                content="Default null content",
                source="null_source",
                metadata={},
            )
            search_responses = [[SearchResult(default_doc, 0.95)]]

        # Loading the encoder model into memory is quite expensive (20+ seconds
        # on old machines). We are using a Fake implementation, that mimic the
        # original dependency to bypass this performance drag
        encoder = FakeSentenceTransformer("fake-embedding-model")

        return QdrantDocumentRepository(
            QdrantDocumentRepository._StubbedQdrantClient(
                search_responses, stored_documents or []
            ),
            encoder=encoder,
        )

    def __init__(
        self,
        client,
        encoder: EmbeddingModel,
        collection_name: str = "docs",
    ):
        self._client = client
        self._collection_name = collection_name
        self._encoder = encoder

    def _ensure_collection_exists(self):
        # Skip for stubbed clients (they don't need real collections)
        if hasattr(self._client, "_search_responses"):
            return

        try:
            # Try to get collection info
            _ = self._client.get_collection(self._collection_name)
            # If we get here, collection exists
            return
        except Exception:
            # Collection doesn't exist, create it
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
            # Re-raise if we can't create the collection
            raise RuntimeError(
                f"Failed to create Qdrant collection '{self._collection_name}': {e}"
            )

    def _create_point(self, document: Document):
        """Adapts between test mode (mock) and production mode (PointStruct)."""
        if hasattr(self._client, "_search_responses"):
            # Test mode - simple mock object
            return type(
                "MockPoint",
                (),
                {
                    "id": document.id,
                    "vector": self._vectorize(document.content),
                    "payload": {
                        "content": document.content,
                        "source": document.source,
                        "metadata": document.metadata,
                    },
                },
            )()
        else:
            # Production mode - real PointStruct
            from qdrant_client.models import PointStruct

            return PointStruct(
                id=document.id,
                vector=self._vectorize(document.content),
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
        return [self._qdrant_hit_to_search_result(hit) for hit in results.points]

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
    ) -> Tensor:  # Not imported since it has slow side effects
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

    class _StubbedQdrantClient:
        """Enables testing without running actual Qdrant server."""

        def __init__(
            self,
            search_responses: list[list[SearchResult]],
            stored_docs: list[Document],
        ):
            self._search_responses = search_responses.copy()
            self._stored_docs = {doc.id: doc for doc in stored_docs}
            self._points = {}

        def get_collection(self, collection_name: str):
            return {"status": "green"}

        def create_collection(self, collection_name: str, vectors_config):
            pass

        def upsert(self, collection_name: str, points: list[PointStruct]):
            for point in points:
                self._points[point.id] = point

        def query_points(
            self, collection_name: str, query: list[float], limit: int
        ):
            class MockScoredPoint:
                def __init__(self, result: SearchResult):
                    self.id = result.document.id
                    self.score = result.relevance_score
                    self.payload = {
                        "content": result.document.content,
                        "source": result.document.source,
                        "metadata": result.document.metadata,
                    }

            class MockQueryResponse:
                def __init__(self, points):
                    self.points = points

            if not self._search_responses:
                return MockQueryResponse([])

            results = self._search_responses.pop(0)

            mock_points = [MockScoredPoint(r) for r in results[:limit]]
            return MockQueryResponse(mock_points)

        def retrieve(self, collection_name: str, ids: list[str]):
            results = []
            for doc_id in ids:
                if doc_id in self._points:
                    point = self._points[doc_id]

                    class MockPoint:
                        def __init__(self, point_data):
                            self.id = point_data.id
                            self.payload = point_data.payload

                    results.append(MockPoint(point))
            return results
