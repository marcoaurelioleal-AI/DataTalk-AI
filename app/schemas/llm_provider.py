from typing import Literal

from pydantic import BaseModel, ConfigDict


class LlmProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["success", "needs_clarification"]
    answer: str
    generated_sql: str | None
    provider_used: str
    model_used: str
    recognized_intent: str | None
