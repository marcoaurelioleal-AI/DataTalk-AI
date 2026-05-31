import re

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
TABLE_REFERENCE_PATTERN = re.compile(r"\b(?:FROM|JOIN)\s+([a-z_][a-z0-9_]*)\b", re.IGNORECASE)
TABLE_SOURCE_PATTERN = re.compile(r"\b(?:FROM|JOIN)\b", re.IGNORECASE)
FROM_CLAUSE_PATTERN = re.compile(
    r"\bFROM\b(?P<clause>.*?)(?=\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bHAVING\b|\bLIMIT\b|$)",
    re.IGNORECASE,
)
LIMIT_KEYWORD_PATTERN = re.compile(r"\bLIMIT\b", re.IGNORECASE)
LIMIT_VALUE_PATTERN = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
SELECT_PROJECTION_PATTERN = re.compile(r"^SELECT\s+(?P<projection>.*?)\s+FROM\b", re.IGNORECASE)
SELECT_WILDCARD_PATTERN = re.compile(r"(?:^|,)\s*(?:[a-z_][a-z0-9_]*\.)?\*\s*(?:,|$)", re.IGNORECASE)
COMMENT_PATTERN = re.compile(r"--|/\*|\*/")


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
        if prohibited_command:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Comando {prohibited_command.group(1).upper()} detectado.",
            )
        if not re.match(r"^SELECT\b", normalized_masked_sql, re.IGNORECASE):
            return self._blocked(original_sql, normalized_sql, "A query deve comecar com SELECT.")
        unsupported_keyword = UNSUPPORTED_KEYWORD_PATTERN.search(normalized_masked_sql)
        if unsupported_keyword:
            return self._blocked(
                original_sql,
                normalized_sql,
                f"Construcao {unsupported_keyword.group(1).upper()} nao e permitida.",
            )
        if self._contains_select_wildcard(normalized_masked_sql):
            return self._blocked(original_sql, normalized_sql, "SELECT * nao e permitido.")

        detected_tables, error_reason = self._detect_tables(normalized_masked_sql)
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

        limit_matches = LIMIT_VALUE_PATTERN.findall(normalized_masked_sql)
        if not LIMIT_KEYWORD_PATTERN.search(normalized_masked_sql):
            return self._blocked(original_sql, normalized_sql, "A query deve possuir LIMIT.", detected_tables)
        if len(limit_matches) != 1:
            return self._blocked(
                original_sql,
                normalized_sql,
                "A query deve possuir exatamente um LIMIT inteiro.",
                detected_tables,
            )

        limit = int(limit_matches[0])
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

    def _detect_tables(self, sql: str) -> tuple[tuple[str, ...], str | None]:
        detected_tables = tuple(dict.fromkeys(match.lower() for match in TABLE_REFERENCE_PATTERN.findall(sql)))
        if len(TABLE_SOURCE_PATTERN.findall(sql)) != len(TABLE_REFERENCE_PATTERN.findall(sql)):
            return detected_tables, "Referencia de tabela nao suportada."

        for match in FROM_CLAUSE_PATTERN.finditer(sql):
            if "," in match.group("clause"):
                return detected_tables, "Use JOIN explicito para consultar multiplas tabelas."

        return detected_tables, None

    def _contains_select_wildcard(self, sql: str) -> bool:
        projection_match = SELECT_PROJECTION_PATTERN.search(sql)
        if not projection_match:
            return False

        projection = re.sub(r"^DISTINCT\s+", "", projection_match.group("projection"), flags=re.IGNORECASE)
        return SELECT_WILDCARD_PATTERN.search(projection) is not None

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
