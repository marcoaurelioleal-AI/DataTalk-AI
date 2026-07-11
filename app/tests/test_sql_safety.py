import pytest

from app.services.sql_safety_service import SqlSafetyService

validator = SqlSafetyService()


def test_allows_safe_select_with_limit() -> None:
    result = validator.validate("SELECT id, name, price FROM products LIMIT 20")

    assert result.is_valid is True
    assert result.reason is None
    assert result.detected_tables == ("products",)


@pytest.mark.parametrize(
    ("command", "sql"),
    [
        ("DELETE", "DELETE FROM orders WHERE status = 'cancelled'"),
        ("UPDATE", "UPDATE products SET price = 1"),
        ("INSERT", "INSERT INTO products (name) VALUES ('Injected')"),
        ("DROP", "DROP TABLE products"),
        ("ALTER", "ALTER TABLE products ADD COLUMN injected INTEGER"),
        ("TRUNCATE", "TRUNCATE TABLE orders"),
        ("CREATE", "CREATE TABLE injected (id INTEGER)"),
        ("REPLACE", "REPLACE INTO products (id) VALUES (1)"),
        ("GRANT", "GRANT SELECT ON products TO public"),
        ("REVOKE", "REVOKE SELECT ON products FROM public"),
        ("MERGE", "MERGE INTO products USING orders ON products.id = orders.id"),
        ("CALL", "CALL refresh_products()"),
        ("EXEC", "EXEC refresh_products"),
    ],
)
def test_blocks_prohibited_commands(command: str, sql: str) -> None:
    result = validator.validate(sql)

    assert result.is_valid is False
    assert result.reason == f"Comando {command} detectado."


def test_blocks_non_select_statement() -> None:
    result = validator.validate("EXPLAIN SELECT id FROM products LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "A query deve ser uma consulta SELECT segura."


def test_blocks_multiple_statements() -> None:
    result = validator.validate("SELECT id FROM products LIMIT 10; SELECT id FROM orders LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Multiplas statements nao sao permitidas."


def test_allows_single_terminal_semicolon() -> None:
    result = validator.validate("SELECT id FROM products LIMIT 10;")

    assert result.is_valid is True
    assert result.normalized_sql == "SELECT id FROM products LIMIT 10"


def test_blocks_select_star() -> None:
    result = validator.validate("SELECT * FROM products LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "SELECT * nao e permitido."


def test_blocks_qualified_select_star() -> None:
    result = validator.validate("SELECT p.* FROM products p LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "SELECT * nao e permitido."


def test_blocks_query_without_limit() -> None:
    result = validator.validate("SELECT id, name FROM products")

    assert result.is_valid is False
    assert result.reason == "A query deve possuir LIMIT."


def test_blocks_limit_above_configured_maximum() -> None:
    result = validator.validate("SELECT id, name FROM products LIMIT 101")

    assert result.is_valid is False
    assert result.reason == "LIMIT 101 excede o maximo permitido de 100."


@pytest.mark.parametrize("table_name", ["users", "query_logs", "query_feedback"])
def test_blocks_internal_tables(table_name: str) -> None:
    result = validator.validate(f"SELECT id FROM {table_name} LIMIT 10")

    assert result.is_valid is False
    assert result.reason == f"Tabela interna '{table_name}' nao pode ser consultada."
    assert result.detected_tables == (table_name,)


def test_blocks_unknown_table() -> None:
    result = validator.validate("SELECT id FROM invoices LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Tabela 'invoices' nao esta na allowlist."


def test_allows_join_between_queryable_tables() -> None:
    result = validator.validate(
        "SELECT p.name, oi.quantity "
        "FROM products p "
        "JOIN order_items oi ON oi.product_id = p.id "
        "JOIN orders o ON o.id = oi.order_id "
        "LIMIT 20"
    )

    assert result.is_valid is True
    assert result.detected_tables == ("products", "order_items", "orders")


def test_detects_tables_with_aliases() -> None:
    result = validator.validate("SELECT oi.quantity, c.name FROM order_items oi JOIN campaigns c ON c.id = oi.id LIMIT 10")

    assert result.is_valid is True
    assert result.detected_tables == ("order_items", "campaigns")


def test_normalizes_excess_whitespace_and_preserves_original_sql() -> None:
    sql = "  SELECT p.name,\n  p.price   FROM products p\n LIMIT 5;  "

    result = validator.validate(sql)

    assert result.is_valid is True
    assert result.original_sql == sql
    assert result.normalized_sql == "SELECT p.name, p.price FROM products p LIMIT 5"


def test_semicolon_inside_string_literal_does_not_create_second_statement() -> None:
    result = validator.validate("SELECT name FROM products WHERE name = 'Desk; Pro' LIMIT 1")

    assert result.is_valid is True


def test_prohibited_word_inside_string_literal_does_not_block_query() -> None:
    result = validator.validate("SELECT name FROM products WHERE name = 'UPDATE Pack' LIMIT 1")

    assert result.is_valid is True


def test_blocks_comma_separated_table_sources() -> None:
    result = validator.validate("SELECT p.name, o.id FROM products p, orders o LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Use JOIN explicito para consultar multiplas tabelas."


def test_blocks_sql_comments() -> None:
    result = validator.validate("SELECT id FROM products -- hidden clause\nLIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Comentarios SQL nao sao permitidos."


def test_blocks_select_into() -> None:
    result = validator.validate("SELECT id INTO leaked_products FROM products LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Construcao INTO nao e permitida."


def test_blocks_union_queries() -> None:
    result = validator.validate("SELECT id FROM products UNION SELECT id FROM orders LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Construcao UNION nao e permitida."


def test_blocks_select_without_queryable_table() -> None:
    result = validator.validate("SELECT current_user LIMIT 1")

    assert result.is_valid is False
    assert result.reason == "A query deve consultar ao menos uma tabela permitida."


def test_allows_safe_cte() -> None:
    result = validator.validate(
        "WITH recent_products AS ("
        "SELECT id, name FROM products WHERE price > 100"
        ") "
        "SELECT id, name FROM recent_products LIMIT 10"
    )

    assert result.is_valid is True
    assert result.detected_tables == ("products",)


def test_blocks_write_command_inside_cte() -> None:
    result = validator.validate(
        "WITH deleted_orders AS ("
        "DELETE FROM orders WHERE status = 'cancelled' RETURNING id"
        ") "
        "SELECT id FROM deleted_orders LIMIT 10"
    )

    assert result.is_valid is False
    assert result.reason == "Comando DELETE detectado."


def test_allows_safe_subquery() -> None:
    result = validator.validate(
        "SELECT name FROM products "
        "WHERE id IN (SELECT product_id FROM order_items WHERE quantity > 1) "
        "LIMIT 10"
    )

    assert result.is_valid is True
    assert result.detected_tables == ("products", "order_items")


def test_allows_public_schema_qualified_table() -> None:
    result = validator.validate("SELECT p.id, p.name FROM public.products p LIMIT 10")

    assert result.is_valid is True
    assert result.detected_tables == ("products",)


def test_blocks_non_public_schema() -> None:
    result = validator.validate("SELECT p.id FROM analytics.products p LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "Schema 'analytics' nao e permitido."


@pytest.mark.parametrize("schema_name", ["pg_catalog", "information_schema"])
def test_blocks_system_schemas(schema_name: str) -> None:
    result = validator.validate(f"SELECT t.table_name FROM {schema_name}.tables t LIMIT 10")

    assert result.is_valid is False
    assert result.reason == f"Schema de sistema '{schema_name}' nao pode ser consultado."


@pytest.mark.parametrize(
    "function_name",
    ["pg_sleep", "pg_read_file", "pg_ls_dir", "lo_export", "dblink", "set_config"],
)
def test_blocks_dangerous_functions(function_name: str) -> None:
    result = validator.validate(f"SELECT {function_name}('test') FROM products LIMIT 1")

    assert result.is_valid is False
    assert result.reason == f"Funcao perigosa '{function_name}' nao e permitida."


def test_blocks_wildcard_inside_aggregate() -> None:
    result = validator.validate("SELECT COUNT(*) AS total FROM products LIMIT 1")

    assert result.is_valid is False
    assert result.reason == "SELECT * nao e permitido."


@pytest.mark.parametrize(
    "limit_clause",
    ["LIMIT ALL", "LIMIT 1 + 1", "LIMIT -1", "LIMIT $1"],
)
def test_blocks_non_literal_integer_limit(limit_clause: str) -> None:
    result = validator.validate(f"SELECT id FROM products {limit_clause}")

    assert result.is_valid is False
    assert result.reason == "A query deve possuir exatamente um LIMIT inteiro."


def test_blocks_row_locking_clause() -> None:
    result = validator.validate("SELECT id FROM products LIMIT 10 FOR UPDATE")

    assert result.is_valid is False
    assert result.reason == "Consultas com bloqueio de linhas nao sao permitidas."


def test_cte_alias_does_not_hide_internal_table_in_outer_scope() -> None:
    result = validator.validate(
        "SELECT u.id FROM users u "
        "WHERE EXISTS ("
        "WITH users AS (SELECT id FROM products) "
        "SELECT id FROM users LIMIT 1"
        ") "
        "LIMIT 1"
    )

    assert result.is_valid is False
    assert result.reason == "Tabela interna 'users' nao pode ser consultada."
    assert "users" in result.detected_tables


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT p.id FROM (SELECT id FROM products FOR SHARE) p LIMIT 10",
        "WITH p AS (SELECT id FROM products FOR SHARE) SELECT id FROM p LIMIT 10",
        "SELECT p.id FROM (SELECT id FROM products FOR KEY SHARE) p LIMIT 10",
    ],
)
def test_blocks_nested_row_locking_clause(sql: str) -> None:
    result = validator.validate(sql)

    assert result.is_valid is False
    assert result.reason == "Consultas com bloqueio de linhas nao sao permitidas."


def test_allows_explicit_join_with_multi_argument_function() -> None:
    result = validator.validate(
        "SELECT p.id, o.id AS order_id "
        "FROM products p "
        "JOIN orders o ON COALESCE(p.id, 0) = o.id "
        "LIMIT 10"
    )

    assert result.is_valid is True
    assert result.detected_tables == ("products", "orders")
