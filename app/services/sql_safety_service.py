import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError
from sqlglot.optimizer.scope import traverse_scope

from app.core.config import settings
from app.repositories.catalog_repository import INTERNAL_TABLE_NAMES, QUERYABLE_TABLE_NAMES
from app.schemas.sql_safety import SqlSafetyResult

PROHIBITED_COMMANDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "MERGE",
    "CALL",
    "EXEC",
)
PROHIBITED_COMMAND_PATTERN = re.compile(rf"\b({'|'.join(PROHIBITED_COMMANDS)})\b", re.IGNORECASE)
UNSUPPORTED_KEYWORD_PATTERN = re.compile(r"\b(INTO|UNION|INTERSECT|EXCEPT)\b", re.IGNORECASE)
LIMIT_KEYWORD_PATTERN = re.compile(r"\bLIMIT\b", re.IGNORECASE)
COMMENT_PATTERN = re.compile(r"--|/\*|\*/")
QUERY_START_PATTERN = re.compile(r"^(?:SELECT|WITH)\b", re.IGNORECASE)

ALLOWED_SCHEMA_NAMES = {"public"}
SYSTEM_SCHEMA_NAMES = {"pg_catalog", "information_schema"}
DANGEROUS_FUNCTION_NAMES = {
    "pg_sleep",
    "pg_read_file",
    "pg_ls_dir",
    "lo_export",
    "dblink",
    "set_config",
}
WRITE_NODE_COMMANDS = (
    (exp.Insert, "INSERT"),
    (exp.Update, "UPDATE"),
    (exp.Delete, "DELETE"),
    (exp.Drop, "DROP"),
    (exp.Alter, "ALTER"),
    (exp.TruncateTable, "TRUNCATE"),
    (exp.Create, "CREATE"),
    (exp.Grant, "GRANT"),
    (exp.Revoke, "REVOKE"),
    (exp.Merge, "MERGE"),
)


class SqlSafetyService:
    def __init__(self, max_rows: int | None = None) -> None:
        self.max_rows = settings.query_max_rows if max_rows is None else max_rows
        if self.max_rows < 1:
            raise ValueError("max_rows must be greater than zero.")

    def validate(self, sql: str) -> SqlSafetyResult:
        original_sql = sql
        stripped_sql = sql.strip()
        if not stripped_sql:
            return self._blocked(original_sql, "", "A query SQL nao pode estar vazia.")

        masked_sql, error_reason = self._mask_string_literals(stripped_sql)
        if error_reason:
            return self._blocked(original_sql, self._normalize_sql(stripped_sql), error_reason)
        if COMMENT_PATTERN.search(masked_sql):
            return self._blocked(
                original_sql,
                self._normalize_sql(stripped_sql),
                "Comentarios SQL nao sao permitidos.",
            )

        statement_sql, masked_statement_sql, error_reason = self._remove_terminal_semicolon(stripped_sql, masked_sql)
        normalized_sql = self._normalize_sql(statement_sql)
        if error_reason:
            return self._blocked(original_sql, normalized_sql, error_reason)

        normalized_masked_sql = self._normalize_sql(masked_statement_sql)
        prohibited_command = PROHIBITED_COMMAND_PATTERN.search(normalized_masked_sql)
        if not QUERY_START_PATTERN.match(normalized_masked_sql):
            if prohibited_command:
                return self._blocked(
                    original_sql,
                    normalized_sql,
                    f"Comando {prohibited_command.group(1).upper()} detectado.",
                )
            return self._blocked(
                original_sql,
                normalized_sql,
                "A query deve ser uma consulta SELECT segura.",
            )

        expression, error_reason = self._parse_single_statement(statement_sql)
        if error_reason or expression is None:
            return self._blocked(original_sql, normalized_sql, error_reason or "SQL invalido ou nao suportado.")

        if any(select.args.get("locks") for select in expression.find_all(exp.Select)):
            return self._blocked(
                original_sql,
                normalized_sql,
                "Consultas com bloqueio de linhas nao sao permitidas.",
            )

        if prohibited_command:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Comando {prohibited_command.group(1).upper()} detectado.",
            )

        ast_write_command = self._find_write_command(expression)
        if ast_write_command:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Comando {ast_write_command} detectado.",
            )

        unsupported_keyword = UNSUPPORTED_KEYWORD_PATTERN.search(normalized_masked_sql)
        if unsupported_keyword:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Construcao {unsupported_keyword.group(1).upper()} nao e permitida.",
            )
        if not isinstance(expression, exp.Select):
            return self._blocked(
                original_sql,
                normalized_sql,
                "A query deve ser uma consulta SELECT segura.",
            )

        dangerous_function = self._find_dangerous_function(expression)
        if dangerous_function:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Funcao perigosa '{dangerous_function}' nao e permitida.",
            )
        if next(expression.find_all(exp.Star), None) is not None:
            return self._blocked(original_sql, normalized_sql, "SELECT * nao e permitido.")

        detected_tables, error_reason = self._detect_tables(expression)
        if error_reason:
            return self._blocked(original_sql, normalized_sql, error_reason, detected_tables)
        if not detected_tables:
            return self._blocked(
                original_sql,
                normalized_sql,
                "A query deve consultar ao menos uma tabela permitida.",
            )

        for table_name in detected_tables:
            if table_name in INTERNAL_TABLE_NAMES:
                return self._blocked(
                    original_sql,
                    normalized_sql,
                    f"Tabela interna '{table_name}' nao pode ser consultada.",
                    detected_tables,
                )
            if table_name not in QUERYABLE_TABLE_NAMES:
                return self._blocked(
                    original_sql,
                    normalized_sql,
                    f"Tabela '{table_name}' nao esta na allowlist.",
                    detected_tables,
                )

        if self._has_implicit_comma_join(expression):
            return self._blocked(
                original_sql,
                normalized_sql,
                "Use JOIN explicito para consultar multiplas tabelas.",
                detected_tables,
            )

        limit_node = expression.args.get("limit")
        if limit_node is None:
            if LIMIT_KEYWORD_PATTERN.search(normalized_masked_sql):
                reason = "A query deve possuir exatamente um LIMIT inteiro."
            else:
                reason = "A query deve possuir LIMIT."
            return self._blocked(original_sql, normalized_sql, reason, detected_tables)

        limit_expression = limit_node.expression
        if not isinstance(limit_expression, exp.Literal) or not limit_expression.is_int:
            return self._blocked(
                original_sql,
                normalized_sql,
                "A query deve possuir exatamente um LIMIT inteiro.",
                detected_tables,
            )

        limit = int(limit_expression.this)
        if limit > self.max_rows:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"LIMIT {limit} excede o maximo permitido de {self.max_rows}.",
                detected_tables,
            )

        return SqlSafetyResult(
            is_valid=True,
            reason=None,
            original_sql=original_sql,
            normalized_sql=normalized_sql,
            detected_tables=detected_tables,
        )

    def _parse_single_statement(self, sql: str) -> tuple[exp.Expr | None, str | None]:
        try:
            expressions = sqlglot.parse(sql, read="postgres")
        except ParseError:
            return None, "SQL invalido ou nao suportado."
        if len(expressions) != 1 or expressions[0] is None:
            return None, "Multiplas statements nao sao permitidas."
        return expressions[0], None

    def _find_write_command(self, expression: exp.Expr) -> str | None:
        for node_type, command in WRITE_NODE_COMMANDS:
            if next(expression.find_all(node_type), None) is not None:
                return command
        return None

    def _find_dangerous_function(self, expression: exp.Expr) -> str | None:
        for function in expression.find_all(exp.Func):
            if isinstance(function, exp.Anonymous):
                function_name = function.name.lower()
            else:
                function_name = function.sql_name().lower()
            if function_name in DANGEROUS_FUNCTION_NAMES:
                return function_name
        return None

    def _detect_tables(self, expression: exp.Expr) -> tuple[tuple[str, ...], str | None]:
        try:
            scopes = list(traverse_scope(expression))
            physical_table_ids = {
                id(source)
                for scope in scopes
                for _, source in scope.selected_sources.values()
                if isinstance(source, exp.Table)
            }
        except Exception:
            return (), "Estrutura de fontes SQL nao suportada."

        detected_tables: list[str] = []

        for table in expression.find_all(exp.Table):
            if id(table) not in physical_table_ids:
                continue
            table_name = table.name.lower()
            schema_name = table.db.lower() if table.db else ""
            catalog_name = table.catalog.lower() if table.catalog else ""

            if catalog_name:
                return tuple(dict.fromkeys(detected_tables)), "Referencias com catalogo nao sao permitidas."
            if schema_name in SYSTEM_SCHEMA_NAMES:
                return (
                    tuple(dict.fromkeys(detected_tables)),
                    f"Schema de sistema '{schema_name}' nao pode ser consultado.",
                )
            if schema_name and schema_name not in ALLOWED_SCHEMA_NAMES:
                return (
                    tuple(dict.fromkeys(detected_tables)),
                    f"Schema '{schema_name}' nao e permitido.",
                )
            detected_tables.append(table_name)

        return tuple(dict.fromkeys(detected_tables)), None

    def _has_implicit_comma_join(self, expression: exp.Expr) -> bool:
        try:
            scopes = traverse_scope(expression)
            return any(
                join.sql(dialect="postgres").lstrip().startswith(",")
                for scope in scopes
                for join in (scope.expression.args.get("joins") or [])
            )
        except Exception:
            return True

    def _remove_terminal_semicolon(self, sql: str, masked_sql: str) -> tuple[str, str, str | None]:
        semicolon_indexes = [index for index, character in enumerate(masked_sql) if character == ";"]
        if not semicolon_indexes:
            return sql, masked_sql, None

        terminal_index = len(masked_sql.rstrip()) - 1
        if len(semicolon_indexes) != 1 or semicolon_indexes[0] != terminal_index:
            return sql, masked_sql, "Multiplas statements nao sao permitidas."

        return sql.rstrip()[:-1].rstrip(), masked_sql.rstrip()[:-1].rstrip(), None

    def _mask_string_literals(self, sql: str) -> tuple[str, str | None]:
        characters = list(sql)
        index = 0
        while index < len(characters):
            if characters[index] != "'":
                index += 1
                continue

            characters[index] = " "
            index += 1
            while index < len(characters):
                if characters[index] != "'":
                    characters[index] = " "
                    index += 1
                    continue
                if index + 1 < len(characters) and characters[index + 1] == "'":
                    characters[index] = " "
                    characters[index + 1] = " "
                    index += 2
                    continue

                characters[index] = " "
                index += 1
                break
            else:
                return "".join(characters), "Literal de texto SQL nao terminado."

        return "".join(characters), None

    def _normalize_sql(self, sql: str) -> str:
        return " ".join(sql.split())

    def _blocked(
        self,
        original_sql: str,
        normalized_sql: str,
        reason: str,
        detected_tables: tuple[str, ...] = (),
    ) -> SqlSafetyResult:
        return SqlSafetyResult(
            is_valid=False,
            reason=reason,
            original_sql=original_sql,
            normalized_sql=normalized_sql,
            detected_tables=detected_tables,
        )
