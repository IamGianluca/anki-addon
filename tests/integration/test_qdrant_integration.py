import uuid

import pytest

from addon.domain.repositories.document_repository import Document, SearchQuery

"""
Narrow integration tests for QdrantDocumentRepository.

These tests focus exclusively on Qdrant interaction mechanics:
- Collection creation
- Document storage
- Document retrieval
- Basic search functionality

Complex workflows, edge cases, and performance tests should go in e2e tests.
"""


@pytest.mark.slow
def test_repository_creation(repo):
    # Then
    assert repo is not None


@pytest.mark.slow
def test_store_single_document(repo):
    # Given
    doc_id = str(uuid.uuid4())

    document = Document(
        id=doc_id,
        content="Test document content",
        source="test_source",
        metadata={"category": "test"},
    )
    repo.store(document)

    # When
    retrieved = repo.find_by_id(doc_id)

    # Then
    assert retrieved is not None
    assert retrieved.id == doc_id
    assert retrieved.content == "Test document content"
    assert retrieved.source == "test_source"
    assert retrieved.metadata == {"category": "test"}


@pytest.mark.slow
def test_store_batch_documents(repo):
    # Given
    documents = [
        Document(
            id=str(uuid.uuid4()),
            content=f"Document {i} content",
            source="batch_test",
            metadata={"index": i},
        )
        for i in range(3)
    ]

    # When
    repo.store_batch(documents)

    # Then
    for doc in documents:
        retrieved = repo.find_by_id(doc.id)
        assert retrieved is not None
        assert retrieved.content == doc.content


@pytest.mark.slow
def test_find_by_id_nonexistent(repo):
    # Given
    from addon.domain.repositories.document_repository import (
        DocumentNotFoundError,
    )

    # When/Then
    with pytest.raises(DocumentNotFoundError) as exc_info:
        repo.find_by_id("nonexistent_id")

    assert "nonexistent_id" in str(exc_info.value)


@pytest.mark.slow
def test_basic_similarity_search(repo):
    # Given
    document = Document(
        id=str(uuid.uuid4()),
        content="Vector database search functionality",
        source="search_test",
        metadata={},
    )
    repo.store(document)

    query = SearchQuery("database search", max_results=5)

    # When
    results = repo.find_similar(query)

    # Then
    assert isinstance(results, list)
    for result in results:
        assert hasattr(result, "document")
        assert hasattr(result, "relevance_score")
        assert isinstance(result.relevance_score, (int, float))
