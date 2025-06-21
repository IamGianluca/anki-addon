# create integration test to ensure we can format a semi-real note using
# a real l

import pytest
from tests.fakes.aqt_fakes import FakeNote

from addon.application.services.completion_service import CompletionService
from addon.application.services.formatter_service import (
    NoteFormatter,
    format_note_workflow,
)
from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient


@pytest.mark.slow
def test_format_note_using_llm():
    # Given
    note = FakeNote(
        note_id="1111",
        fields={
            "Front": "What is the most winning team in NHL history?",
            "Back": "The Montreal Canadiens are the most winning team in NHL history with 24 Stanley Cup championships, far more than any other franchise.",
        },
    )
    note.tags = ["hockey"]
    config = AddonConfig.create_nullable()
    openai = OpenAIClient.create(config)

    completion = CompletionService(openai)
    formatter = NoteFormatter(completion)

    # When
    result = format_note_workflow(note, formatter)

    # Then

    from anki.notes import Note  # Prevents circular import

    assert isinstance(result, (Note, FakeNote))
    assert "Most winning NHL team" in result["Front"]
    assert "Montreal Canadiens" in result["Back"]
