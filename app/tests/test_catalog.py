from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.repositories.catalog_repository import QUERYABLE_TABLE_NAMES

client = TestClient(app)


@pytest.fixture
def authenticated_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_current_user] = lambda: object()
    yield client
    app.dependency_overrides.clear()


def get_table_names(response_payload: list[dict[str, object]]) -> set[str]:
    return {str(table["name"]) for table in response_payload}


def test_catalog_tables_returns_200(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables")

    assert response.status_code == 200


def test_catalog_tables_returns_only_allowed_tables(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables")

    assert get_table_names(response.json()) == QUERYABLE_TABLE_NAMES


def test_catalog_tables_does_not_return_users(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables")

    assert "users" not in get_table_names(response.json())


def test_catalog_tables_does_not_return_query_logs(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables")

    assert "query_logs" not in get_table_names(response.json())


def test_products_schema_returns_valid_schema(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables/products/schema")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "products"
    assert payload["queryable"] is True
    assert {column["name"] for column in payload["columns"]} == {
        "id",
        "name",
        "category",
        "price",
        "created_at",
    }
    assert all(column["description"] for column in payload["columns"])
    assert all(column["queryable"] is True for column in payload["columns"])


@pytest.mark.parametrize("table_name", ["users", "query_logs", "query_feedback"])
def test_internal_table_schema_is_blocked(authenticated_client: TestClient, table_name: str) -> None:
    response = authenticated_client.get(f"/catalog/tables/{table_name}/schema")

    assert response.status_code == 403
    assert response.json()["detail"] == f"Table '{table_name}' is internal and cannot be queried."


def test_unknown_table_schema_returns_404(authenticated_client: TestClient) -> None:
    response = authenticated_client.get("/catalog/tables/unknown/schema")

    assert response.status_code == 404
    assert response.json()["detail"] == "Table 'unknown' was not found in the queryable catalog."


def test_catalog_requires_authentication() -> None:
    response = client.get("/catalog/tables")

    assert response.status_code == 401
