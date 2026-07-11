from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.sql.elements import TextClause

from app.core.config import settings
from app.repositories.catalog_repository import INTERNAL_TABLE_NAMES, QUERYABLE_TABLE_NAMES

QUERY_ROLE_NAME = "datatalk_reader"


def build_query_role_statements(password: str) -> Sequence[tuple[TextClause, dict[str, str] | None]]:
    if not password:
        raise ValueError("The query database password is required.")

    queryable_tables = ", ".join(f"public.{table_name}" for table_name in sorted(QUERYABLE_TABLE_NAMES))
    internal_tables = ", ".join(f"public.{table_name}" for table_name in sorted(INTERNAL_TABLE_NAMES))

    role_upsert = f"""
DO $role$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{QUERY_ROLE_NAME}') THEN
        EXECUTE format(
            'CREATE ROLE {QUERY_ROLE_NAME} WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
            current_setting('datatalk.reader_password')
        );
    ELSE
        EXECUTE format(
            'ALTER ROLE {QUERY_ROLE_NAME} WITH LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD %L',
            current_setting('datatalk.reader_password')
        );
    END IF;
END
$role$
""".strip()

    database_privileges = f"""
DO $database_privileges$
BEGIN
    EXECUTE format('REVOKE TEMPORARY ON DATABASE %I FROM PUBLIC', current_database());
    EXECUTE format('REVOKE ALL PRIVILEGES ON DATABASE %I FROM {QUERY_ROLE_NAME}', current_database());
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO {QUERY_ROLE_NAME}', current_database());
END
$database_privileges$
""".strip()

    return (
        (text("SELECT set_config('datatalk.reader_password', :password, true)"), {"password": password}),
        (text(role_upsert), None),
        (text(database_privileges), None),
        (text(f"ALTER ROLE {QUERY_ROLE_NAME} SET default_transaction_read_only = on"), None),
        (text(f"REVOKE ALL PRIVILEGES ON SCHEMA public FROM {QUERY_ROLE_NAME}"), None),
        (text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"), None),
        (text(f"REVOKE CREATE ON SCHEMA public FROM {QUERY_ROLE_NAME}"), None),
        (text(f"GRANT USAGE ON SCHEMA public TO {QUERY_ROLE_NAME}"), None),
        (text(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {QUERY_ROLE_NAME}"), None),
        (text(f"REVOKE ALL PRIVILEGES ON TABLE {internal_tables} FROM PUBLIC"), None),
        (text(f"REVOKE ALL PRIVILEGES ON TABLE {internal_tables} FROM {QUERY_ROLE_NAME}"), None),
        (
            text(
                "REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER "
                f"ON TABLE {queryable_tables} FROM PUBLIC"
            ),
            None,
        ),
        (text(f"GRANT SELECT ON TABLE {queryable_tables} TO {QUERY_ROLE_NAME}"), None),
        (
            text(
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                f"REVOKE ALL PRIVILEGES ON TABLES FROM {QUERY_ROLE_NAME}"
            ),
            None,
        ),
    )


def configure_query_role(
    query_database_url: str | None = None,
    admin_engine: Engine | None = None,
) -> None:
    configured_url = make_url(query_database_url or settings.query_database_url)
    if configured_url.username != QUERY_ROLE_NAME:
        raise ValueError(f"QUERY_DATABASE_URL must use the '{QUERY_ROLE_NAME}' role.")
    if not configured_url.password:
        raise ValueError("QUERY_DATABASE_URL must include a password.")

    if admin_engine is None:
        from app.db.database import engine

        admin_engine = engine

    admin_url = make_url(str(admin_engine.url))
    admin_target = (admin_url.host, admin_url.port or 5432, admin_url.database)
    query_target = (configured_url.host, configured_url.port or 5432, configured_url.database)
    if admin_target != query_target:
        raise ValueError("DATABASE_URL and QUERY_DATABASE_URL must target the same PostgreSQL database.")

    with admin_engine.begin() as connection:
        for statement, parameters in build_query_role_statements(configured_url.password):
            connection.execute(statement, parameters or {})


if __name__ == "__main__":
    configure_query_role()
