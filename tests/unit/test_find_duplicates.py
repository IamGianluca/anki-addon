from tests.fakes.domain_fakes import FakeDocumentRepository
from tests.fakes.qdrant_fakes import FakeQdrantClient, FakeSentenceTransformer

from addon.application.use_cases.note_duplicate_finder import (
    SimilarNoteFinder,
)
from addon.domain.entities.note import AddonCollection, AddonNote
from addon.domain.repositories.document_repository import (
    convert_addon_note_to_document,
)
from addon.infrastructure.persistence.qdrant_repository import (
    QdrantDocumentRepository,
)


def _point_from_note(note: AddonNote, score: float) -> dict:
    """Build a mock scored point from an AddonNote."""
    doc = convert_addon_note_to_document(note)
    return {
        "id": doc.id,
        "score": score,
        "payload": {
            "content": doc.content,
            "source": doc.source,
            "metadata": doc.metadata,
        },
    }


def test_find_possible_duplicate_notes_given_a_new_note(
    addon_collection: AddonCollection,
    addon_note1: AddonNote,
    addon_note2: AddonNote,
) -> None:
    # Given
    repository = QdrantDocumentRepository(
        FakeSentenceTransformer(),
        client=FakeQdrantClient(
            search_responses=[
                [
                    _point_from_note(addon_note2, 0.98),
                    # This result should be skipped because
                    # SimilarNoteFinder only returns the most similar
                    # note for now
                    _point_from_note(addon_note1, 0.92),
                ]
            ]
        ),
    )

    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    finder.load_collection()
    note = AddonNote(front="two", back="two")

    # When
    result = finder.find_duplicates(note=note)

    # Then
    assert result is not None
    assert len(result) == 1
    assert result[0].guid == addon_note2.guid


def test_find_duplicates_returns_empty_when_no_similar_notes(
    addon_collection: AddonCollection,
) -> None:
    # Given
    # Test the case where the collection exists but contains no documents.
    # This simulates a valid but empty vector database - we expect the finder
    # to gracefully return an empty list rather than raise an error.
    repository = QdrantDocumentRepository(
        FakeSentenceTransformer(),
        client=FakeQdrantClient(search_responses=[[]]),
    )
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    finder.load_collection()
    note = AddonNote(front="unique", back="content")

    # When
    result = finder.find_duplicates(note=note)

    # Then
    assert result == []


def test_find_duplicates_respects_max_results(
    addon_collection: AddonCollection,
    addon_note1: AddonNote,
    addon_note2: AddonNote,
    addon_note3: AddonNote,
) -> None:
    # Given - return 3 results but finder should only return the most similar
    repository = QdrantDocumentRepository(
        FakeSentenceTransformer(),
        client=FakeQdrantClient(
            search_responses=[
                [
                    _point_from_note(addon_note1, 0.99),
                    _point_from_note(addon_note2, 0.95),
                    _point_from_note(addon_note3, 0.90),
                ]
            ]
        ),
    )
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    finder.load_collection()

    # When
    result = finder.find_duplicates(note=AddonNote(front="test", back="test"))

    # Then - only most similar note returned
    assert len(result) == 1
    assert result[0].guid == addon_note1.guid


def test_find_duplicates_joins_tags_with_spaces(
    addon_collection: AddonCollection,
) -> None:
    # Given
    repository = FakeDocumentRepository()
    finder = SimilarNoteFinder(
        collection=addon_collection, repository=repository
    )
    finder.load_collection()

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
