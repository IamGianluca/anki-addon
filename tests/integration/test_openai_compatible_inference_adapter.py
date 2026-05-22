import json
import os

import pytest
from tests.fakes.aqt_fakes import FakeAddonManager

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient

# NOTE: These tests require a live inference server. Configure it via env vars
# in .envrc: OPENAI_HOST, OPENAI_PORT, OPENAI_MODEL.


@pytest.fixture
def fast_addon_config() -> AddonConfig:
    """Config for integration tests: reads server address from env vars,
    reasoning disabled to save tokens/time."""
    return AddonConfig.create(
        FakeAddonManager(
            {
                "openai_host": os.environ["OPENAI_HOST"],
                "openai_port": os.environ["OPENAI_PORT"],
                "openai_model": os.environ["OPENAI_MODEL"],
            }
        )
    )


@pytest.mark.slow
def test_openai(fast_addon_config: AddonConfig) -> None:
    # Given
    openai_client = OpenAIClient(fast_addon_config)
    prompt = [
        {
            "role": "user",
            "content": "Respond only with one word, lowercase, without punctuation. What is the Italian word for hello?",
        }
    ]

    # When
    result = openai_client.run(prompt, max_tokens=5)

    # Then
    assert "ciao" in result.lower()


@pytest.mark.slow
def test_openai_with_json_schema_validation(
    fast_addon_config: AddonConfig,
) -> None:
    """Test that OpenAI client can accept and use JSON schema to restrict output."""
    # Given
    openai_client = OpenAIClient(fast_addon_config)

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
