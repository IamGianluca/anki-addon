import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient

COLLECTION_NAME = "anki_collection"


class VectorDB:
    """Infrastructure wrapper for Qdrant vector database."""

    @staticmethod
    def create():
        """Production factory - uses real QdrantClient with sensible defaults"""
        client = QdrantClient(":memory:")
        return VectorDB(client)

    @staticmethod
    def create_null(
        search_responses: Optional[List[List[Dict[str, Any]]]] = None,
    ):
        """Null factory - uses stubbed QdrantClient with configurable responses"""

        def _format_response_as_qdrant_search(
            results: List[Dict[str, Any]],
        ) -> List[Dict[str, Any]]:
            """Format search results to match Qdrant's expected response format"""
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append(
                    {
                        "id": result.get("id", f"null_result_{i}"),
                        "score": result.get("score", 0.95),
                        "payload": result.get(
                            "payload",
                            {
                                "source": "null_source",
                                "text": f"Default null result {i}",
                            },
                        ),
                    }
                )
            return formatted_results

        # Default search responses if none provided
        if search_responses is None:
            search_responses = [
                [
                    {
                        "id": "null_result_1",
                        "score": 0.95,
                        "payload": {
                            "source": "null_source",
                            "text": "Default null result",
                        },
                    }
                ]
            ]

        # Format all responses
        formatted_responses = [
            _format_response_as_qdrant_search(response)
            for response in search_responses
        ]

        return VectorDB(VectorDB.StubbedQdrantClient(formatted_responses))

    def __init__(self, qdrant_client) -> None:
        """Shared initialization - works with both real and stubbed clients"""
        self._client = qdrant_client
        self.is_connected = self._check_connection()
        self._event_listeners = {"document_added": [], "search_performed": []}

    def _check_connection(self) -> bool:
        """Check if client is connected"""
        try:
            info = self._client.info()
            return info is not None
        except Exception:
            return False

    def add_documents(
        self,
        documents: List[str],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[Any]] = None,
    ) -> None:
        """Add documents to the vector database"""
        if not self.is_connected:
            raise RuntimeError("VectorDB is not connected")

        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Perform the actual operation
        self._client.add(
            collection_name=COLLECTION_NAME,
            documents=documents,
            metadata=metadata,
            ids=ids,
        )

        # Emit behavior event (not method call tracking)
        self._emit_event(
            "document_added",
            {
                "collection_name": COLLECTION_NAME,
                "document_count": len(documents),
                "ids": ids,
            },
        )

    def search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.is_connected:
            raise RuntimeError("VectorDB is not connected")

        # Perform the actual operation
        results = self._client.query(
            collection_name=COLLECTION_NAME, query_text=query_text, limit=limit
        )

        # Emit behavior event (not method call tracking)
        self._emit_event(
            "search_performed",
            {
                "collection_name": COLLECTION_NAME,
                "query_text": query_text,
                "result_count": len(results),
                "limit": limit,
            },
        )

        return results

    def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit events for output tracking"""
        if event_type in self._event_listeners:
            for listener in self._event_listeners[event_type]:
                listener(event_data)

    def on_document_added(self, listener_fn) -> None:
        """Register listener for document addition events"""
        self._event_listeners["document_added"].append(listener_fn)

    def on_search_performed(self, listener_fn) -> None:
        """Register listener for search events"""
        self._event_listeners["search_performed"].append(listener_fn)

    def track_document_additions(self) -> "DocumentAdditionTracker":
        """Output tracking for document additions"""
        return DocumentAdditionTracker(self)

    def track_searches(self) -> "SearchTracker":
        """Output tracking for searches"""
        return SearchTracker(self)

    class StubbedQdrantClient:
        """Embedded stub that mimics QdrantClient behavior"""

        def __init__(self, search_responses: List[List[Dict[str, Any]]]):
            self._search_responses = search_responses

        def info(self):
            """Stub for connection check"""
            return {"version": "stubbed_version", "status": "ok"}

        def add(
            self,
            collection_name: str,
            documents: List[str],
            metadata: List[Dict[str, Any]],
            ids: List[Any],
        ) -> None:
            """Stub for adding documents - just succeeds silently"""
            # In a real stub, you might store these for later verification
            # but we're focusing on behavior events rather than method call tracking
            pass

        def query(
            self, collection_name: str, query_text: str, limit: int = 5
        ) -> List[Dict[str, Any]]:
            """Stub for querying - returns configured results"""
            return self._get_next_response(self._search_responses, limit)

        @staticmethod
        def _get_next_response(
            responses: List[List[Dict[str, Any]]], limit: int
        ) -> List[Dict[str, Any]]:
            """Get next configured response"""
            if isinstance(responses, list):
                # If it's a list, pop the next response
                if not responses:
                    raise Exception(
                        "No more search responses configured in nulled VectorDB"
                    )
                response = responses.pop(0)
                # Return up to 'limit' results
                return response[:limit]
            else:
                # If it's a single value, always return that (up to limit)
                return responses[:limit]


# Output tracking classes
class DocumentAdditionTracker:
    """Tracks document addition events"""

    def __init__(self, vector_db: VectorDB):
        self._data = []
        vector_db.on_document_added(self._track_event)

    def _track_event(self, event_data: Dict[str, Any]) -> None:
        self._data.append(event_data)

    @property
    def data(self) -> List[Dict[str, Any]]:
        return self._data.copy()

    def clear(self) -> List[Dict[str, Any]]:
        data = self._data.copy()
        self._data.clear()
        return data


class SearchTracker:
    """Tracks search events"""

    def __init__(self, vector_db: VectorDB):
        self._data = []
        vector_db.on_search_performed(self._track_event)

    def _track_event(self, event_data: Dict[str, Any]) -> None:
        self._data.append(event_data)

    @property
    def data(self) -> List[Dict[str, Any]]:
        return self._data.copy()

    def clear(self) -> List[Dict[str, Any]]:
        data = self._data.copy()
        self._data.clear()
        return data
