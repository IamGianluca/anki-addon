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
def test_create_addonnote(notetype, expected):
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


def test_convert_addon_note_to_document_and_back(addon_note1):
    # When
    doc = convert_addon_note_to_document(addon_note1)

    # Then
    assert doc.metadata == addon_note1.__dict__

    # When
    note = convert_document_to_addon_note(doc)

    # Then
    for attr, val in addon_note1.__dict__.items():
        assert getattr(note, attr) == val
