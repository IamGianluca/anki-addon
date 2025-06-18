from typing import Any, Dict, List, Optional

import pytest

from addon.infrastructure.qdrant import (
    COLLECTION_NAME,
    VectorDB,
)


# Helper function for Signature Shielding
def create_vector_db_for_test(
    search_responses: Optional[List[List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """Signature Shielding helper - creates VectorDB with tracking"""
    vector_db = VectorDB.create_null(search_responses=search_responses)
    document_tracker = vector_db.track_document_additions()
    search_tracker = vector_db.track_searches()

    return {
        "vector_db": vector_db,
        "document_tracker": document_tracker,
        "search_tracker": search_tracker,
    }


def test_null_instance_is_connected_by_default():
    """Test that VectorDB.create_null() produces a connected instance
    (Parameterless Instantiation)
    """
    # When
    vector_db = VectorDB.create_null()

    # Then
    assert vector_db.is_connected is True


def test_search_returns_configured_results(first_response, second_response):
    """Test search returns the configured responses"""
    # Given
    expected_results = [first_response, second_response]
    vector_db = VectorDB.create_null(search_responses=[expected_results])

    # When
    actual_results = vector_db.search("test query")

    # Then
    assert actual_results == expected_results


def test_search_respects_limit_parameter(
    first_response, second_response, third_response
):
    """Test that search limit parameter controls number of results returned"""
    # Given
    all_responses = [first_response, second_response, third_response]
    vector_db = VectorDB.create_null(search_responses=[all_responses])

    # When
    limited_results = vector_db.search("test query", limit=2)

    # Then
    assert len(limited_results) == 2
    assert limited_results[0]["id"] == "doc_1"
    assert limited_results[1]["id"] == "doc_2"


def test_multiple_searches_use_sequential_responses(
    first_response, second_response
):
    """Test that multiple searches consume configured responses in order"""
    # Given
    vector_db = VectorDB.create_null(
        search_responses=[[first_response], [second_response]]
    )

    # When
    first_result = vector_db.search("first query")
    second_result = vector_db.search("second query")

    # Then
    assert first_result == [first_response]
    assert second_result == [second_response]


def test_search_tracking_records_behavior_events(
    first_response, second_response
):
    """Test that search tracking captures behavior events, not method calls"""
    # Given
    search_responses = [[first_response], [second_response]]
    test_setup = create_vector_db_for_test(search_responses)
    vector_db = test_setup["vector_db"]
    search_tracker = test_setup["search_tracker"]

    # When
    vector_db.search("my test query", limit=3)
    vector_db.search("another query", limit=5)

    # Then
    search_events = search_tracker.data
    assert len(search_events) == 2

    # First search event
    first_event = search_events[0]
    assert first_event["collection_name"] == COLLECTION_NAME
    assert first_event["query_text"] == "my test query"
    assert first_event["limit"] == 3
    assert first_event["result_count"] == 1  # Default response has 1 result

    # Second search event
    second_event = search_events[1]
    assert second_event["query_text"] == "another query"
    assert second_event["limit"] == 5


def test_document_addition_tracking_records_behavior_events():
    """Test that document addition tracking captures behavior events"""
    # Given
    test_setup = create_vector_db_for_test()
    vector_db = test_setup["vector_db"]
    document_tracker = test_setup["document_tracker"]

    # When
    documents = ["Doc 1", "Doc 2", "Doc 3"]
    metadata = [{"type": "test"}, {"type": "test"}, {"type": "test"}]
    custom_ids = ["id_1", "id_2", "id_3"]

    vector_db.add_documents(documents, metadata, custom_ids)

    # Then
    doc_events = document_tracker.data
    assert len(doc_events) == 1

    event = doc_events[0]
    assert event["collection_name"] == COLLECTION_NAME
    assert event["document_count"] == 3
    assert event["ids"] == custom_ids


def test_document_addition_generates_ids_when_none_provided():
    """Test that document addition generates IDs when none are provided"""
    # Given
    test_setup = create_vector_db_for_test()
    vector_db = test_setup["vector_db"]
    document_tracker = test_setup["document_tracker"]

    # When
    vector_db.add_documents(
        ["Doc 1", "Doc 2"], [{"type": "test"}, {"type": "test"}]
    )

    # Then - check that IDs were generated
    events = document_tracker.data
    assert len(events) == 1

    generated_ids = events[0]["ids"]
    assert len(generated_ids) == 2
    assert all(isinstance(id_val, str) for id_val in generated_ids)
    assert generated_ids[0] != generated_ids[1]  # IDs should be unique


def test_output_tracking_can_be_cleared(
    first_response, second_response, third_response
):
    """Test that output trackers can be cleared and return previous data"""
    # Given
    test_setup = create_vector_db_for_test(
        [[first_response], [second_response], [third_response]]
    )
    vector_db = test_setup["vector_db"]
    search_tracker = test_setup["search_tracker"]

    # When - perform some operations
    vector_db.search("first query")
    vector_db.search("second query")

    # When - Clear and get the data
    cleared_data = search_tracker.clear()

    # Then - cleared data should contain previous events
    assert len(cleared_data) == 2
    assert cleared_data[0]["query_text"] == "first query"
    assert cleared_data[1]["query_text"] == "second query"

    # Tracker should now be empty
    assert len(search_tracker.data) == 0

    # When - New operations should start fresh tracking
    vector_db.search("new query")

    # Then
    assert len(search_tracker.data) == 1
    assert search_tracker.data[0]["query_text"] == "new query"


def test_search_fails_when_not_connected():
    """Test that operations fail gracefully when not connected"""
    # This would require adding a way to create a disconnected instance
    # For now, we'll test the error handling structure

    # Given - create a VectorDB and manually set connection to False
    vector_db = VectorDB.create_null()
    vector_db.is_connected = False  # Simulate disconnection

    # When and Then
    with pytest.raises(RuntimeError, match="VectorDB is not connected"):
        vector_db.search("test query")


def test_add_documents_fails_when_not_connected():
    """Test that document addition fails when not connected"""
    # Given - create a VectorDB and manually set connection to False
    vector_db = VectorDB.create_null()
    vector_db.is_connected = False  # Simulate disconnection

    # When and Then
    with pytest.raises(RuntimeError, match="VectorDB is not connected"):
        vector_db.add_documents(["test doc"], [{"type": "test"}])


def test_exhausting_configured_responses_raises_error(first_response):
    """Test that using more searches than configured responses raises an error"""
    # Given - configure only one response
    vector_db = VectorDB.create_null(search_responses=[[first_response]])

    # When and Then - first search should work
    first_result = vector_db.search("first query")
    assert len(first_result) == 1

    # When and Then - Second search should raise an error
    with pytest.raises(Exception, match="No more search responses configured"):
        vector_db.search("second query")


def test_signature_shielding_helper_sets_up_complete_test_environment():
    """Test that the signature shielding helper creates a complete test setup"""
    # Given
    custom_responses = [
        [{"id": "custom", "score": 0.99, "payload": {"text": "Custom result"}}]
    ]

    # When
    test_setup = create_vector_db_for_test(search_responses=custom_responses)

    # Then - helper should return all necessary components
    assert "vector_db" in test_setup
    assert "document_tracker" in test_setup
    assert "search_tracker" in test_setup

    # Components should be properly connected
    vector_db = test_setup["vector_db"]
    search_tracker = test_setup["search_tracker"]

    # Test that tracking works
    result = vector_db.search("test")
    assert len(search_tracker.data) == 1
    assert result[0]["id"] == "custom"


def test_complete_workflow_with_behavior_tracking(
    first_response, second_response, third_response
):
    """Integration test showing a complete workflow: add documents, search, verify all behavior is tracked"""
    # Given - set up configured responses for predictable testing
    search_responses = [
        [first_response, second_response],
        [third_response],
    ]

    test_setup = create_vector_db_for_test(search_responses=search_responses)
    vector_db = test_setup["vector_db"]
    document_tracker = test_setup["document_tracker"]
    search_tracker = test_setup["search_tracker"]

    # When - perform a complete workflow
    # 1. Add some documents
    vector_db.add_documents(
        documents=["First document", "Second document"],
        metadata=[{"category": "test"}, {"category": "test"}],
        ids=["doc1", "doc2"],
    )

    # 2. Perform searches
    first_search_results = vector_db.search("find relevant documents", limit=2)
    second_search_results = vector_db.search("different query", limit=1)

    # Then - verify the complete behavior
    # Document addition behavior
    doc_events = document_tracker.data
    assert len(doc_events) == 1
    assert doc_events[0]["document_count"] == 2
    assert doc_events[0]["ids"] == ["doc1", "doc2"]

    # Search behavior
    search_events = search_tracker.data
    assert len(search_events) == 2

    # First search
    assert search_events[0]["query_text"] == "find relevant documents"
    assert search_events[0]["limit"] == 2
    assert search_events[0]["result_count"] == 2

    # Second search
    assert search_events[1]["query_text"] == "different query"
    assert search_events[1]["limit"] == 1
    assert search_events[1]["result_count"] == 1

    # Search results match configured responses
    assert first_search_results == search_responses[0]
    assert second_search_results == search_responses[1]


def test_default_search_responses_when_none_configured():
    """Test that VectorDB provides sensible defaults when no search responses
    are configured
    """
    # Given - create null instance without specifying responses
    vector_db = VectorDB.create_null()

    # When
    result = vector_db.search("any query")

    # Then - should get the default response
    assert len(result) == 1
    assert result[0]["id"] == "null_result_1"
    assert result[0]["score"] == 0.95
    assert "payload" in result[0]
    assert result[0]["payload"]["source"] == "null_source"


def test_search_with_empty_response_list():
    """Test behavior when an empty response list is configured"""
    # Given
    vector_db = VectorDB.create_null(search_responses=[[]])  # Empty response

    # When
    result = vector_db.search("query")

    # Then
    assert result == []


def test_multiple_document_additions_tracked_separately():
    """Test that multiple document addition calls are tracked as separate events"""
    # Given
    test_setup = create_vector_db_for_test()
    vector_db = test_setup["vector_db"]
    document_tracker = test_setup["document_tracker"]

    # When - add documents in multiple calls
    vector_db.add_documents(["Doc 1"], [{"type": "first"}], ["id1"])
    vector_db.add_documents(
        ["Doc 2", "Doc 3"],
        [{"type": "second"}, {"type": "second"}],
        ["id2", "id3"],
    )

    # Then - should have two separate events
    events = document_tracker.data
    assert len(events) == 2

    # First addition
    assert events[0]["document_count"] == 1
    assert events[0]["ids"] == ["id1"]

    # Second addition
    assert events[1]["document_count"] == 2
    assert events[1]["ids"] == ["id2", "id3"]
