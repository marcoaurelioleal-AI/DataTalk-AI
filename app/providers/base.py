from typing import Protocol

from app.schemas.llm_provider import LlmProviderResult


class LlmProviderError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        provider_used: str,
        model_used: str,
        category: str,
        retryable: bool,
        attempts: int,
    ) -> None:
        super().__init__(message)
        self.provider_used = provider_used
        self.model_used = model_used
        self.category = category
        self.retryable = retryable
        self.attempts = attempts


class LlmProvider(Protocol):
    name: str
    model_name: str

    def generate(self, question: str, *, prompt: str | None = None) -> LlmProviderResult: ...
