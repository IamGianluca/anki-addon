from addon.application.use_cases.note_duplicate_finder import (
    SimilarNoteFinder,
)
from addon.domain.entities.note import AddonNote
from addon.domain.repositories.document_repository import (
    FakeDocumentRepository,
    SearchResult,
    convert_addon_note_to_document,
)
from addon.infrastructure.persistence.qdrant_repository import (
    QdrantDocumentRepository,
)


def test_find_possible_duplicate_notes_given_a_new_note(
    addon_collection, addon_note1, addon_note2
):
    # Given
    repository = QdrantDocumentRepository.create_null(
        search_responses=[
            [
                SearchResult(
                    document=convert_addon_note_to_document(addon_note2),
                    relevance_score=0.98,
                ),
                # This result should be skipped because SimilarNoteFinder only return
                # the most similar note for now
                SearchResult(
                    document=convert_addon_note_to_document(addon_note1),
                    relevance_score=0.92,
                ),
            ]
        ],
    )

    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    note = AddonNote(front="two", back="two")

    # When
    result = finder.find_duplicates(note=note)

    # Then
    assert result is not None
    assert len(result) == 1
    assert result[0].guid == addon_note2.guid


def test_find_duplicates_returns_empty_when_no_similar_notes(addon_collection):
    # Given
    # Test the case where the collection exists but contains no documents.
    # This simulates a valid but empty vector database - we expect the finder
    # to gracefully return an empty list rather than raise an error.
    repository = QdrantDocumentRepository.create_null(
        search_responses=[[]],  # No search results returned
        stored_documents=[],  # Empty collection
    )
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    note = AddonNote(front="unique", back="content")

    # When
    result = finder.find_duplicates(note=note)

    # Then
    assert result == []


def test_find_duplicates_respects_max_results(
    addon_collection, addon_note1, addon_note2, addon_note3
):
    # Given - return 3 results but finder should only return the most similar
    repository = QdrantDocumentRepository.create_null(
        search_responses=[
            [
                SearchResult(
                    convert_addon_note_to_document(addon_note1), 0.99
                ),
                SearchResult(
                    convert_addon_note_to_document(addon_note2), 0.95
                ),
                SearchResult(
                    convert_addon_note_to_document(addon_note3), 0.90
                ),
            ]
        ]
    )
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )

    # When
    result = finder.find_duplicates(note=AddonNote(front="test", back="test"))

    # Then - only most similar note returned
    assert len(result) == 1
    assert result[0].guid == addon_note1.guid


def test_find_duplicates_joins_tags_with_spaces(addon_collection):
    # Given
    repository = FakeDocumentRepository()
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )

    # When - search with multiple tags
    note = AddonNote(
        front="test", back="answer", tags=["python", "programming"]
    )
    finder.find_duplicates(note=note)

    # Then - verify tags are space-separated in query, not concatenated
    assert len(repository.captured_queries) == 1
    query_text = repository.captured_queries[0]
    assert "python programming" in query_text
    assert "pythonprogramming" not in query_text
