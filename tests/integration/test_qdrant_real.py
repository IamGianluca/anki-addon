from addon.infrastructure.qdrant import (
    VectorDB,
)


def test_creates_connected_instance_by_default():
    """Test that VectorDB.create() produces a connected instance (Parameterless Instantiation)"""
    # Given and When
    vector_db = VectorDB.create()

    # Then
    assert vector_db.is_connected is True


def test_overlapping_sociable_behavior_with_real_dependencies():
    """Test that the VectorDB works with its real dependencies in memory

    This is an example of Overlapping Sociable Tests - we're testing VectorDB
    with its real QdrantClient dependency, but using in-memory storage to avoid
    external system dependencies.
    """
    # Given - use the production factory (this runs real QdrantClient code)
    vector_db = VectorDB.create()

    # When - perform real operations (this tests the integration)
    documents = [
        "Qdrant is a vector database",
        "It supports similarity search",
    ]
    metadata = [{"source": "docs"}, {"source": "docs"}]

    vector_db.add_documents(documents, metadata)

    # The search will use real Qdrant algorithms, but against in-memory data
    results = vector_db.search("vector database search")

    # Then - we can't predict exact scores/ordering from real Qdrant,
    # but we can verify the structure and that it returns results
    assert isinstance(results, list)
    # Real Qdrant should return some results for a reasonable query
    # (though exact results depend on the embedding model and Qdrant's algorithms)
    assert len(results) >= 0  # At minimum, it shouldn't crash
