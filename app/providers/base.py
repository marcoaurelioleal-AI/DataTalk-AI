from typing import Protocol

from app.schemas.llm_provider import LlmProviderResult


class LlmProvider(Protocol):
    name: str
    model_name: str

    def generate(self, question: str) -> LlmProviderResult: ...
