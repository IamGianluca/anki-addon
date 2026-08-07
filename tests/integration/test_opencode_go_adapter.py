import os

import pytest

from addon.infrastructure.configuration.settings import OpenCodeGoConfig
from addon.infrastructure.external_services.opencode_go import (
    OpenCodeGoClient,
)
from addon.infrastructure.llm.schemas import AddonNoteChanges

# NOTE: These tests require a live OpenCode Go API key. Configure it via
# env vars in .envrc: OPENCODE_GO_API_KEY, OPENCODE_GO_MODEL.


@pytest.fixture
def client() -> OpenCodeGoClient:
    missing = [
        key
        for key in ("OPENCODE_GO_API_KEY", "OPENCODE_GO_MODEL")
        if not os.environ.get(key)
    ]
    if missing:
        pytest.skip(f"env vars not set: {', '.join(missing)}")
    return OpenCodeGoClient(
        OpenCodeGoConfig(
            {
                "opencode_go_api_key": os.environ["OPENCODE_GO_API_KEY"],
                "opencode_go_model": os.environ["OPENCODE_GO_MODEL"],
            }
        )
    )


@pytest.mark.slow
def test_chat_completion_roundtrip(client: OpenCodeGoClient) -> None:
    # Given
    prompt = [
        {
            "role": "user",
            "content": (
                "Respond only with one word, lowercase, without punctuation. "
                "What is the Italian word for hello?"
            ),
        }
    ]

    # When — no max_tokens override: reasoning models need room to think
    # before answering, so use the config default (8192).
    result = client.run(prompt)

    # Then
    assert "ciao" in result.lower()


@pytest.mark.slow
def test_structured_output_matches_addon_schema(
    client: OpenCodeGoClient,
) -> None:
    """Verify the gateway honors response_format json_schema with the real
    schema the note formatter depends on."""
    # Given
    prompt = [
        {
            "role": "user",
            "content": (
                "Improve this flashcard. Fix the capitalization of the front "
                "field, keep the back as is.\n"
                "Front: what is the capital of france?\n"
                "Back: Paris"
            ),
        }
    ]

    # When
    result = client.run(
        prompt,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "addon_note_changes",
                "schema": AddonNoteChanges.model_json_schema(),
            },
        },
    )

    # Then
    changes = AddonNoteChanges.model_validate_json(result)
    assert changes.front
    assert changes.back
