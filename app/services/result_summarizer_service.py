from datetime import date, datetime, time
from decimal import Decimal
from math import isfinite
from typing import Any

from app.schemas.sql_execution import SqlExecutionResult

TEMPORAL_COLUMN_MARKERS = ("date", "time", "period", "month", "year", "week", "day")


class ResultSummarizerService:
    def summarize(self, result: SqlExecutionResult) -> str:
        if not result.rows:
            return "A consulta não encontrou dados para os filtros informados."

        if len(result.rows) == 1 and len(result.columns) == 1:
            column = result.columns[0]
            value = result.rows[0].get(column)
            if not self._is_identifier_column(column) and self._is_number(value):
                return f"A métrica {self._label(column)} é {self._format_value(value)}."

        numeric_column = self._find_numeric_column(result)
        temporal_column = self._find_temporal_column(result)
        if numeric_column and temporal_column:
            time_summary = self._summarize_time_series(result, temporal_column, numeric_column)
            if time_summary:
                return time_summary

        category_column = self._find_category_column(result, excluded={temporal_column})
        if numeric_column and category_column:
            category_summary = self._summarize_categories(result, category_column, numeric_column)
            if category_summary:
                return category_summary

        return self._summarize_table(result)

    def _summarize_time_series(
        self,
        result: SqlExecutionResult,
        temporal_column: str,
        numeric_column: str,
    ) -> str | None:
        points: list[tuple[datetime, Any, Any]] = []
        for row in result.rows:
            parsed_date = self._parse_datetime(row.get(temporal_column))
            numeric_value = row.get(numeric_column)
            if parsed_date is not None and self._is_number(numeric_value):
                points.append((parsed_date, row.get(temporal_column), numeric_value))

        if len(points) < 2:
            return None

        points.sort(key=lambda point: point[0])
        first = points[0]
        last = points[-1]
        return (
            f"A série temporal de {self._label(numeric_column)} contém {len(points)} períodos, "
            f"de {self._format_value(first[1])} a {self._format_value(last[1])}, "
            f"começando em {self._format_value(first[2])} e terminando em {self._format_value(last[2])}."
        )

    def _summarize_categories(
        self,
        result: SqlExecutionResult,
        category_column: str,
        numeric_column: str,
    ) -> str | None:
        pairs = [
            (row.get(category_column), row.get(numeric_column))
            for row in result.rows
            if row.get(category_column) is not None and self._is_number(row.get(numeric_column))
        ]
        if len(pairs) < 2:
            return None

        values = [value for _, value in pairs]
        if all(value == values[0] for value in values[1:]):
            return (
                f"As {len(pairs)} categorias retornaram o mesmo {self._label(numeric_column)}: "
                f"{self._format_value(values[0])}."
            )

        if all(current >= following for current, following in zip(values, values[1:])):
            ranking_items = [
                f"{self._format_value(category)} ({self._format_value(value)})"
                for category, value in pairs[:3]
            ]
            return f"Ranking por {self._label(numeric_column)}: {self._join_items(ranking_items)}."

        highest_category, highest_value = max(pairs, key=lambda pair: pair[1])
        lowest_category, lowest_value = min(pairs, key=lambda pair: pair[1])
        return (
            f"Na comparação por {self._label(category_column)}, "
            f"{self._format_value(highest_category)} tem o maior {self._label(numeric_column)} "
            f"({self._format_value(highest_value)}) e {self._format_value(lowest_category)} o menor "
            f"({self._format_value(lowest_value)})."
        )

    def _summarize_table(self, result: SqlExecutionResult) -> str:
        record_count = len(result.rows)
        column_count = len(result.columns)
        columns = self._join_items([self._label(column) for column in result.columns])
        return f"A consulta retornou {record_count} registros em {column_count} colunas: {columns}."

    def _find_numeric_column(self, result: SqlExecutionResult) -> str | None:
        for column in result.columns:
            if self._is_identifier_column(column):
                continue
            values = [row.get(column) for row in result.rows if row.get(column) is not None]
            if values and all(self._is_number(value) for value in values):
                return column
        return None

    def _find_temporal_column(self, result: SqlExecutionResult) -> str | None:
        for column in result.columns:
            normalized_name = column.lower()
            if not any(marker in normalized_name for marker in TEMPORAL_COLUMN_MARKERS):
                continue
            if any(self._parse_datetime(row.get(column)) is not None for row in result.rows):
                return column
        return None

    def _find_category_column(self, result: SqlExecutionResult, excluded: set[str | None]) -> str | None:
        for column in result.columns:
            if column in excluded:
                continue
            values = [row.get(column) for row in result.rows if row.get(column) is not None]
            if values and all(isinstance(value, str) for value in values):
                return column
        return None

    def _parse_datetime(self, value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min)
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.combine(date.fromisoformat(value), time.min)
            except ValueError:
                return None

    def _is_number(self, value: Any) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, Decimal):
            return value.is_finite()
        if isinstance(value, float):
            return isfinite(value)
        return isinstance(value, int)

    def _format_value(self, value: Any) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def _label(self, column: str) -> str:
        return column.replace("_", " ")

    def _is_identifier_column(self, column: str) -> bool:
        normalized_column = column.lower()
        return normalized_column == "id" or normalized_column.endswith("_id")

    def _join_items(self, items: list[str]) -> str:
        if len(items) <= 1:
            return "".join(items)
        return f"{', '.join(items[:-1])} e {items[-1]}"
