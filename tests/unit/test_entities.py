import pytest

from addon.domain.entities.note import AddonNote, AddonNoteType


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
