from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.sql_safety import SqlSafetyResult


class SqlAgentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["success", "blocked", "needs_clarification"]
    answer: str
    generated_sql: str | None
    provider_used: str
    model_used: str
    recognized_intent: str | None
    schema_context: str
    agent_prompt: str
    safety_result: SqlSafetyResult | None
