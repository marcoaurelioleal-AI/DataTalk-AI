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


def test_blocks_query_that_does_not_start_with_select() -> None:
    result = validator.validate("WITH product_names AS (SELECT name FROM products) SELECT name FROM product_names LIMIT 10")

    assert result.is_valid is False
    assert result.reason == "A query deve comecar com SELECT."


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
