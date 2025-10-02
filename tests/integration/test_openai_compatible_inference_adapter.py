import json

import pytest

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient

# NOTE: This test requires a live inference server. The test will fail if the
# inference server is not live.


@pytest.mark.slow
def test_openai(addon_config: AddonConfig) -> None:
    # Given
    openai_client = OpenAIClient.create(addon_config)
    prompt = "Respond only with one word, lowercase, without punctuation. What is the Italian word for hello?\nAnswer: "

    # When
    # NOTE: The word `ciao` requires two tokens using the
    # meta-llama/Meta-Llama-3-8B tokenizer
    result = openai_client.run(prompt, max_tokens=2)

    # Then
    assert result.strip().lower() == "ciao"


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

    prompt = """Create a JSON object for a fictional person. Include name, age, and city.
Example: A 25-year-old software engineer named Alice who lives in San Francisco."""

    # When
    result = openai_client.run(
        prompt, max_tokens=100, temperature=0, guided_json=person_schema
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
