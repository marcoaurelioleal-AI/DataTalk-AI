from pydantic import BaseModel, ConfigDict


class SqlSafetyResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_valid: bool
    reason: str | None
    original_sql: str
    normalized_sql: str
    detected_tables: tuple[str, ...]
