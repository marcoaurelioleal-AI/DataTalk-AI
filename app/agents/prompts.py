from app.core.config import settings
from app.schemas.catalog import CatalogTableSchema

SQL_AGENT_SYSTEM_PROMPT = """Voce e o DataTalk AI, um agente especializado em analise de dados empresariais.

Seu trabalho e transformar perguntas em linguagem natural em consultas SQL seguras.

Regras obrigatorias:
1. Gere apenas consultas SELECT.
2. Nunca gere INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, REPLACE, GRANT ou REVOKE.
3. Use apenas tabelas permitidas.
4. Nunca consulte tabelas internas como users, query_logs ou query_feedback.
5. Sempre use LIMIT, no maximo {max_rows}.
6. Nunca use SELECT *.
7. Use nomes explicitos de colunas.
8. Se a pergunta for ambigua, peca esclarecimento.
9. Se nao for possivel responder com os dados disponiveis, diga isso claramente.
10. Antes de executar, a query sera validada por uma camada de seguranca.
"""


def render_schema_context(tables: list[CatalogTableSchema]) -> str:
    rendered_tables: list[str] = []
    for table in tables:
        columns = ", ".join(
            f"{column.name} ({column.type}) - {column.description}"
            for column in table.columns
            if column.queryable
        )
        rendered_tables.append(f"- {table.name}: {table.description} Columns: {columns}")

    return "\n".join(rendered_tables)


def build_sql_agent_prompt(question: str, schema_context: str, max_rows: int | None = None) -> str:
    row_limit = settings.query_max_rows if max_rows is None else max_rows
    return (
        SQL_AGENT_SYSTEM_PROMPT.format(max_rows=row_limit)
        + "\nPergunta do usuario:\n"
        + question.strip()
        + "\n\nSchema permitido:\n"
        + schema_context
    )
