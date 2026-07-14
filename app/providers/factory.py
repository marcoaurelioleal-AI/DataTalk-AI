from app.core.config import settings
from app.providers.base import LlmProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.mock_provider import MockProvider


class UnsupportedLlmProviderError(ValueError):
    pass


def get_llm_provider(provider_name: str | None = None) -> LlmProvider:
    selected_provider = (provider_name or settings.llm_provider).strip().lower()
    if selected_provider == "mock":
        return MockProvider()
    if selected_provider == "gemini":
        return GeminiProvider()

    raise UnsupportedLlmProviderError(f"LLM provider '{selected_provider}' is not implemented.")
