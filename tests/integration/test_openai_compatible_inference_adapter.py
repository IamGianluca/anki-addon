import pytest

from addon.infrastructure.configuration.settings import AddonConfig
from addon.infrastructure.external_services.openai import OpenAIClient

# NOTE: This test requires a live inference server. The test will fail if the
# inference server is not live.


@pytest.mark.slow
def test_openai():
    # Given
    config = AddonConfig.create_nullable()
    openai_client = OpenAIClient.create(config)
    prompt = "Respond only with one word, lowercase, without punctuation. What is the Italian word for hello?\nAnswer: "

    # When
    # NOTE: The word `ciao` requires two tokens using the
    # meta-llama/Meta-Llama-3-8B tokenizer
    result = openai_client.run(prompt, max_tokens=2)

    # Then
    assert result.strip().lower() == "ciao"
