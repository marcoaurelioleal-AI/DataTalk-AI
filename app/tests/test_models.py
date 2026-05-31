import app.models  # noqa: F401
from app.db.base import Base


def test_metadata_contains_expected_tables() -> None:
    expected_tables = {
        "users",
        "customers",
        "products",
        "sales_channels",
        "campaigns",
        "orders",
        "order_items",
        "query_logs",
        "query_feedback",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_internal_tables_are_present_for_future_auditability() -> None:
    assert "users" in Base.metadata.tables
    assert "query_logs" in Base.metadata.tables
    assert "query_feedback" in Base.metadata.tables
