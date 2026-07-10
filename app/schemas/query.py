from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AskQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        return " ".join(value.strip().split())


class ChartSuggestion(BaseModel):
    type: Literal["bar", "line", "pie", "table", "metric"] = "table"
    x: str | None = None
    y: str | None = None


class QueryResponseMetadata(BaseModel):
    provider_used: str
    model_used: str
    execution_time_ms: int


class AskQueryResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    query_id: int
    status: Literal["success", "blocked", "needs_clarification"]
    answer: str
    generated_sql: str | None
    blocked_reason: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    chart: ChartSuggestion = Field(default_factory=ChartSuggestion)
    metadata: QueryResponseMetadata


class QueryHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    generated_sql: str | None
    status: Literal["success", "blocked", "error", "needs_clarification"]
    blocked_reason: str | None
    answer_summary: str | None
    execution_time_ms: int | None
    provider_used: str | None
    model_used: str | None
    created_at: datetime
