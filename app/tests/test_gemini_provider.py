import json
import logging
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.providers.gemini_provider import (
    GeminiConfigurationError,
    GeminiGeneration,
    GeminiProvider,
    GeminiProviderError,
)


class FakeModels:
    def __init__(
        self,
        parsed: object = None,
        error: Exception | None = None,
        outcomes: list[object] | None = None,
    ) -> None:
        self.parsed = parsed
        self.error = error
        self.outcomes = list(outcomes or [])
        self.calls: list[dict[str, object]] = []

    def generate_content(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return SimpleNamespace(parsed=outcome, text="unused")
        if self.error:
            raise self.error
        return SimpleNamespace(parsed=self.parsed, text="unused")


def make_client(
    parsed: object = None,
    error: Exception | None = None,
    outcomes: list[object] | None = None,
) -> object:
    return SimpleNamespace(models=FakeModels(parsed=parsed, error=error, outcomes=outcomes))


class FakeSdkError(RuntimeError):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


SUCCESS_PAYLOAD = {
    "status": "success",
    "answer": "Consulta preparada com seguranca.",
    "generated_sql": "SELECT name FROM products LIMIT 5",
    "recognized_intent": "list_products",
}


@pytest.mark.parametrize("api_key", ["", "   ", "your_gemini_key_here"])
def test_gemini_provider_rejects_missing_or_placeholder_key(api_key: str) -> None:
    with pytest.raises(GeminiConfigurationError, match="GEMINI_API_KEY"):
        GeminiProvider(api_key=api_key)


def test_gemini_provider_returns_validated_structured_result() -> None:
    client = make_client(SUCCESS_PAYLOAD)
    provider = GeminiProvider(api_key="test-api-key", model_name="gemini-test", client=client)

    result = provider.generate("Liste produtos", prompt="PROMPT SEGURO COM SCHEMA")

    assert result.status == "success"
    assert result.generated_sql == "SELECT name FROM products LIMIT 5"
    assert result.provider_used == "gemini"
    assert result.model_used == "gemini-test"
    assert result.recognized_intent == "list_products"
    call = client.models.calls[0]  # type: ignore[attr-defined]
    assert call["model"] == "gemini-test"
    assert call["contents"] == "PROMPT SEGURO COM SCHEMA"
    assert call["config"].response_mime_type == "application/json"  # type: ignore[union-attr]


def test_gemini_generation_schema_avoids_unsupported_additional_properties() -> None:
    assert "additionalProperties" not in GeminiGeneration.model_json_schema()


def test_gemini_provider_supports_clarification_without_sql() -> None:
    client = make_client(
        {
            "status": "needs_clarification",
            "answer": "Qual periodo deseja analisar?",
            "generated_sql": None,
            "recognized_intent": None,
        }
    )
    provider = GeminiProvider(api_key="test-api-key", client=client)

    result = provider.generate("Mostre vendas", prompt="prompt")

    assert result.status == "needs_clarification"
    assert result.generated_sql is None


def test_gemini_provider_rejects_inconsistent_structured_output() -> None:
    client = make_client(
        {
            "status": "success",
            "answer": "Sem SQL",
            "generated_sql": None,
            "recognized_intent": "invalid",
        }
    )
    provider = GeminiProvider(api_key="test-api-key", client=client)

    with pytest.raises(GeminiProviderError, match="resposta valida"):
        provider.generate("Pergunta", prompt="prompt")


def test_gemini_provider_sanitizes_sdk_errors() -> None:
    client = make_client(error=RuntimeError("request failed with key test-api-key"))
    provider = GeminiProvider(api_key="test-api-key", client=client)

    with pytest.raises(GeminiProviderError, match="Gemini") as error:
        provider.generate("Pergunta", prompt="prompt")

    assert "test-api-key" not in str(error.value)


def test_settings_expose_gemini_resilience_configuration() -> None:
    configured_settings = Settings(
        _env_file=None,
        LLM_REQUEST_TIMEOUT_SECONDS=12,
        LLM_MAX_RETRIES=3,
        LLM_RETRY_BACKOFF_SECONDS=0.4,
    )

    assert configured_settings.llm_request_timeout_seconds == 12
    assert configured_settings.llm_max_retries == 3
    assert configured_settings.llm_retry_backoff_seconds == 0.4


def test_gemini_provider_configures_sdk_timeout_and_single_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(**kwargs: object) -> object:
        captured.update(kwargs)
        return make_client(SUCCESS_PAYLOAD)

    monkeypatch.setattr("app.providers.gemini_provider.genai.Client", fake_client)

    GeminiProvider(
        api_key="test-api-key",
        timeout_seconds=12,
        max_retries=2,
        retry_backoff_seconds=0,
    )

    http_options = captured["http_options"]
    assert http_options.timeout == 12_000  # type: ignore[union-attr]
    assert http_options.retry_options.attempts == 1  # type: ignore[union-attr]


def test_gemini_provider_retries_transient_failure_and_logs_metrics(caplog: pytest.LogCaptureFixture) -> None:
    client = make_client(outcomes=[FakeSdkError("temporary outage", 503), SUCCESS_PAYLOAD])
    provider = GeminiProvider(
        api_key="test-api-key",
        model_name="gemini-test",
        client=client,
        max_retries=2,
        retry_backoff_seconds=0,
    )

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        result = provider.generate("pergunta secreta", prompt="prompt com schema")

    assert result.status == "success"
    assert len(client.models.calls) == 2  # type: ignore[attr-defined]
    completed = json.loads(caplog.records[-1].getMessage())
    assert completed == {
        "event": "llm_provider_request",
        "provider": "gemini",
        "model": "gemini-test",
        "status": "success",
        "attempts": 2,
        "latency_ms": completed["latency_ms"],
        "error_category": None,
    }
    assert completed["latency_ms"] >= 0
    assert caplog.records[-1].name == "uvicorn.error"
    assert "pergunta secreta" not in caplog.text
    assert "prompt com schema" not in caplog.text
    assert "test-api-key" not in caplog.text


def test_gemini_provider_does_not_retry_permanent_failure() -> None:
    client = make_client(error=FakeSdkError("invalid credential test-api-key", 401))
    provider = GeminiProvider(
        api_key="test-api-key",
        client=client,
        max_retries=2,
        retry_backoff_seconds=0,
    )

    with pytest.raises(GeminiProviderError) as captured:
        provider.generate("Pergunta", prompt="prompt")

    assert captured.value.category == "authentication"
    assert captured.value.retryable is False
    assert captured.value.attempts == 1
    assert len(client.models.calls) == 1  # type: ignore[attr-defined]
    assert "credential" not in str(captured.value)


def test_gemini_provider_limits_timeout_retries() -> None:
    client = make_client(error=TimeoutError("socket timeout test-api-key"))
    provider = GeminiProvider(
        api_key="test-api-key",
        client=client,
        max_retries=2,
        retry_backoff_seconds=0,
    )

    with pytest.raises(GeminiProviderError) as captured:
        provider.generate("Pergunta", prompt="prompt")

    assert captured.value.category == "timeout"
    assert captured.value.retryable is True
    assert captured.value.attempts == 3
    assert len(client.models.calls) == 3  # type: ignore[attr-defined]
    assert "socket" not in str(captured.value)
