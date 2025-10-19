import os

from tests.fakes.aqt_fakes import FakeAddonManager

from addon.infrastructure.configuration.settings import AddonConfig


def test_reads_required_parameters_from_env():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_TEMPERATURE"] = "0.7"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.url == "http://localhost:8000/v1/chat/completions"
    assert config.model_name == "test-model"
    assert config.temperature == 0.7


def test_defaults_temperature_when_not_set():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ.pop("OPENAI_TEMPERATURE", None)

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.temperature == 0.0


def test_reads_max_tokens_from_env():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_MAX_TOKENS"] = "200"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.max_tokens == 200


def test_defaults_max_tokens_when_not_set():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ.pop("OPENAI_MAX_TOKENS", None)

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.max_tokens == 500


def test_reads_optional_top_p_parameter():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_TOP_P"] = "0.8"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.top_p == 0.8


def test_reads_optional_top_k_parameter():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_TOP_K"] = "20"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.top_k == 20


def test_reads_optional_min_p_parameter():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_MIN_P"] = "0.05"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.min_p == 0.05


def test_optional_parameters_are_none_when_not_set():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ.pop("OPENAI_TOP_P", None)
    os.environ.pop("OPENAI_TOP_K", None)
    os.environ.pop("OPENAI_MIN_P", None)

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.top_p is None
    assert config.top_k is None
    assert config.min_p is None


def test_reads_all_parameters_together():
    # Given
    os.environ["OPENAI_HOST"] = "localhost"
    os.environ["OPENAI_PORT"] = "8000"
    os.environ["OPENAI_MODEL"] = "test-model"
    os.environ["OPENAI_TEMPERATURE"] = "0.7"
    os.environ["OPENAI_MAX_TOKENS"] = "300"
    os.environ["OPENAI_TOP_P"] = "0.9"
    os.environ["OPENAI_TOP_K"] = "40"
    os.environ["OPENAI_MIN_P"] = "0.1"

    # When
    config = AddonConfig.create_nullable()

    # Then
    assert config.url == "http://localhost:8000/v1/chat/completions"
    assert config.model_name == "test-model"
    assert config.temperature == 0.7
    assert config.max_tokens == 300
    assert config.top_p == 0.9
    assert config.top_k == 40
    assert config.min_p == 0.1


def test_reads_required_parameters_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_temperature": 0.7,
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.url == "http://localhost:8000/v1/chat/completions"
    assert config.model_name == "test-model"
    assert config.temperature == 0.7


def test_defaults_temperature_when_not_in_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.temperature == 0.0


def test_reads_max_tokens_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_max_tokens": 200,
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.max_tokens == 200


def test_defaults_max_tokens_when_not_in_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.max_tokens == 200


def test_reads_optional_top_p_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_top_p": "0.8",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.top_p == 0.8


def test_reads_optional_top_k_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_top_k": "20",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.top_k == 20


def test_reads_optional_min_p_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_min_p": "0.05",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.min_p == 0.05


def test_optional_parameters_are_none_when_not_in_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.top_p is None
    assert config.top_k is None
    assert config.min_p is None


def test_reads_all_parameters_from_anki_config():
    # Given
    addon_manager = FakeAddonManager(
        {
            "openai_host": "localhost",
            "openai_port": "8000",
            "openai_model": "test-model",
            "openai_temperature": 0.7,
            "openai_max_tokens": 300,
            "openai_top_p": "0.9",
            "openai_top_k": "40",
            "openai_min_p": "0.1",
        }
    )

    # When
    config = AddonConfig.create(addon_manager)

    # Then
    assert config.url == "http://localhost:8000/v1/chat/completions"
    assert config.model_name == "test-model"
    assert config.temperature == 0.7
    assert config.max_tokens == 300
    assert config.top_p == 0.9
    assert config.top_k == 40
    assert config.min_p == 0.1
