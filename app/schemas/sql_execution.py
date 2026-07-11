from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SqlExecutionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    row_count: int
    execution_time_ms: int
