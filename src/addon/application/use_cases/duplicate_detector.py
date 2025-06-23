"""
Use case for finding potentially duplicated notes using semantic search.
This module provides functionality to detect and report duplicate notes
based on semantic similarity of their content.
"""

from dataclasses import dataclass
from typing import List, Optional

from aqt import mw
from aqt.utils import showInfo

from ...domain.entities.note import AddonNote
from ...domain.repositories.document_repository import (
    Document,
    DocumentRepository,
    SearchQuery,
)
from ...utils import ensure_collection, is_cloze_note


@dataclass
class DuplicateCandidate:
    """Represents a potential duplicate note pair"""

    original_note: AddonNote
    duplicate_note: AddonNote
    similarity_score: float

    def __str__(self) -> str:
        return (
            f"Score: {self.similarity_score:.3f} | "
            f"Original: {self.original_note.front[:50]}... | "
            f"Duplicate: {self.duplicate_note.front[:50]}..."
        )


@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection analysis"""

    total_notes_analyzed: int
    duplicate_candidates: List[DuplicateCandidate]
    similarity_threshold: float

    @property
    def duplicate_count(self) -> int:
        return len(self.duplicate_candidates)

    def get_summary(self) -> str:
        return (
            f"Found {self.duplicate_count} potential duplicates "
            f"out of {self.total_notes_analyzed} notes analyzed "
            f"(threshold: {self.similarity_threshold})"
        )


class DuplicateDetectionService:
    """Service for detecting duplicate notes using semantic search"""

    def __init__(self, document_repository: DocumentRepository):
        self._repository = document_repository

    def find_duplicates(
        self,
        notes: List[AddonNote],
        similarity_threshold: float = 0.85,
        max_candidates_per_note: int = 3,
    ) -> DuplicateDetectionResult:
        """
        Find potential duplicate notes using semantic similarity.

        Args:
            notes: List of notes to analyze
            similarity_threshold: Minimum similarity score to consider as duplicate
            max_candidates_per_note: Maximum number of similar notes to check per note

        Returns:
            DuplicateDetectionResult with found duplicates
        """
        # First, store all notes in the vector database
        self._store_notes_as_documents(notes)

        duplicate_candidates = []
        processed_pairs = set()  # Avoid duplicate pairs (A,B) and (B,A)

        for note in notes:
            # Search for similar notes
            query_text = self._prepare_search_text(note)
            search_query = SearchQuery(
                query_text, max_results=max_candidates_per_note + 1
            )
            similar_notes = self._repository.find_similar(search_query)

            for result in similar_notes:
                # Skip self-matches
                if result.document.id == note.guid:
                    continue

                # Skip if similarity is below threshold
                if result.relevance_score < similarity_threshold:
                    continue

                # Create ordered pair key to avoid duplicates
                pair_key = tuple(sorted([note.guid, result.document.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                # Find the corresponding note object
                duplicate_note = self._find_note_by_guid(
                    notes, result.document.id
                )
                if duplicate_note:
                    candidate = DuplicateCandidate(
                        original_note=note,
                        duplicate_note=duplicate_note,
                        similarity_score=result.relevance_score,
                    )
                    duplicate_candidates.append(candidate)

        # Sort by similarity score (highest first)
        duplicate_candidates.sort(
            key=lambda x: x.similarity_score, reverse=True
        )

        return DuplicateDetectionResult(
            total_notes_analyzed=len(notes),
            duplicate_candidates=duplicate_candidates,
            similarity_threshold=similarity_threshold,
        )

    def _store_notes_as_documents(self, notes: List[AddonNote]) -> None:
        """Convert notes to documents and store them in the repository"""
        documents = []
        for note in notes:
            content = self._prepare_search_text(note)
            document = Document(
                id=note.guid,
                content=content,
                source="anki_note",
                metadata={
                    "note_type": "cloze"
                    if self._is_cloze_note_from_addon_note(note)
                    else "basic",
                    "tags": note.tags or [],
                    "deck_name": note.deck_name,
                },
            )
            documents.append(document)

        self._repository.store_batch(documents)

    def _prepare_search_text(self, note: AddonNote) -> str:
        """Prepare note content for semantic search"""
        # Combine front and back content, removing HTML tags for better matching
        from ...application.services.formatter_service import remove_html_tags

        front_text = remove_html_tags(note.front) if note.front else ""
        back_text = remove_html_tags(note.back) if note.back else ""

        # For cloze notes, focus more on the main text
        if self._is_cloze_note_from_addon_note(note):
            return front_text  # Cloze text is in the front field

        # For basic notes, combine front and back
        combined = f"{front_text} {back_text}".strip()
        return combined

    def _is_cloze_note_from_addon_note(self, note: AddonNote) -> bool:
        """Check if an AddonNote is a cloze note based on content patterns"""
        # Simple heuristic: check for cloze patterns like {{c1::text}}
        import re

        cloze_pattern = r"\{\{c\d+::[^}]+\}\}"
        return bool(re.search(cloze_pattern, note.front or ""))

    def _find_note_by_guid(
        self, notes: List[AddonNote], guid: str
    ) -> Optional[AddonNote]:
        """Find a note in the list by its GUID"""
        for note in notes:
            if note.guid == guid:
                return note
        return None


def display_duplicate_notes_count() -> None:
    """
    UI entry point to count and display potentially duplicate notes.
    This function should be added to the Tools menu.
    """
    try:
        from ...infrastructure.persistence.qdrant_repository import (
            QdrantDocumentRepository,
        )

        # Initialize the repository
        repository = QdrantDocumentRepository.create()
        detection_service = DuplicateDetectionService(repository)

        # Get all notes from current deck
        col = ensure_collection(mw.col)
        deck_id = col.decks.current()["id"]
        query = f"did:{deck_id}"
        note_ids = col.find_notes(query)

        if not note_ids:
            showInfo("No notes found in current deck.")
            return

        # Convert Anki notes to AddonNotes
        notes = []
        for note_id in note_ids:
            anki_note = col.get_note(note_id)
            addon_note = _convert_anki_note_to_addon_note(anki_note)
            notes.append(addon_note)

        # Run duplicate detection
        result = detection_service.find_duplicates(
            notes, similarity_threshold=0.85
        )

        # Display results
        summary = result.get_summary()
        if result.duplicate_count > 0:
            detailed_info = _format_duplicate_details(
                result.duplicate_candidates[:10]
            )  # Show top 10
            message = f"{summary}\n\nTop duplicates:\n{detailed_info}"
        else:
            message = f"{summary}\n\nNo potential duplicates found!"

        showInfo(message)

    except Exception as e:
        showInfo(f"Error detecting duplicates: {str(e)}")


def show_duplicate_notes_report() -> None:
    """
    Generate and display a detailed report of duplicate notes.
    This could open a separate dialog with more detailed information.
    """
    try:
        from ...infrastructure.persistence.qdrant_repository import (
            QdrantDocumentRepository,
        )

        repository = QdrantDocumentRepository.create()
        detection_service = DuplicateDetectionService(repository)

        col = ensure_collection(mw.col)
        deck_id = col.decks.current()["id"]
        query = f"did:{deck_id}"
        note_ids = col.find_notes(query)

        if not note_ids:
            showInfo("No notes found in current deck.")
            return

        notes = []
        for note_id in note_ids:
            anki_note = col.get_note(note_id)
            addon_note = _convert_anki_note_to_addon_note(anki_note)
            notes.append(addon_note)

        result = detection_service.find_duplicates(
            notes, similarity_threshold=0.80
        )

        if result.duplicate_count == 0:
            showInfo("No potential duplicates found!")
            return

        # Create detailed report
        report_lines = [
            "=== DUPLICATE DETECTION REPORT ===",
            f"Total notes analyzed: {result.total_notes_analyzed}",
            f"Potential duplicates found: {result.duplicate_count}",
            f"Similarity threshold: {result.similarity_threshold}",
            "",
            "=== DUPLICATE CANDIDATES ===",
            "",
        ]

        for i, candidate in enumerate(result.duplicate_candidates, 1):
            report_lines.extend(
                [
                    f"{i}. Similarity: {candidate.similarity_score:.3f}",
                    f"   Original: {candidate.original_note.front[:100]}...",
                    f"   Duplicate: {candidate.duplicate_note.front[:100]}...",
                    f"   Tags: {candidate.original_note.tags} vs {candidate.duplicate_note.tags}",
                    "",
                ]
            )

        report_text = "\n".join(report_lines)

        # For now, show in a simple info dialog
        # In a real implementation, you might want to create a custom dialog
        showInfo(report_text)

    except Exception as e:
        showInfo(f"Error generating duplicate report: {str(e)}")


def _convert_anki_note_to_addon_note(anki_note) -> AddonNote:
    """Convert an Anki Note to AddonNote format"""
    if is_cloze_note(anki_note):
        front, back = anki_note["Text"], anki_note["Back Extra"]
    else:
        front, back = anki_note["Front"], anki_note["Back"]

    return AddonNote(
        guid=anki_note.guid,
        front=front,
        back=back,
        tags=anki_note.tags,
        deck_name=None,  # Could be populated if needed
    )


def _format_duplicate_details(candidates: List[DuplicateCandidate]) -> str:
    """Format duplicate candidates for display"""
    lines = []
    for i, candidate in enumerate(candidates, 1):
        lines.append(f"{i}. {candidate}")
    return "\n".join(lines)
