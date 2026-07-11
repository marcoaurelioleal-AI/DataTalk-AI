import pytest
from sqlalchemy.engine import make_url

from app.db.configure_query_role import QUERY_ROLE_NAME, build_query_role_statements, configure_query_role
from app.repositories.catalog_repository import INTERNAL_TABLE_NAMES, QUERYABLE_TABLE_NAMES


def test_query_role_statements_apply_least_privilege_allowlist() -> None:
    password = "super-secret-reader-password"
    statements = build_query_role_statements(password)
    rendered_sql = "\n".join(str(statement) for statement, _ in statements)

    assert QUERY_ROLE_NAME == "datatalk_reader"
    assert password not in rendered_sql
    assert statements[0][1] == {"password": password}
    assert "IF NOT EXISTS" in rendered_sql
    assert "NOINHERIT" in rendered_sql
    assert "NOSUPERUSER" in rendered_sql
    assert "NOBYPASSRLS" in rendered_sql
    assert "default_transaction_read_only = on" in rendered_sql
    assert "GRANT CONNECT" in rendered_sql
    assert "GRANT USAGE ON SCHEMA public" in rendered_sql
    assert "REVOKE CREATE ON SCHEMA public FROM PUBLIC" in rendered_sql
    assert "REVOKE ALL PRIVILEGES ON TABLE public.query_feedback, public.query_logs, public.users FROM PUBLIC" in rendered_sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE" in rendered_sql
    assert "FROM PUBLIC" in rendered_sql

    grant_statement = next(sql for sql, _ in statements if str(sql).startswith("GRANT SELECT ON TABLE"))
    for table_name in QUERYABLE_TABLE_NAMES:
        assert f"public.{table_name}" in str(grant_statement)
    for table_name in INTERNAL_TABLE_NAMES:
        assert f"public.{table_name}" not in str(grant_statement)

    internal_revoke = next(
        sql
        for sql, _ in statements
        if str(sql).startswith("REVOKE ALL PRIVILEGES ON TABLE")
        and all(f"public.{table_name}" in str(sql) for table_name in INTERNAL_TABLE_NAMES)
    )
    for table_name in INTERNAL_TABLE_NAMES:
        assert f"public.{table_name}" in str(internal_revoke)


def test_query_role_configuration_requires_a_password() -> None:
    with pytest.raises(ValueError, match="password"):
        build_query_role_statements("")


class MismatchedAdminEngine:
    url = make_url("postgresql+psycopg://postgres:postgres@other-db:5432/other_database")

    def begin(self) -> None:
        raise AssertionError("The admin connection must not open for a mismatched query database.")


def test_query_role_configuration_rejects_a_different_database_target() -> None:
    with pytest.raises(ValueError, match="same PostgreSQL database"):
        configure_query_role(
            "postgresql+psycopg://datatalk_reader:test@db:5432/datatalk",
            admin_engine=MismatchedAdminEngine(),
        )
