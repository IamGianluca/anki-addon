from typing import Optional

import pytest

from addon.domain.entities.note import AddonNote, AddonNoteType
from addon.domain.repositories.document_repository import (
    convert_addon_note_to_document,
    convert_document_to_addon_note,
)


@pytest.mark.parametrize(
    "notetype, expected",
    [
        (None, AddonNoteType.BASIC),  # Test default behavior
        (AddonNoteType.BASIC, AddonNoteType.BASIC),
        (AddonNoteType.CLOZE, AddonNoteType.CLOZE),
    ],
)
def test_create_addonnote(
    notetype: Optional[AddonNoteType], expected: AddonNoteType
) -> None:
    # Given
    kwargs = {
        "guid": "first",
        "front": "question",
        "back": "answer",
        "deck_name": "test",
    }

    if notetype:
        kwargs["notetype"] = notetype

    # When
    result = AddonNote(**kwargs)

    # Then
    assert result.notetype == expected


def test_convert_addon_note_to_document_and_back(
    addon_note1: AddonNote,
) -> None:
    # When
    doc = convert_addon_note_to_document(addon_note1)

    # Then
    assert doc.metadata == addon_note1.__dict__

    # When
    note = convert_document_to_addon_note(doc)

    # Then
    for attr, val in addon_note1.__dict__.items():
        assert getattr(note, attr) == val


def test_addonnote_requires_front_and_back() -> None:
    # When/Then - missing back should raise TypeError
    with pytest.raises(TypeError):
        AddonNote(front="only front")

    # When/Then - missing front should raise TypeError
    with pytest.raises(TypeError):
        AddonNote(back="only back")


def test_convert_preserves_all_fields_including_tags_and_notetype(
    addon_note1: AddonNote,
) -> None:
    # Given
    addon_note1.tags = ["tag1", "tag2"]
    addon_note1.notetype = AddonNoteType.CLOZE
    addon_note1.deck_name = "Test Deck"

    # When
    doc = convert_addon_note_to_document(addon_note1)
    restored = convert_document_to_addon_note(doc)

    # Then
    assert restored.front == addon_note1.front
    assert restored.back == addon_note1.back
    assert restored.tags == addon_note1.tags
    assert restored.notetype == addon_note1.notetype
    assert restored.deck_name == addon_note1.deck_name
    assert restored.guid == addon_note1.guid


def test_addonnote_generates_guid_automatically() -> None:
    # When
    note1 = AddonNote(front="front", back="back")
    note2 = AddonNote(front="front", back="back")

    # Then - each note should have unique guid
    assert note1.guid != note2.guid
    assert len(note1.guid) > 0
    assert len(note2.guid) > 0


def test_convert_addon_note_to_document_joins_tags_with_spaces() -> None:
    # Given
    note = AddonNote(
        front="test front", back="test back", tags=["python", "programming"]
    )

    # When
    doc = convert_addon_note_to_document(note)

    # Then - tags should be space-separated in content, not concatenated
    assert "python programming" in doc.content
    assert "pythonprogramming" not in doc.content
    # Verify front and back are also included
    assert "test front" in doc.content
    assert "test back" in doc.content
