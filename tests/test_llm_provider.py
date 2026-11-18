
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.llm import GeminiLLM, configured_client
from google.genai import errors

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.interactions.create.return_value = SimpleNamespace(
        status="completed",
        output_text="The expense ratio is 0.5%. [7 p.4]",
        usage=SimpleNamespace(
            total_input_tokens=20,
            total_output_tokens=12,
            total_tokens=32,
        ),
    )
    return client


@pytest.fixture
def llm(tmp_path, mock_client):
    return GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        cache_enabled=True,
        cache_dir=tmp_path / "cache",
        usage_log=tmp_path / "logs" / "usage.jsonl",
    )


def test_gemini_success(llm, mock_client):
    result = llm.generate("Test prompt")

    assert result == "The expense ratio is 0.5%. [7 p.4]"
    mock_client.interactions.create.assert_called_once_with(
        model="gemini-test-model",
        input="Test prompt",
        store=False,
        generation_config={"temperature": 0.0, "max_output_tokens": 400},
    )
    assert llm.last_usage == {"input_tokens": 20, "output_tokens": 12, "total_tokens": 32}


def test_gemini_cache_hit(llm, mock_client):
    first = llm.generate("Test prompt")
    second = llm.generate("Test prompt")

    assert first == second
    assert mock_client.interactions.create.call_count == 1


def test_cache_separates_generation_parameters(llm, mock_client):
    llm.generate("Same prompt", temperature=0.0, max_tokens=64)
    llm.generate("Same prompt", temperature=0.2, max_tokens=64)
    llm.generate("Same prompt", temperature=0.2, max_tokens=128)

    assert mock_client.interactions.create.call_count == 3


def test_cache_separates_different_prompts(llm, mock_client):
    llm.generate("Prompt A")
    llm.generate("Prompt B")

    assert mock_client.interactions.create.call_count == 2


def test_usage_log_contains_metadata_only(llm):
    llm.generate("Sensitive prompt that must not be logged")

    records = [
        json.loads(line)
        for line in llm.usage_log.read_text(encoding="utf-8").splitlines()
    ]

    assert records[0]["status"] == "success"
    assert records[0]["provider"] == "gemini"
    assert records[0]["total_tokens"] == 32

    log_text = llm.usage_log.read_text(encoding="utf-8")
    assert "Sensitive prompt" not in log_text
    assert "The expense ratio" not in log_text


def test_empty_prompt_rejected(llm, mock_client):
    with pytest.raises(ValueError, match="non-empty"):
        llm.generate("   ")

    mock_client.interactions.create.assert_not_called()


def test_cache_disabled_always_calls_provider(mock_client, tmp_path):
    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        cache_enabled=False,
        cache_dir=tmp_path / "cache",
        usage_log=tmp_path / "usage.jsonl",
    )

    client.generate("Same prompt")
    client.generate("Same prompt")

    assert mock_client.interactions.create.call_count == 2


def test_failed_request_logs_error_without_prompt(mock_client, tmp_path):
    mock_client.interactions.create.side_effect = ValueError(
        "Invalid request"
    )

    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        max_retries=3,
        cache_enabled=False,
        cache_dir=tmp_path / "cache",
        usage_log=tmp_path / "usage.jsonl",
    )

    with pytest.raises(ValueError, match="Invalid request"):
        client.generate("Private prompt")

    log_text = (tmp_path / "usage.jsonl").read_text(encoding="utf-8")
    record = json.loads(log_text.splitlines()[-1])

    assert record["status"] == "error"
    assert record["error_type"] == "ValueError"
    assert "Private prompt" not in log_text

class ServiceUnavailable(Exception):
    """Simulates a temporary provider outage."""


def test_transient_failure_is_retried(mock_client, tmp_path):
    mock_client.interactions.create.side_effect = [
        ServiceUnavailable("Temporary outage"),
        ServiceUnavailable("Temporary outage"),
        SimpleNamespace(
            status="completed",
            output_text="Recovered successfully.",
            usage=SimpleNamespace(
                total_input_tokens=10,
                total_output_tokens=5,
                total_tokens=15,
            ),
        ),
    ]

    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        max_retries=2,
        cache_enabled=False,
        usage_log=tmp_path / "usage.jsonl",
    )

    result = client.generate("Test retry")

    assert result == "Recovered successfully."
    assert mock_client.interactions.create.call_count == 3


def test_permanent_failure_is_not_retried(mock_client, tmp_path):
    mock_client.interactions.create.side_effect = ValueError(
        "Invalid request"
    )

    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        max_retries=3,
        cache_enabled=False,
        usage_log=tmp_path / "usage.jsonl",
    )

    with pytest.raises(ValueError, match="Invalid request"):
        client.generate("Test permanent failure")

    assert mock_client.interactions.create.call_count == 1

def test_configured_client_uses_yaml_settings(
    tmp_path, monkeypatch
):
    from google import genai

    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
llm:
  provider: gemini
  model: gemini-test-model
  timeout_seconds: 17
  max_retries: 4
  cache_enabled: false
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("LLM_PROVIDER", "Gemini")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")

    mock_sdk_client = MagicMock()
    client_factory = MagicMock(return_value=mock_sdk_client)

    monkeypatch.setattr(genai, "Client", client_factory)

    result = configured_client(config_path=config_path)

    client_factory.assert_called_once()

    kwargs = client_factory.call_args.kwargs

    assert kwargs["api_key"] == "test-key-not-real"
    assert kwargs["http_options"].timeout == 17000
    assert kwargs["http_options"].retry_options.attempts == 1
    assert mock_sdk_client.interactions.sdk_configuration.retry_config.max_retries == 0
    assert mock_sdk_client.interactions.sdk_configuration.retry_config.retry_connection_errors is False

    assert isinstance(result, GeminiLLM)
    assert result.model == "gemini-test-model"
    assert result.timeout_seconds == 17
    assert result.max_retries == 4
    assert result.cache_enabled is False

def test_configured_client_accepts_short_no_retry_preflight_overrides(
    tmp_path, monkeypatch
):
    from google import genai

    config_path = tmp_path / "config.yaml"
    config_path.write_text("llm:\n  model: gemini-test-model\n", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "Gemini")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    factory = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(genai, "Client", factory)

    result = configured_client(
        config_path=config_path,
        timeout_seconds_override=30,
        max_retries_override=0,
        cache_enabled_override=False,
    )
    options = factory.call_args.kwargs["http_options"]
    assert options.timeout == 30000
    assert options.retry_options.attempts == 1
    assert result.timeout_seconds == 30
    assert result.max_retries == 0
    assert result.cache_enabled is False


def test_real_gemini_server_error_is_retried(mock_client, tmp_path):
    mock_client.interactions.create.side_effect = [
        errors.ServerError(
            503,
            {"error": {"status": "UNAVAILABLE", "message": "Busy"}},
        ),
        errors.ServerError(
            503,
            {"error": {"status": "UNAVAILABLE", "message": "Busy"}},
        ),
        SimpleNamespace(
            status="completed",
            output_text="Recovered after retry.",
            usage=SimpleNamespace(
                total_input_tokens=10,
                total_output_tokens=5,
                total_tokens=15,
            ),
        ),
    ]

    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        max_retries=2,
        cache_enabled=False,
        usage_log=tmp_path / "usage.jsonl",
    )

    result = client.generate("Test real Gemini retry")

    assert result == "Recovered after retry."
    assert mock_client.interactions.create.call_count == 3


def test_real_gemini_client_error_is_not_retried(mock_client, tmp_path):
    mock_client.interactions.create.side_effect = errors.ClientError(
        400,
        {"error": {"status": "INVALID_ARGUMENT", "message": "Bad request"}},
    )

    client = GeminiLLM(
        client=mock_client,
        model="gemini-test-model",
        max_retries=3,
        cache_enabled=False,
        usage_log=tmp_path / "usage.jsonl",
    )

    with pytest.raises(errors.ClientError):
        client.generate("Test permanent Gemini error")

    assert mock_client.interactions.create.call_count == 1