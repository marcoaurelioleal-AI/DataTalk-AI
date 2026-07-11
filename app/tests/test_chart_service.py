from decimal import Decimal

from app.schemas.sql_execution import SqlExecutionResult
from app.services.chart_service import ChartRecommendationService


chart_service = ChartRecommendationService()


def make_result(columns: list[str], rows: list[dict[str, object]]) -> SqlExecutionResult:
    return SqlExecutionResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=1,
    )


def test_recommends_table_for_empty_result() -> None:
    recommendation = chart_service.recommend(make_result(["product_name", "total_sold"], []))

    assert recommendation.model_dump() == {"type": "table", "x": None, "y": None}


def test_recommends_metric_for_single_numeric_value() -> None:
    result = make_result(
        ["label", "total_revenue"],
        [{"label": "Receita total", "total_revenue": Decimal("12500.75")}],
    )

    assert chart_service.recommend(result).model_dump() == {
        "type": "metric",
        "x": None,
        "y": "total_revenue",
    }


def test_recommends_line_for_time_series() -> None:
    result = make_result(
        ["order_date", "total_revenue"],
        [
            {"order_date": "2026-07-01", "total_revenue": 100},
            {"order_date": "2026-07-02", "total_revenue": 150},
        ],
    )

    assert chart_service.recommend(result).model_dump() == {
        "type": "line",
        "x": "order_date",
        "y": "total_revenue",
    }


def test_recommends_pie_for_percentage_share_with_few_categories() -> None:
    result = make_result(
        ["channel_name", "revenue_percentage"],
        [
            {"channel_name": "Website", "revenue_percentage": 40},
            {"channel_name": "Marketplace", "revenue_percentage": 35},
            {"channel_name": "App Mobile", "revenue_percentage": 25},
        ],
    )

    assert chart_service.recommend(result).model_dump() == {
        "type": "pie",
        "x": "channel_name",
        "y": "revenue_percentage",
    }


def test_recommends_bar_for_category_and_number() -> None:
    result = make_result(
        ["product_name", "total_sold"],
        [
            {"product_name": "Notebook Pro", "total_sold": 128},
            {"product_name": "Mouse Gamer", "total_sold": 80},
        ],
    )

    assert chart_service.recommend(result).model_dump() == {
        "type": "bar",
        "x": "product_name",
        "y": "total_sold",
    }


def test_uses_bar_when_percentage_result_has_too_many_categories_for_pie() -> None:
    rows = [
        {"category_name": f"Categoria {index}", "share_percent": value}
        for index, value in enumerate([20, 18, 16, 14, 12, 10, 10], start=1)
    ]

    recommendation = chart_service.recommend(make_result(["category_name", "share_percent"], rows))

    assert recommendation.model_dump() == {
        "type": "bar",
        "x": "category_name",
        "y": "share_percent",
    }


def test_allows_bar_when_some_numeric_values_are_null() -> None:
    result = make_result(
        ["channel_name", "total_revenue"],
        [
            {"channel_name": "Website", "total_revenue": 100},
            {"channel_name": "Marketplace", "total_revenue": None},
            {"channel_name": "App Mobile", "total_revenue": 150},
        ],
    )

    assert chart_service.recommend(result).model_dump() == {
        "type": "bar",
        "x": "channel_name",
        "y": "total_revenue",
    }


def test_recommends_table_for_identifiers_or_invalid_numbers() -> None:
    identifier_result = make_result(
        ["customer_name", "customer_id"],
        [
            {"customer_name": "Ana", "customer_id": 1},
            {"customer_name": "Bruno", "customer_id": 2},
        ],
    )
    invalid_number_result = make_result(
        ["product_name", "total_sold"],
        [
            {"product_name": "Notebook Pro", "total_sold": float("nan")},
            {"product_name": "Mouse Gamer", "total_sold": float("inf")},
        ],
    )

    assert chart_service.recommend(identifier_result).type == "table"
    assert chart_service.recommend(invalid_number_result).type == "table"


def test_never_references_columns_outside_the_execution_result() -> None:
    result = make_result(
        ["channel_name"],
        [{"channel_name": "Website", "hidden_total": 100}],
    )

    recommendation = chart_service.recommend(result)

    assert recommendation.type == "table"
    assert recommendation.x is None
    assert recommendation.y is None
