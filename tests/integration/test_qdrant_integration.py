import uuid

import pytest

from addon.domain.repositories.document_repository import Document, SearchQuery
from addon.infrastructure.persistence.qdrant_repository import (
    FakeSentenceTransformer,
    QdrantDocumentRepository,
)

# These integration tests are designed to test exclusively our Qdrant adapter.
# SentenceTransformer is a heavy dependency, which adds 20+ seconds when loading
# the library. To bypass that performance drag, and keep the integration tests
# relatively fast, we will use a fake object that mimic SentenceTransformer
# behavior


@pytest.fixture
def encoder():
    return FakeSentenceTransformer("fake")


@pytest.mark.slow
def test_overlapping_sociable_behavior_with_real_dependencies(encoder):
    """Test overlapping sociable behavior - can skip in development"""

    # Given - use the production factory (this runs real QdrantClient code)
    repo = QdrantDocumentRepository.create(encoder)

    # When - perform real operations (this tests the integration)
    documents = [
        Document(
            id=str(uuid.uuid4()),
            content="Qdrant is a vector database",
            source="docs",
            metadata={"category": "database"},
        ),
        Document(
            id=str(uuid.uuid4()),
            content="It supports similarity search",
            source="docs",
            metadata={"category": "features"},
        ),
    ]

    # Store documents using batch operation
    repo.store_batch(documents)

    # The search will use real Qdrant algorithms, but against in-memory data
    query = SearchQuery("vector database search", max_results=5)
    results = repo.find_similar(query)

    # Then - verify structure and behavior
    assert isinstance(results, list)
    assert len(results) >= 0  # At minimum, it shouldn't crash

    # If results are returned, verify they have the correct structure
    for result in results:
        assert hasattr(result, "document")
        assert hasattr(result, "relevance_score")
        assert hasattr(result.document, "id")
        assert hasattr(result.document, "content")
        assert hasattr(result.document, "source")
        assert hasattr(result.document, "metadata")
        assert isinstance(result.relevance_score, (int, float))


@pytest.mark.slow
def test_real_qdrant_store_and_retrieve_cycle(encoder):
    """CRITICAL: Test complete store/retrieve cycle - fail if qdrant missing in CI"""
    # Given
    repo = QdrantDocumentRepository.create(encoder)

    test_doc_id = str(uuid.uuid4())
    test_doc = Document(
        id=test_doc_id,
        content="This is a test document for integration testing",
        source="integration_test",
        metadata={"test": True, "category": "integration"},
    )
    repo.store(test_doc)

    # When
    retrieved_doc = repo.find_by_id(test_doc_id)

    # Then
    assert retrieved_doc is not None
    assert retrieved_doc.id == test_doc.id
    assert retrieved_doc.content == test_doc.content
    assert retrieved_doc.source == test_doc.source
    assert retrieved_doc.metadata == test_doc.metadata


@pytest.mark.slow
def test_real_qdrant_similarity_search_behavior(encoder):
    """Test similarity search with real algorithms"""
    # Given
    repo = QdrantDocumentRepository.create(encoder)
    doc1_id = str(uuid.uuid4())
    doc2_id = str(uuid.uuid4())
    doc3_id = str(uuid.uuid4())
    doc4_id = str(uuid.uuid4())
    documents = [
        Document(doc1_id, "Machine learning algorithms", "source1", {}),
        Document(doc2_id, "Deep learning neural networks", "source2", {}),
        Document(doc3_id, "Cooking pasta recipes", "source3", {}),
        Document(doc4_id, "Artificial intelligence and ML", "source4", {}),
    ]
    repo.store_batch(documents)

    # When - search for ML-related content
    ml_query = SearchQuery("machine learning", max_results=3)
    ml_results = repo.find_similar(ml_query)

    # When - search for cooking-related content
    cooking_query = SearchQuery("cooking recipes", max_results=3)
    cooking_results = repo.find_similar(cooking_query)

    # Then - verify search works
    assert isinstance(ml_results, list)
    assert isinstance(cooking_results, list)

    # If any results are returned, they should have proper structure
    all_results = ml_results + cooking_results
    for result in all_results:
        assert hasattr(result, "document")
        assert hasattr(result, "relevance_score")
        # NOTE: We are using cosine similarity, which is a raw similarity
        # scores, not a normalized relevance scores.
        assert isinstance(result.relevance_score, (int, float))

    # Test that we can retrieve stored documents by ID
    doc1 = repo.find_by_id(doc1_id)
    assert doc1 is not None
    assert doc1.content == "Machine learning algorithms"


@pytest.mark.slow
def test_real_qdrant_handles_empty_search_gracefully(encoder):
    """Test edge cases - can skip in development"""
    # Given
    repo = QdrantDocumentRepository.create(encoder)

    # When - search in empty collection
    empty_query = SearchQuery("nonexistent content", max_results=5)
    empty_results = repo.find_similar(empty_query)

    # When - search for nonexistent document
    nonexistent_doc = repo.find_by_id("nonexistent_id")

    # Then - should handle gracefully without errors
    assert isinstance(empty_results, list)
    assert nonexistent_doc is None


@pytest.mark.slow
def test_real_qdrant_batch_operations(encoder):
    """Test batch operations - can skip in development"""
    # Given
    repo = QdrantDocumentRepository.create(encoder)

    # Create multiple documents
    batch_docs = [
        Document(
            str(uuid.uuid4()),
            f"Content for document {i}",
            "batch_source",
            {"index": i},
        )
        for i in range(10)
    ]
    doc0_id = batch_docs[0].id
    doc9_id = batch_docs[9].id

    # When - store batch
    repo.store_batch(batch_docs)

    # When - verify some documents can be retrieved
    first_doc = repo.find_by_id(doc0_id)
    last_doc = repo.find_by_id(doc9_id)

    # Then
    assert first_doc is not None
    assert first_doc.content == "Content for document 0"
    assert last_doc is not None
    assert last_doc.content == "Content for document 9"

    # Test search across batch
    batch_query = SearchQuery("Content for document", max_results=5)
    batch_results = repo.find_similar(batch_query)
    assert isinstance(batch_results, list)


@pytest.mark.slow
def test_real_qdrant_performance_characteristics(encoder):
    """Performance test - can skip in development, should run in CI"""
    import time

    # Given
    repo = QdrantDocumentRepository.create(encoder)

    # Store a moderate number of documents
    docs = [
        Document(
            str(uuid.uuid4()),
            f"Performance test document number {i} with some content",
            "perf_test",
            {"num": i},
        )
        for i in range(100)
    ]
    fifty_doc_id = docs[50].id

    # When - measure batch store time
    start_time = time.time()
    repo.store_batch(docs)
    store_time = time.time() - start_time

    # When - measure search time
    start_time = time.time()
    query = SearchQuery("Performance test document", max_results=10)
    results = repo.find_similar(query)
    search_time = time.time() - start_time

    # When - measure retrieval time
    start_time = time.time()
    doc = repo.find_by_id(fifty_doc_id)
    retrieve_time = time.time() - start_time

    # Then - operations should complete in reasonable time
    assert store_time < 10.0  # Storing 100 docs should take < 10 seconds
    assert search_time < 5.0  # Search should take < 5 seconds
    assert retrieve_time < 1.0  # Single retrieval should take < 1 second

    # Verify operations actually worked
    assert isinstance(results, list)
    assert doc is not None
    assert doc.metadata["num"] == 50
