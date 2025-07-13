import pytest

from addon.domain.repositories.document_repository import (
    Document,
    SearchQuery,
    SearchResult,
)
from addon.infrastructure.persistence.qdrant_repository import (
    QdrantDocumentRepository,
)


# Fixtures for test data
@pytest.fixture
def sample_document():
    return Document(
        id="doc_1",
        content="Sample document content",
        source="test_source",
        metadata={"category": "test"},
    )


@pytest.fixture
def first_response():
    doc = Document(
        id="doc_1",
        content="First document content",
        source="source_1",
        metadata={"type": "test"},
    )
    return SearchResult(document=doc, relevance_score=0.95)


@pytest.fixture
def second_response():
    doc = Document(
        id="doc_2",
        content="Second document content",
        source="source_2",
        metadata={"type": "test"},
    )
    return SearchResult(document=doc, relevance_score=0.85)


@pytest.fixture
def third_response():
    doc = Document(
        id="doc_3",
        content="Third document content",
        source="source_3",
        metadata={"type": "test"},
    )
    return SearchResult(document=doc, relevance_score=0.75)


def test_search_returns_configured_results(first_response, second_response):
    """Test search returns the configured responses"""
    # Given
    expected_results = [first_response, second_response]
    repo = QdrantDocumentRepository.create_null(
        search_responses=[expected_results]
    )
    search_query = SearchQuery("test_query")

    # When
    actual_results = repo.find_similar(search_query)

    # Then
    assert actual_results == expected_results


def test_search_respects_limit_parameter(
    first_response, second_response, third_response
):
    """Test that search limit parameter controls number of results returned"""
    # Given
    all_responses = [first_response, second_response, third_response]
    repo = QdrantDocumentRepository.create_null(
        search_responses=[all_responses]
    )

    # When
    query = SearchQuery("test query", max_results=2)
    limited_results = repo.find_similar(query)

    # Then
    assert len(limited_results) == 2
    assert limited_results[0].document.id == "doc_1"
    assert limited_results[1].document.id == "doc_2"


def test_multiple_searches_use_sequential_responses(
    first_response, second_response
):
    """Test that multiple searches consume configured responses in order"""
    # Given
    repo = QdrantDocumentRepository.create_null(
        search_responses=[[first_response], [second_response]]
    )

    # When
    first_query = SearchQuery("first query")
    second_query = SearchQuery("second query")

    first_result = repo.find_similar(first_query)
    second_result = repo.find_similar(second_query)

    # Then
    assert first_result == [first_response]
    assert second_result == [second_response]


def test_store_document_succeeds():
    """Test that storing a document works without errors"""
    # Given
    repo = QdrantDocumentRepository.create_null()
    document = Document(
        id="test_doc_1",
        content="Test document content",
        source="test",
        metadata={"category": "test"},
    )

    # When & Then - should not raise an exception
    repo.store(document)


def test_store_batch_documents_succeeds():
    """Test that batch storing documents works"""
    # Given
    repo = QdrantDocumentRepository.create_null()
    documents = [
        Document(id="doc1", content="Content 1", source="test", metadata={}),
        Document(id="doc2", content="Content 2", source="test", metadata={}),
        Document(id="doc3", content="Content 3", source="test", metadata={}),
    ]

    # When & Then - should not raise an exception
    repo.store_batch(documents)


def test_store_batch_with_empty_list():
    """Test that storing empty list of documents handles gracefully"""
    # Given
    repo = QdrantDocumentRepository.create_null()

    # When & Then - should not raise an exception
    repo.store_batch([])


def test_find_by_id_returns_stored_document():
    """Test that find_by_id can retrieve a stored document"""
    # Given
    repo = QdrantDocumentRepository.create_null()
    document = Document(
        id="test_doc_1",
        content="Test content",
        source="test",
        metadata={"key": "value"},
    )

    # When
    repo.store(document)
    retrieved = repo.find_by_id("test_doc_1")

    # Then
    assert retrieved is not None
    assert retrieved.id == document.id
    assert retrieved.content == document.content
    assert retrieved.source == document.source
    assert retrieved.metadata == document.metadata


def test_find_by_id_returns_none_for_nonexistent_document():
    """Test that find_by_id returns None for documents that don't exist"""
    # Given
    repo = QdrantDocumentRepository.create_null()

    # When
    result = repo.find_by_id("nonexistent_id")

    # Then
    assert result is None


def test_exhausting_configured_responses_returns_empty_list(first_response):
    """Test that using more searches than configured responses returns empty list"""
    # Given - configure only one response
    repo = QdrantDocumentRepository.create_null(
        search_responses=[[first_response]]
    )

    # When - first search should work
    first_query = SearchQuery("first query")
    first_result = repo.find_similar(first_query)
    assert len(first_result) == 1

    # When - second search should return empty list (no more responses configured)
    second_query = SearchQuery("second query")
    second_result = repo.find_similar(second_query)

    # Then
    assert second_result == []


def test_default_search_responses_when_none_configured():
    """Test that QdrantDocumentRepository provides sensible defaults when no search responses are configured"""
    # Given - create null instance without specifying responses
    repo = QdrantDocumentRepository.create_null()

    # When
    query = SearchQuery("any query")
    result = repo.find_similar(query)

    # Then - should get the default response
    assert len(result) == 1
    assert result[0].document.id == "null_doc_1"
    assert result[0].relevance_score == 0.95
    assert result[0].document.content == "Default null content"
    assert result[0].document.source == "null_source"


def test_search_with_empty_response_list():
    """Test behavior when an empty response list is configured"""
    # Given
    repo = QdrantDocumentRepository.create_null(search_responses=[[]])

    # When
    query = SearchQuery("test query")
    result = repo.find_similar(query)

    # Then
    assert result == []


def test_domain_exceptions_are_raised_for_errors():
    """Test that domain exceptions are raised when infrastructure fails"""
    # This test would require mocking the client to raise exceptions
    # For now, we test that the methods exist and can be called
    repo = QdrantDocumentRepository.create_null()

    # These should not raise exceptions with the stubbed client
    document = Document("test", "content", "source", {})
    repo.store(document)

    query = SearchQuery("test")
    results = repo.find_similar(query)
    assert isinstance(results, list)


def test_complete_workflow():
    """Integration test showing a complete workflow"""
    # Given
    doc1 = Document("id1", "First document", "source1", {"type": "test"})
    doc2 = Document("id2", "Second document", "source2", {"type": "test"})

    search_result1 = SearchResult(doc1, 0.95)
    search_result2 = SearchResult(doc2, 0.85)

    repo = QdrantDocumentRepository.create_null(
        search_responses=[[search_result1, search_result2]]
    )

    # When - store documents
    repo.store_batch([doc1, doc2])

    # When - search for documents
    query = SearchQuery("test query", max_results=2)
    results = repo.find_similar(query)

    # When - retrieve by ID
    retrieved = repo.find_by_id("id1")

    # Then
    assert len(results) == 2
    assert results[0].document.id == "id1"
    assert results[1].document.id == "id2"

    assert retrieved is not None
    assert retrieved.id == "id1"


def test_search_query_validation():
    """Test SearchQuery domain object validation"""
    # Test valid query
    query = SearchQuery("test query", max_results=5)
    assert query.text == "test query"
    assert query.max_results == 5

    # Test default max_results
    query2 = SearchQuery("another query")
    assert query2.max_results == 5


def test_document_domain_object():
    """Test Document domain object"""
    doc = Document(
        id="test_id",
        content="Test content",
        source="test_source",
        metadata={"key": "value"},
    )

    assert doc.id == "test_id"
    assert doc.content == "Test content"
    assert doc.source == "test_source"
    assert doc.metadata == {"key": "value"}


def test_search_result_domain_object():
    """Test SearchResult domain object"""
    doc = Document("id", "content", "source", {})
    result = SearchResult(document=doc, relevance_score=0.85)

    assert result.document == doc
    assert result.relevance_score == 0.85
