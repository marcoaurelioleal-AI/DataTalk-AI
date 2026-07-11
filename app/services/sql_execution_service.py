from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from math import isfinite
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.schemas.sql_execution import SqlExecutionResult
from app.services.sql_safety_service import SqlSafetyService


class SqlExecutionError(Exception):
    """Safe domain error for failures while executing approved SQL."""


class SqlExecutionRejectedError(SqlExecutionError):
    """Raised when SQL fails the final safety validation."""


class SqlExecutionService:
    def __init__(
        self,
        engine: Engine | None = None,
        safety_service: SqlSafetyService | None = None,
        max_rows: int | None = None,
        statement_timeout_ms: int | None = None,
        lock_timeout_ms: int | None = None,
    ) -> None:
        if engine is None:
            from app.db.database import query_engine

            engine = query_engine

        self.engine = engine
        self.max_rows = settings.query_max_rows if max_rows is None else max_rows
        self.statement_timeout_ms = (
            settings.query_statement_timeout_ms if statement_timeout_ms is None else statement_timeout_ms
        )
        self.lock_timeout_ms = settings.query_lock_timeout_ms if lock_timeout_ms is None else lock_timeout_ms
        self.safety_service = safety_service or SqlSafetyService(max_rows=self.max_rows)

        if self.max_rows < 1:
            raise ValueError("max_rows must be greater than zero.")
        if self.statement_timeout_ms < 1:
            raise ValueError("statement_timeout_ms must be greater than zero.")
        if self.lock_timeout_ms < 1:
            raise ValueError("lock_timeout_ms must be greater than zero.")

    def execute(self, sql: str) -> SqlExecutionResult:
        safety_result = self.safety_service.validate(sql)
        if not safety_result.is_valid:
            reason = safety_result.reason or "A consulta nao foi aprovada pelo validador de seguranca."
            raise SqlExecutionRejectedError(reason)

        started_at = perf_counter()
        try:
            with self.engine.connect() as connection:
                transaction = connection.begin()
                try:
                    if connection.dialect.name == "postgresql":
                        connection.execute(text("SET TRANSACTION READ ONLY"))
                        connection.execute(
                            text(f"SET LOCAL statement_timeout = '{self.statement_timeout_ms}ms'")
                        )
                        connection.execute(text(f"SET LOCAL lock_timeout = '{self.lock_timeout_ms}ms'"))

                    result = connection.execute(text(safety_result.normalized_sql))
                    columns = [str(column) for column in result.keys()]
                    raw_rows = result.mappings().fetchmany(self.max_rows + 1)
                    rows = [
                        {str(key): self._json_safe(value) for key, value in dict(row).items()}
                        for row in raw_rows[: self.max_rows]
                    ]
                finally:
                    transaction.rollback()
        except SQLAlchemyError as error:
            raise SqlExecutionError("Nao foi possivel executar a consulta aprovada.") from error

        execution_time_ms = max(0, round((perf_counter() - started_at) * 1000))
        return SqlExecutionResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
        )

    def _json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, bool)):
            return value
        if isinstance(value, float):
            return value if isfinite(value) else None
        if isinstance(value, Decimal):
            return float(value) if value.is_finite() else None
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return self._json_safe(value.value)
        if isinstance(value, dict):
            return {str(key): self._json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._json_safe(item) for item in value]
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)
