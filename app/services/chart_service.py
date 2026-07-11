from datetime import date, datetime
from decimal import Decimal
from math import isclose, isfinite
from typing import Any, Literal

from app.schemas.query import ChartSuggestion
from app.schemas.sql_execution import SqlExecutionResult

TEMPORAL_COLUMN_MARKERS = ("date", "time", "period", "month", "year", "week", "day")
PERCENTAGE_COLUMN_MARKERS = (
    "percentage",
    "percent",
    "share",
    "participation",
    "participacao",
    "participação",
    "pct",
)


class ChartRecommendationService:
    def recommend(self, result: SqlExecutionResult) -> ChartSuggestion:
        if not result.columns or not result.rows:
            return self._table()

        numeric_columns = self._numeric_columns(result)
        if len(result.rows) == 1 and numeric_columns:
            return self._suggest("metric", None, numeric_columns[0], result.columns)

        numeric_column = self._first_column_with_values(result, numeric_columns, minimum_values=2)
        if numeric_column is None:
            return self._table()

        temporal_column = self._temporal_column(result)
        if temporal_column is not None:
            return self._suggest("line", temporal_column, numeric_column, result.columns)

        category_column = self._category_column(result)
        if category_column is None:
            return self._table()

        if self._is_percentage_share(result, category_column, numeric_column):
            return self._suggest("pie", category_column, numeric_column, result.columns)

        return self._suggest("bar", category_column, numeric_column, result.columns)

    def _numeric_columns(self, result: SqlExecutionResult) -> list[str]:
        columns: list[str] = []
        for column in result.columns:
            if self._is_identifier_column(column):
                continue
            values = [row.get(column) for row in result.rows if row.get(column) is not None]
            if values and all(self._is_number(value) for value in values):
                columns.append(column)
        return columns

    def _first_column_with_values(
        self,
        result: SqlExecutionResult,
        columns: list[str],
        minimum_values: int,
    ) -> str | None:
        for column in columns:
            valid_values = [row.get(column) for row in result.rows if self._is_number(row.get(column))]
            if len(valid_values) >= minimum_values:
                return column
        return None

    def _temporal_column(self, result: SqlExecutionResult) -> str | None:
        for column in result.columns:
            normalized_name = column.lower()
            if not any(marker in normalized_name for marker in TEMPORAL_COLUMN_MARKERS):
                continue
            values = [row.get(column) for row in result.rows if row.get(column) is not None]
            if len(values) >= 2 and all(self._is_temporal(value) for value in values):
                return column
        return None

    def _category_column(self, result: SqlExecutionResult) -> str | None:
        for column in result.columns:
            values = [row.get(column) for row in result.rows]
            if len(values) >= 2 and all(isinstance(value, str) and bool(value.strip()) for value in values):
                return column
        return None

    def _is_percentage_share(
        self,
        result: SqlExecutionResult,
        category_column: str,
        numeric_column: str,
    ) -> bool:
        if not 2 <= len(result.rows) <= 6:
            return False
        if not any(marker in numeric_column.lower() for marker in PERCENTAGE_COLUMN_MARKERS):
            return False

        values: list[float] = []
        for row in result.rows:
            if not isinstance(row.get(category_column), str) or not self._is_number(row.get(numeric_column)):
                return False
            value = float(row[numeric_column])
            if value < 0:
                return False
            values.append(value)

        total = sum(values)
        return isclose(total, 100.0, abs_tol=0.5) or isclose(total, 1.0, abs_tol=0.01)

    def _is_temporal(self, value: Any) -> bool:
        if isinstance(value, (datetime, date)):
            return True
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return True
        except ValueError:
            try:
                date.fromisoformat(value)
                return True
            except ValueError:
                return False

    def _is_number(self, value: Any) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, Decimal):
            return value.is_finite()
        if isinstance(value, float):
            return isfinite(value)
        return isinstance(value, int)

    def _is_identifier_column(self, column: str) -> bool:
        normalized_column = column.lower()
        return normalized_column == "id" or normalized_column.endswith("_id")

    def _suggest(
        self,
        chart_type: Literal["bar", "line", "pie", "metric"],
        x: str | None,
        y: str | None,
        columns: list[str],
    ) -> ChartSuggestion:
        if (x is not None and x not in columns) or (y is not None and y not in columns):
            return self._table()
        return ChartSuggestion(type=chart_type, x=x, y=y)

    def _table(self) -> ChartSuggestion:
        return ChartSuggestion(type="table")
