"""Protocols describing external APIs our addon depends on.

Defines the minimal contract our code needs from dependencies we don't control
(Anki, Qdrant, etc.). Production code depends on these, not on concrete
implementations. mypy verifies both real and fake implementations satisfy them.
"""

from __future__ import annotations

from typing import Any, Protocol


class ConfigProvider(Protocol):
    """Minimal contract for reading addon configuration from Anki's addon manager."""

    def getConfig(self, module: str) -> dict[str, Any] | None: ...


class HttpResponse(Protocol):
    """Minimal response contract that HTTP clients must produce."""

    @property
    def status_code(self) -> int: ...

    def json(self) -> dict: ...

    @property
    def text(self) -> str: ...


class HttpClient(Protocol):
    """Minimal HTTP client contract for making POST requests.

    Both real adapters (requests, httpx) and test fakes implement this port.
    """

    def post(self, url: str, json: dict | None = None) -> HttpResponse: ...


class EmbeddingModel(Protocol):
    """Minimal contract for a text embedding model."""

    def encode(self, text: str) -> list[int]: ...

    def get_sentence_embedding_dimension(self) -> int: ...


class QdrantQueryResponse(Protocol):
    """Minimal response from Qdrant query_points."""

    @property
    def points(self) -> list[object]: ...


class QdrantDriver(Protocol):
    """Minimal Qdrant client contract for document storage and retrieval.

    Both the real qdrant-client library and test fakes implement this port.
    """

    def get_collection(
        self, collection_name: str, **kwargs: object
    ) -> object: ...

    def create_collection(
        self, collection_name: str, vectors_config: object, **kwargs: object
    ) -> object: ...

    def upsert(
        self, collection_name: str, points: object, **kwargs: object
    ) -> None: ...

    def query_points(
        self, collection_name: str, query: object, limit: int, **kwargs: object
    ) -> QdrantQueryResponse: ...

    def retrieve(
        self, collection_name: str, ids: list[str], **kwargs: object
    ) -> list[object]: ...
