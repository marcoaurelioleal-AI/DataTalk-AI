import json
import logging
from time import perf_counter, sleep
from typing import Any, Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError, model_validator

from app.core.config import settings
from app.providers.base import LlmProviderError
from app.schemas.llm_provider import LlmProviderResult

LOGGER = logging.getLogger("uvicorn.error")


class GeminiConfigurationError(ValueError):
    pass


class GeminiProviderError(LlmProviderError):
    pass


class GeminiGeneration(BaseModel):
    status: Literal["success", "needs_clarification"]
    answer: str = Field(min_length=1)
    generated_sql: str | None
    recognized_intent: str | None

    @model_validator(mode="after")
    def validate_status_payload(self) -> "GeminiGeneration":
        if self.status == "success" and not self.generated_sql:
            raise ValueError("A successful generation must include SQL.")
        if self.status == "needs_clarification" and self.generated_sql is not None:
            raise ValueError("A clarification response cannot include SQL.")
        return self


class GeminiProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        client: Any | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        selected_api_key = settings.gemini_api_key if api_key is None else api_key
        if not selected_api_key.strip() or selected_api_key.strip() == "your_gemini_key_here":
            raise GeminiConfigurationError(
                "GEMINI_API_KEY deve ser configurada quando LLM_PROVIDER=gemini."
            )

        self.model_name = model_name or settings.gemini_chat_model
        self.timeout_seconds = (
            settings.llm_request_timeout_seconds if timeout_seconds is None else timeout_seconds
        )
        self.max_retries = settings.llm_max_retries if max_retries is None else max_retries
        self.retry_backoff_seconds = (
            settings.llm_retry_backoff_seconds
            if retry_backoff_seconds is None
            else retry_backoff_seconds
        )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative.")
        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds cannot be negative.")

        self._client = client or genai.Client(
            api_key=selected_api_key.strip(),
            http_options=types.HttpOptions(
                timeout=round(self.timeout_seconds * 1000),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    def generate(self, question: str, *, prompt: str | None = None) -> LlmProviderResult:
        contents = prompt.strip() if prompt and prompt.strip() else question.strip()
        started_at = perf_counter()
        attempts = 0

        while True:
            attempts += 1
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=GeminiGeneration,
                        temperature=0,
                    ),
                )
                break
            except Exception as error:
                category, retryable = self._classify_error(error)
                if retryable and attempts <= self.max_retries:
                    self._log_event(
                        event="llm_provider_retry",
                        status="retrying",
                        attempts=attempts,
                        latency_ms=self._elapsed_ms(started_at),
                        error_category=category,
                        level=logging.WARNING,
                    )
                    sleep(self.retry_backoff_seconds * (2 ** (attempts - 1)))
                    continue

                self._log_event(
                    event="llm_provider_request",
                    status="error",
                    attempts=attempts,
                    latency_ms=self._elapsed_ms(started_at),
                    error_category=category,
                    level=logging.ERROR,
                )
                raise GeminiProviderError(
                    "Nao foi possivel consultar o Gemini neste momento.",
                    provider_used=self.name,
                    model_used=self.model_name,
                    category=category,
                    retryable=retryable,
                    attempts=attempts,
                ) from error

        try:
            parsed = response.parsed
            generation = parsed if isinstance(parsed, GeminiGeneration) else GeminiGeneration.model_validate(parsed)
        except (ValidationError, AttributeError, TypeError, ValueError) as error:
            self._log_event(
                event="llm_provider_request",
                status="error",
                attempts=attempts,
                latency_ms=self._elapsed_ms(started_at),
                error_category="invalid_response",
                level=logging.ERROR,
            )
            raise GeminiProviderError(
                "O Gemini nao retornou uma resposta valida.",
                provider_used=self.name,
                model_used=self.model_name,
                category="invalid_response",
                retryable=False,
                attempts=attempts,
            ) from error

        self._log_event(
            event="llm_provider_request",
            status="success",
            attempts=attempts,
            latency_ms=self._elapsed_ms(started_at),
            error_category=None,
            level=logging.INFO,
        )

        return LlmProviderResult(
            status=generation.status,
            answer=generation.answer,
            generated_sql=generation.generated_sql,
            provider_used=self.name,
            model_used=self.model_name,
            recognized_intent=generation.recognized_intent,
        )

    def _classify_error(self, error: Exception) -> tuple[str, bool]:
        if isinstance(error, TimeoutError):
            return "timeout", True
        if isinstance(error, ConnectionError):
            return "unavailable", True

        code = getattr(error, "code", None)
        if code == 429:
            return "rate_limit", True
        if isinstance(code, int) and code >= 500:
            return "unavailable", True
        if code in {401, 403}:
            return "authentication", False
        if isinstance(code, int) and 400 <= code < 500:
            return "invalid_request", False
        return "provider_error", False

    def _log_event(
        self,
        *,
        event: str,
        status: str,
        attempts: int,
        latency_ms: int,
        error_category: str | None,
        level: int,
    ) -> None:
        payload = {
            "event": event,
            "provider": self.name,
            "model": self.model_name,
            "status": status,
            "attempts": attempts,
            "latency_ms": latency_ms,
            "error_category": error_category,
        }
        LOGGER.log(level, json.dumps(payload, separators=(",", ":")))

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
