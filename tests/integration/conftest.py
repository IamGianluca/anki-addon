import pytest
from tests.fakes.qdrant_fakes import FakeSentenceTransformer

from addon.infrastructure.persistence.qdrant_repository import (
    QdrantDocumentRepository,
)


@pytest.fixture
def encoder() -> FakeSentenceTransformer:
    """SentenceTransformer is a heavy dependency, which adds 20+ seconds just
    to load the library. To bypass that performance drag, and keep the
    integration tests relatively fast, we will use a fake object that mimic
    SentenceTransformer behavior.
    """
    return FakeSentenceTransformer()


@pytest.fixture
def repo(encoder) -> QdrantDocumentRepository:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name="docs",
        vectors_config=VectorParams(
            size=encoder.get_sentence_embedding_dimension(),
            distance=Distance.DOT,
        ),
    )
    return QdrantDocumentRepository(encoder, client=client)
