from app.schemas.sql_execution import SqlExecutionResult
from app.services.result_summarizer_service import ResultSummarizerService


summarizer = ResultSummarizerService()


def make_result(columns: list[str], rows: list[dict[str, object]]) -> SqlExecutionResult:
    return SqlExecutionResult(
        columns=columns,
        rows=rows,
        row_count=len(rows),
        execution_time_ms=1,
    )


def test_summarizes_empty_result() -> None:
    result = make_result(["product_name", "total_sold"], [])

    assert summarizer.summarize(result) == "A consulta não encontrou dados para os filtros informados."


def test_summarizes_single_metric() -> None:
    result = make_result(["total_revenue"], [{"total_revenue": 12500.75}])

    assert summarizer.summarize(result) == "A métrica total revenue é 12500.75."


def test_summarizes_descending_category_result_as_ranking() -> None:
    result = make_result(
        ["product_name", "total_sold"],
        [
            {"product_name": "Notebook Pro", "total_sold": 128},
            {"product_name": "Smartwatch X", "total_sold": 96},
            {"product_name": "Mouse Gamer", "total_sold": 80},
        ],
    )

    assert summarizer.summarize(result) == (
        "Ranking por total sold: Notebook Pro (128), Smartwatch X (96) e Mouse Gamer (80)."
    )


def test_summarizes_unsorted_category_result_as_comparison() -> None:
    result = make_result(
        ["channel_name", "total_revenue"],
        [
            {"channel_name": "Website", "total_revenue": 100},
            {"channel_name": "Marketplace", "total_revenue": 200},
            {"channel_name": "App Mobile", "total_revenue": 150},
        ],
    )

    assert summarizer.summarize(result) == (
        "Na comparação por channel name, Marketplace tem o maior total revenue (200) "
        "e Website o menor (100)."
    )


def test_summarizes_time_series_in_chronological_order() -> None:
    result = make_result(
        ["order_date", "total_revenue"],
        [
            {"order_date": "2026-07-03", "total_revenue": 150},
            {"order_date": "2026-07-01", "total_revenue": 100},
            {"order_date": "2026-07-02", "total_revenue": 250},
        ],
    )

    assert summarizer.summarize(result) == (
        "A série temporal de total revenue contém 3 períodos, de 2026-07-01 a 2026-07-03, "
        "começando em 100 e terminando em 150."
    )


def test_summarizes_equal_category_values_without_inventing_a_ranking() -> None:
    result = make_result(
        ["channel_name", "total_revenue"],
        [
            {"channel_name": "Website", "total_revenue": 100},
            {"channel_name": "Marketplace", "total_revenue": 100},
            {"channel_name": "App Mobile", "total_revenue": 100},
        ],
    )

    assert summarizer.summarize(result) == "As 3 categorias retornaram o mesmo total revenue: 100."


def test_falls_back_to_generic_table_summary() -> None:
    result = make_result(
        ["id", "name", "email"],
        [
            {"id": 1, "name": "Ana", "email": "ana@example.com"},
            {"id": 2, "name": "Bruno", "email": "bruno@example.com"},
        ],
    )

    assert summarizer.summarize(result) == "A consulta retornou 2 registros em 3 colunas: id, name e email."


def test_ignores_null_values_when_there_is_not_enough_data_to_compare() -> None:
    result = make_result(
        ["channel_name", "total_revenue"],
        [
            {"channel_name": "Website", "total_revenue": None},
            {"channel_name": "Marketplace", "total_revenue": 200},
        ],
    )

    assert summarizer.summarize(result) == (
        "A consulta retornou 2 registros em 2 colunas: channel name e total revenue."
    )
