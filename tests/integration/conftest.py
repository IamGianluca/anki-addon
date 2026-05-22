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
    repo = QdrantDocumentRepository.create(encoder)
    return repo
