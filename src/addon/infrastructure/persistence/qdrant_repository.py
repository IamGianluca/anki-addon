from typing import List, Optional

from qdrant_client.http.models import PointStruct

from ...domain.repositories.document_repository import (
    Document,
    DocumentRepository,
    SearchQuery,
    SearchResult,
)


class QdrantDocumentRepository(DocumentRepository):
    """Infrastructure implementation with Nullable pattern"""

    @staticmethod
    def create():
        from qdrant_client import QdrantClient

        client = QdrantClient(":memory:")
        repo = QdrantDocumentRepository(client)
        repo._ensure_collection_exists()  # Create collection on startup
        return repo

    @staticmethod
    def create_null(
        search_responses: Optional[List[List[SearchResult]]] = None,
        stored_documents: Optional[List[Document]] = None,
    ):
        """Nullable with configurable responses"""
        # Create default responses if none provided
        if search_responses is None:
            default_doc = Document(
                id="null_doc_1",
                content="Default null content",
                source="null_source",
                metadata={},
            )
            search_responses = [[SearchResult(default_doc, 0.95)]]

        return QdrantDocumentRepository(
            QdrantDocumentRepository._StubbedQdrantClient(
                search_responses, stored_documents or []
            )
        )

    def __init__(self, client):
        self._client = client
        self._collection_name = "docs"

    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist"""
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
                    size=384, distance=Distance.COSINE
                ),
            )
        except Exception as e:
            # Re-raise if we can't create the collection
            raise RuntimeError(
                f"Failed to create Qdrant collection '{self._collection_name}': {e}"
            )

    def store(self, document: Document) -> None:
        # Ensure collection exists before storing
        self._ensure_collection_exists()

        # Real implementation would vectorize and store
        # breakpoint()
        self._client.upsert(
            collection_name=self._collection_name,
            points=[
                PointStruct(
                    id=document.id,
                    vector=self._vectorize(document.content),
                    payload={
                        "content": document.content,
                        "source": document.source,
                        "metadata": document.metadata,
                    },
                )
            ],
        )

    def store_batch(self, documents: List[Document]) -> None:
        """Efficient batch storage"""
        if not documents:
            return

        # Ensure collection exists before storing
        self._ensure_collection_exists()

        # Create all points first, then do single upsert
        points = []
        for doc in documents:
            points.append(
                PointStruct(
                    id=doc.id,
                    vector=self._vectorize(doc.content),
                    payload={
                        "content": doc.content,
                        "source": doc.source,
                        "metadata": doc.metadata,
                    },
                )
            )

        self._client.upsert(
            collection_name=self._collection_name, points=points
        )

    def find_similar(self, query: SearchQuery) -> List[SearchResult]:
        # Ensure collection exists before searching
        self._ensure_collection_exists()

        results = self._client.query_points(
            collection_name=self._collection_name,
            query=self._vectorize(query.text),
            limit=query.max_results,
        )
        return [self._map_result(hit) for hit in results.points]

    def find_by_id(self, doc_id: str) -> Optional[Document]:
        # Ensure collection exists before retrieving
        self._ensure_collection_exists()

        result = self._client.retrieve(
            collection_name=self._collection_name, ids=[doc_id]
        )
        return self._map_document(result[0]) if result else None

    def _vectorize(self, text: str) -> List[float]:
        # Dummy implementation - in real code, use sentence transformers or similar
        import hashlib

        hash_obj = hashlib.md5(text.encode())
        # Generate dummy 384-dimensional vector from hash
        vector = []
        hex_str = hash_obj.hexdigest()
        for i in range(384):
            # Use modulo to cycle through hash characters
            char_index = i % len(hex_str)
            # Convert hex char to float between -1 and 1
            char_value = int(hex_str[char_index], 16)
            normalized_value = (char_value / 15.0) * 2 - 1
            vector.append(normalized_value)
        return vector

    def _map_result(self, hit) -> SearchResult:
        """Map Qdrant search result to domain object"""
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

    def _map_document(self, point) -> Document:
        """Map Qdrant point to domain document"""
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
        """Embedded stub that mimics Qdrant behavior"""

        def __init__(
            self,
            search_responses: List[List[SearchResult]],
            stored_docs: List[Document],
        ):
            self._search_responses = search_responses.copy()
            self._stored_docs = {doc.id: doc for doc in stored_docs}
            self._points = {}

        def get_collection(self, collection_name: str):
            """Stub - always succeeds"""
            return {"status": "green"}

        def create_collection(self, collection_name: str, vectors_config):
            """Stub - always succeeds"""
            pass

        def upsert(self, collection_name: str, points: List[PointStruct]):
            for point in points:
                self._points[point.id] = point

        def query_points(
            self, collection_name: str, query: List[float], limit: int
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

        def retrieve(self, collection_name: str, ids: List[str]):
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
