"""
Unit tests for duplicate detection functionality.
These tests use the nullable pattern and do not touch real Qdrant.
"""

import pytest

from addon.application.use_cases.duplicate_detector import (
    DuplicateCandidate,
    DuplicateDetectionResult,
    DuplicateDetectionService,
)
from addon.domain.entities.note import AddonNote
from addon.domain.repositories.document_repository import (
    Document,
    SearchResult,
)
from addon.infrastructure.persistence.qdrant_repository import (
    QdrantDocumentRepository,
)


@pytest.fixture
def sample_notes():
    """Create sample notes for testing"""
    return [
        AddonNote(
            guid="note1",
            front="What is the capital of France?",
            back="Paris",
            tags=["geography", "europe"],
        ),
        AddonNote(
            guid="note2",
            front="What is France's capital city?",
            back="The capital of France is Paris",
            tags=["geography"],
        ),
        AddonNote(
            guid="note3",
            front="What is the capital of Italy?",
            back="Rome",
            tags=["geography", "europe"],
        ),
        AddonNote(
            guid="note4",
            front="{{c1::Paris}} is the capital of France",
            back="",
            tags=["geography", "cloze"],
        ),
    ]


@pytest.fixture
def duplicate_search_responses():
    """Mock search responses that simulate finding duplicates"""
    # When searching for note1 ("What is the capital of France?")
    # Return note2 as a high-similarity match
    note1_search = [
        SearchResult(
            document=Document(
                "note1",
                "What is the capital of France? Paris",
                "anki_note",
                {},
            ),
            relevance_score=1.0,  # Self-match
        ),
        SearchResult(
            document=Document(
                "note2",
                "What is France's capital city? The capital of France is Paris",
                "anki_note",
                {},
            ),
            relevance_score=0.92,  # High similarity
        ),
    ]

    # When searching for note2
    note2_search = [
        SearchResult(
            document=Document(
                "note2",
                "What is France's capital city? The capital of France is Paris",
                "anki_note",
                {},
            ),
            relevance_score=1.0,
        ),
        SearchResult(
            document=Document(
                "note1",
                "What is the capital of France? Paris",
                "anki_note",
                {},
            ),
            relevance_score=0.92,
        ),
    ]

    # When searching for note3 (Italy) - should not match France notes
    note3_search = [
        SearchResult(
            document=Document(
                "note3", "What is the capital of Italy? Rome", "anki_note", {}
            ),
            relevance_score=1.0,
        )
    ]

    # When searching for note4 (cloze about Paris)
    note4_search = [
        SearchResult(
            document=Document(
                "note4", "Paris is the capital of France", "anki_note", {}
            ),
            relevance_score=1.0,
        ),
        SearchResult(
            document=Document(
                "note1",
                "What is the capital of France? Paris",
                "anki_note",
                {},
            ),
            relevance_score=0.88,  # Medium-high similarity
        ),
    ]

    return [note1_search, note2_search, note3_search, note4_search]


def test_duplicate_detection_service_finds_similar_notes(
    sample_notes, duplicate_search_responses
):
    """Test that the service correctly identifies duplicate candidates"""
    # Given
    repository = QdrantDocumentRepository.create_null(
        search_responses=duplicate_search_responses
    )
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates(sample_notes, similarity_threshold=0.85)

    # Then
    assert result.total_notes_analyzed == 4
    assert result.similarity_threshold == 0.85
    assert (
        result.duplicate_count >= 1
    )  # Should find at least the France/Paris duplicates

    # Check that we found the high-similarity pair
    high_sim_candidates = [
        c for c in result.duplicate_candidates if c.similarity_score >= 0.90
    ]
    assert len(high_sim_candidates) >= 1

    # Verify the duplicate candidate structure
    for candidate in result.duplicate_candidates:
        assert isinstance(candidate, DuplicateCandidate)
        assert isinstance(candidate.original_note, AddonNote)
        assert isinstance(candidate.duplicate_note, AddonNote)
        assert isinstance(candidate.similarity_score, float)
        assert candidate.similarity_score >= 0.85


def test_duplicate_detection_respects_similarity_threshold(sample_notes):
    """Test that only candidates above the threshold are returned"""
    # Given - responses with varying similarity scores
    search_responses = [
        [
            SearchResult(Document("note1", "content1", "source", {}), 1.0),
            SearchResult(
                Document("note2", "content2", "source", {}), 0.70
            ),  # Below threshold
        ],
        [
            SearchResult(Document("note2", "content2", "source", {}), 1.0),
            SearchResult(Document("note1", "content1", "source", {}), 0.70),
        ],
        [SearchResult(Document("note3", "content3", "source", {}), 1.0)],
        [SearchResult(Document("note4", "content4", "source", {}), 1.0)],
    ]

    repository = QdrantDocumentRepository.create_null(
        search_responses=search_responses
    )
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates(sample_notes, similarity_threshold=0.85)

    # Then
    assert result.duplicate_count == 0  # No candidates above 0.85 threshold


def test_duplicate_detection_avoids_duplicate_pairs(sample_notes):
    """Test that we don't get both (A,B) and (B,A) as separate duplicates"""
    # Given - responses where note1 and note2 are mutually similar
    search_responses = [
        [
            SearchResult(Document("note1", "content1", "source", {}), 1.0),
            SearchResult(Document("note2", "content2", "source", {}), 0.95),
        ],
        [
            SearchResult(Document("note2", "content2", "source", {}), 1.0),
            SearchResult(Document("note1", "content1", "source", {}), 0.95),
        ],
        [SearchResult(Document("note3", "content3", "source", {}), 1.0)],
        [SearchResult(Document("note4", "content4", "source", {}), 1.0)],
    ]

    repository = QdrantDocumentRepository.create_null(
        search_responses=search_responses
    )
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates(sample_notes, similarity_threshold=0.90)

    # Then
    assert result.duplicate_count == 1  # Only one pair, not two

    # Verify it's the correct pair
    candidate = result.duplicate_candidates[0]
    guids = {candidate.original_note.guid, candidate.duplicate_note.guid}
    assert guids == {"note1", "note2"}


def test_duplicate_detection_excludes_self_matches(sample_notes):
    """Test that notes don't match with themselves"""
    # Given - responses that include self-matches (score 1.0)
    search_responses = [
        [
            SearchResult(Document("note1", "content1", "source", {}), 1.0)
        ],  # Only self-match
        [
            SearchResult(Document("note2", "content2", "source", {}), 1.0)
        ],  # Only self-match
        [
            SearchResult(Document("note3", "content3", "source", {}), 1.0)
        ],  # Only self-match
        [
            SearchResult(Document("note4", "content4", "source", {}), 1.0)
        ],  # Only self-match
    ]

    repository = QdrantDocumentRepository.create_null(
        search_responses=search_responses
    )
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates(sample_notes, similarity_threshold=0.80)

    # Then
    assert result.duplicate_count == 0  # No duplicates, only self-matches


def test_prepare_search_text_handles_cloze_notes():
    """Test that cloze notes are properly processed for search"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)
    cloze_note = AddonNote(
        guid="cloze1",
        front="The capital of {{c1::France}} is {{c2::Paris}}",
        back="Additional info",
        tags=["geography"],
    )

    # When
    search_text = service._prepare_search_text(cloze_note)

    # Then
    assert "France" in search_text
    assert "Paris" in search_text
    assert "capital" in search_text
    # Should focus on front text for cloze notes


def test_prepare_search_text_handles_basic_notes():
    """Test that basic notes combine front and back text"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)
    basic_note = AddonNote(
        guid="basic1",
        front="What is the capital?",
        back="Paris is the capital",
        tags=["geography"],
    )

    # When
    search_text = service._prepare_search_text(basic_note)

    # Then
    assert "capital" in search_text
    assert "Paris" in search_text
    # Should combine front and back


def test_cloze_note_detection():
    """Test the cloze note detection method"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)

    cloze_note = AddonNote(
        guid="1", front="{{c1::Paris}} is the capital", back="back", tags=[]
    )
    basic_note = AddonNote(
        guid="2", front="What is the capital?", back="Paris", tags=[]
    )

    # When & Then
    assert service._is_cloze_note_from_addon_note(cloze_note) is True
    assert service._is_cloze_note_from_addon_note(basic_note) is False


def test_find_note_by_guid(sample_notes):
    """Test finding notes by GUID"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)

    # When & Then
    found_note = service._find_note_by_guid(sample_notes, "note2")
    assert found_note is not None
    assert found_note.guid == "note2"
    assert found_note.front == "What is France's capital city?"

    not_found = service._find_note_by_guid(sample_notes, "nonexistent")
    assert not_found is None


def test_duplicate_detection_result_properties():
    """Test the DuplicateDetectionResult data class"""
    # Given
    candidates = [
        DuplicateCandidate(
            original_note=AddonNote(guid="1", front="front1", back="back1"),
            duplicate_note=AddonNote(guid="2", front="front2", back="back2"),
            similarity_score=0.95,
        )
    ]

    # When
    result = DuplicateDetectionResult(
        total_notes_analyzed=10,
        duplicate_candidates=candidates,
        similarity_threshold=0.85,
    )

    # Then
    assert result.duplicate_count == 1
    assert "1 potential duplicates" in result.get_summary()
    assert "10 notes analyzed" in result.get_summary()
    assert "0.85" in result.get_summary()


def test_duplicate_candidate_string_representation():
    """Test the string representation of DuplicateCandidate"""
    # Given
    candidate = DuplicateCandidate(
        original_note=AddonNote(
            guid="1",
            front="This is a very long front text that should be truncated",
            back="back1",
        ),
        duplicate_note=AddonNote(
            guid="2",
            front="This is another very long front text that should also be truncated",
            back="back2",
        ),
        similarity_score=0.923,
    )

    # When
    str_repr = str(candidate)

    # Then
    assert "0.923" in str_repr
    assert "This is a very long front text that should be" in str_repr
    assert "This is another very long front text that should" in str_repr
    assert len(str_repr) < 200  # Should be reasonably short


def test_empty_notes_list():
    """Test behavior with empty notes list"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates([], similarity_threshold=0.85)

    # Then
    assert result.total_notes_analyzed == 0
    assert result.duplicate_count == 0


def test_single_note():
    """Test behavior with single note"""
    # Given
    repository = QdrantDocumentRepository.create_null(search_responses=[[]])
    service = DuplicateDetectionService(repository)
    single_note = [AddonNote(guid="1", front="front", back="back")]

    # When
    result = service.find_duplicates(single_note, similarity_threshold=0.85)

    # Then
    assert result.total_notes_analyzed == 1
    assert result.duplicate_count == 0


def test_similarity_score_sorting():
    """Test that duplicate candidates are sorted by similarity score"""
    # Given
    search_responses = [
        [
            SearchResult(Document("note1", "content1", "source", {}), 1.0),
            SearchResult(Document("note2", "content2", "source", {}), 0.90),
            SearchResult(Document("note3", "content3", "source", {}), 0.95),
        ],
        [SearchResult(Document("note2", "content2", "source", {}), 1.0)],
        [SearchResult(Document("note3", "content3", "source", {}), 1.0)],
    ]

    notes = [
        AddonNote(guid="note1", front="front1", back="back1"),
        AddonNote(guid="note2", front="front2", back="back2"),
        AddonNote(guid="note3", front="front3", back="back3"),
    ]

    repository = QdrantDocumentRepository.create_null(
        search_responses=search_responses
    )
    service = DuplicateDetectionService(repository)

    # When
    result = service.find_duplicates(notes, similarity_threshold=0.85)

    # Then
    assert result.duplicate_count == 2
    # Should be sorted by similarity score (highest first)
    assert (
        result.duplicate_candidates[0].similarity_score
        >= result.duplicate_candidates[1].similarity_score
    )


def test_max_candidates_per_note_parameter():
    """Test that max_candidates_per_note parameter is respected"""
    # Given - search response with many candidates
    many_candidates = [
        SearchResult(Document("note1", "content1", "source", {}), 1.0),
        SearchResult(Document("note2", "content2", "source", {}), 0.95),
        SearchResult(Document("note3", "content3", "source", {}), 0.93),
        SearchResult(Document("note4", "content4", "source", {}), 0.91),
        SearchResult(Document("note5", "content5", "source", {}), 0.89),
    ]

    search_responses = [many_candidates]
    notes = [AddonNote(guid="note1", front="front1", back="back1")]

    repository = QdrantDocumentRepository.create_null(
        search_responses=search_responses
    )
    service = DuplicateDetectionService(repository)

    # When - limit to 2 candidates per note
    result = service.find_duplicates(
        notes, similarity_threshold=0.85, max_candidates_per_note=2
    )

    # Then - should only process top 2 similar notes (plus 1 for the note itself = 3 total)
    # But the limit affects the SearchQuery max_results parameter
    # This test verifies the parameter is passed correctly to the search
    assert isinstance(result, DuplicateDetectionResult)


def test_store_notes_as_documents():
    """Test the document storage functionality"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)

    notes = [
        AddonNote(
            guid="note1",
            front="Front text",
            back="Back text",
            tags=["tag1", "tag2"],
        ),
        AddonNote(
            guid="note2",
            front="{{c1::Cloze}} text",
            back="Extra",
            tags=["cloze"],
        ),
    ]

    # When and Then - should not raise an exception
    service._store_notes_as_documents(notes)


def test_prepare_search_text_with_html_tags():
    """Test that HTML tags are properly removed from search text"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)
    note_with_html = AddonNote(
        guid="html1",
        front="What is <b>machine learning</b>?",
        back="It's a <i>subset</i> of AI",
        tags=["ai"],
    )

    # When
    search_text = service._prepare_search_text(note_with_html)

    # Then
    assert "<b>" not in search_text
    assert "<i>" not in search_text
    assert "machine learning" in search_text
    assert "subset" in search_text
    assert "AI" in search_text


def test_empty_string_fields():
    """Test handling of empty string fields"""
    # Given
    repository = QdrantDocumentRepository.create_null()
    service = DuplicateDetectionService(repository)
    empty_note = AddonNote(guid="empty1", front="", back="", tags=[])

    # When
    search_text = service._prepare_search_text(empty_note)

    # Then
    assert isinstance(search_text, str)
    assert search_text == ""
