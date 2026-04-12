import json

import pytest

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient

# Disable thinking tokens so tests run faster and don't exhaust max_tokens.
# Requires the server to be started with --reasoning-budget 0.
_NO_THINKING = {
    "extra_body": {"chat_template_kwargs": {"enable_thinking": False}}
}

# NOTE: This test requires a live inference server. The test will fail if the
# inference server is not live.


@pytest.mark.slow
def test_openai(addon_config: AddonConfig) -> None:
    # Given
    openai_client = OpenAIClient.create(addon_config)
    prompt = [
        {
            "role": "user",
            "content": "Respond only with one word, lowercase, without punctuation. What is the Italian word for hello?",
        }
    ]

    # When
    result = openai_client.run(prompt, max_tokens=5, **_NO_THINKING)

    # Then
    assert "ciao" in result.lower()


@pytest.mark.slow
def test_openai_with_json_schema_validation(addon_config: AddonConfig) -> None:
    """Test that OpenAI client can accept and use JSON schema to restrict output."""
    # Given
    openai_client = OpenAIClient.create(addon_config)

    person_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "city": {"type": "string"},
        },
        "required": ["name", "age", "city"],
        "additionalProperties": False,
    }

    prompt = [
        {
            "role": "user",
            "content": "Create a JSON object for a fictional person. Include name, age, and city.\nExample: A 25-year-old software engineer named Alice who lives in San Francisco.",
        }
    ]

    # When
    result = openai_client.run(
        prompt,
        max_tokens=50,
        temperature=0,
        guided_json=person_schema,
        **_NO_THINKING,
    )

    # Then
    parsed_result = json.loads(result)

    assert "name" in parsed_result
    assert "age" in parsed_result
    assert "city" in parsed_result

    assert isinstance(parsed_result["name"], str)
    assert isinstance(parsed_result["age"], int)
    assert isinstance(parsed_result["city"], str)

    assert 0 <= parsed_result["age"] <= 150

    # Verify no additional properties (schema constraint)
    assert len(parsed_result) == 3
