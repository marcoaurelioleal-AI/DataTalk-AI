from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.elements import TextClause

from app.core.config import Settings
from app.services.sql_execution_service import (
    SqlExecutionError,
    SqlExecutionRejectedError,
    SqlExecutionService,
)


class FakeTransaction:
    def __init__(self) -> None:
        self.rolled_back = False

    def rollback(self) -> None:
        self.rolled_back = True


class FakeMappings:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.fetchmany_size: int | None = None

    def fetchmany(self, size: int) -> list[dict[str, Any]]:
        self.fetchmany_size = size
        return self.rows[:size]


class FakeResult:
    def __init__(self, columns: list[str], rows: list[dict[str, Any]]) -> None:
        self._columns = columns
        self._mappings = FakeMappings(rows)

    def keys(self) -> list[str]:
        return self._columns

    def mappings(self) -> FakeMappings:
        return self._mappings


class FakeDialect:
    name = "postgresql"


class FakeConnection:
    dialect = FakeDialect()

    def __init__(self, result: FakeResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.transaction = FakeTransaction()
        self.executions: list[tuple[Any, dict[str, Any] | None]] = []

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def begin(self) -> FakeTransaction:
        return self.transaction

    def execute(self, statement: Any, parameters: dict[str, Any] | None = None) -> FakeResult:
        self.executions.append((statement, parameters))
        if str(statement).lstrip().upper().startswith("SELECT"):
            if self.error:
                raise self.error
            assert self.result is not None
            return self.result
        return FakeResult([], [])


class FakeEngine:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.connect_calls = 0

    def connect(self) -> FakeConnection:
        self.connect_calls += 1
        return self.connection


def test_revalidates_and_rejects_sql_before_opening_connection() -> None:
    engine = FakeEngine(FakeConnection())
    service = SqlExecutionService(engine=engine)

    with pytest.raises(SqlExecutionRejectedError, match="Comando DELETE detectado"):
        service.execute("DELETE FROM orders")

    assert engine.connect_calls == 0


def test_executes_with_read_only_guards_and_returns_json_safe_rows() -> None:
    identifier = UUID("8f14e45f-ea5e-4e1e-9de3-29d6bb4f534f")
    rows = [
        {
            "product_name": "Notebook Pro",
            "total_sold": Decimal("128.50"),
            "sale_date": date(2026, 7, 10),
            "created_at": datetime(2026, 7, 10, 12, 30, tzinfo=timezone.utc),
            "reference": identifier,
            "invalid_float": float("nan"),
            "invalid_decimal": Decimal("Infinity"),
        },
        {
            "product_name": "Mouse Gamer",
            "total_sold": Decimal("90"),
            "sale_date": date(2026, 7, 9),
            "created_at": datetime(2026, 7, 9, 9, 15),
            "reference": identifier,
            "invalid_float": float("inf"),
            "invalid_decimal": Decimal("NaN"),
        },
        {
            "product_name": "Ignored defensive overflow",
            "total_sold": Decimal("1"),
            "sale_date": date(2026, 7, 8),
            "created_at": datetime(2026, 7, 8, 8, 0),
            "reference": identifier,
            "invalid_float": float("-inf"),
            "invalid_decimal": Decimal("-Infinity"),
        },
    ]
    result_proxy = FakeResult(list(rows[0]), rows)
    connection = FakeConnection(result=result_proxy)
    service = SqlExecutionService(
        engine=FakeEngine(connection),
        max_rows=2,
        statement_timeout_ms=4_000,
        lock_timeout_ms=800,
    )

    result = service.execute(
        "SELECT p.name AS product_name, p.price AS total_sold, "
        "p.created_at AS sale_date, p.created_at, p.id AS reference "
        "FROM products p LIMIT 2"
    )

    assert result.columns == list(rows[0])
    assert result.row_count == 2
    assert result.rows[0] == {
        "product_name": "Notebook Pro",
        "total_sold": 128.5,
        "sale_date": "2026-07-10",
        "created_at": "2026-07-10T12:30:00+00:00",
        "reference": str(identifier),
        "invalid_float": None,
        "invalid_decimal": None,
    }
    assert result.execution_time_ms >= 0
    assert result_proxy._mappings.fetchmany_size == 3
    assert connection.transaction.rolled_back is True

    executed_sql = [str(statement) for statement, _ in connection.executions]
    assert executed_sql[:3] == [
        "SET TRANSACTION READ ONLY",
        "SET LOCAL statement_timeout = '4000ms'",
        "SET LOCAL lock_timeout = '800ms'",
    ]
    assert isinstance(connection.executions[3][0], TextClause)
    assert executed_sql[3].endswith("FROM products p LIMIT 2")


def test_converts_database_failures_to_safe_domain_error_and_rolls_back() -> None:
    connection = FakeConnection(error=SQLAlchemyError("password=secret internal driver failure"))
    service = SqlExecutionService(engine=FakeEngine(connection))

    with pytest.raises(SqlExecutionError) as captured_error:
        service.execute("SELECT id FROM products LIMIT 1")

    assert str(captured_error.value) == "Nao foi possivel executar a consulta aprovada."
    assert "secret" not in str(captured_error.value)
    assert connection.transaction.rolled_back is True


def test_settings_expose_dedicated_query_connection_and_timeouts() -> None:
    configured_settings = Settings(
        _env_file=None,
        QUERY_DATABASE_URL="postgresql+psycopg://datatalk_reader:test@db:5432/datatalk",
        QUERY_STATEMENT_TIMEOUT_MS=3_000,
        QUERY_LOCK_TIMEOUT_MS=700,
    )

    assert configured_settings.query_database_url.startswith("postgresql+psycopg://datatalk_reader:")
    assert configured_settings.query_statement_timeout_ms == 3_000
    assert configured_settings.query_lock_timeout_ms == 700


@pytest.mark.parametrize("field_name", ["QUERY_STATEMENT_TIMEOUT_MS", "QUERY_LOCK_TIMEOUT_MS"])
def test_settings_reject_non_positive_query_timeouts(field_name: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field_name: 0})
