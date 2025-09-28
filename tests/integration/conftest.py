import pytest

from addon.infrastructure.persistence.qdrant_repository import (
    FakeSentenceTransformer,
    QdrantDocumentRepository,
)


@pytest.fixture
def encoder():
    """SentenceTransformer is a heavy dependency, which adds 20+ seconds just
    to load the library. To bypass that performance drag, and keep the
    integration tests relatively fast, we will use a fake object that mimic
    SentenceTransformer behavior.
    """
    return FakeSentenceTransformer("fake")


@pytest.fixture
def repo(encoder):
    repo = QdrantDocumentRepository.create(encoder)
    return repo
