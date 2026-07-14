from langchain_core.runnables import RunnableSequence

from app.agents.prompts import build_sql_agent_prompt
from app.agents.sql_agent import DataAnalystSqlAgent
from app.schemas.llm_provider import LlmProviderResult


class UnsafeProvider:
    name = "unsafe-test"
    model_name = "unsafe-test-model"

    def generate(self, question: str, *, prompt: str | None = None) -> LlmProviderResult:
        return LlmProviderResult(
            status="success",
            answer="Unsafe SQL generated for testing.",
            generated_sql="DELETE FROM orders WHERE status = 'cancelled'",
            provider_used=self.name,
            model_used=self.model_name,
            recognized_intent="unsafe_delete",
        )


class PromptCapturingProvider:
    name = "prompt-capturing-test"
    model_name = "prompt-capturing-model"

    def __init__(self) -> None:
        self.received_prompt: str | None = None

    def generate(self, question: str, *, prompt: str | None = None) -> LlmProviderResult:
        self.received_prompt = prompt
        return LlmProviderResult(
            status="needs_clarification",
            answer="Teste de prompt.",
            generated_sql=None,
            provider_used=self.name,
            model_used=self.model_name,
            recognized_intent=None,
        )


def test_sql_agent_uses_named_langchain_sequence() -> None:
    agent = DataAnalystSqlAgent()

    assert isinstance(agent.chain, RunnableSequence)
    assert [step.get_name() for step in agent.chain.steps] == [
        "prepare_sql_context",
        "generate_sql",
        "validate_sql",
    ]


def test_sql_agent_lists_only_queryable_tables() -> None:
    table_names = {table.name for table in DataAnalystSqlAgent().list_tables_tool()}

    assert table_names == {"customers", "products", "orders", "order_items", "campaigns", "sales_channels"}
    assert "users" not in table_names
    assert "query_logs" not in table_names
    assert "query_feedback" not in table_names


def test_sql_agent_prompt_contains_safety_rules_and_schema() -> None:
    prompt = build_sql_agent_prompt(
        question="Quais produtos venderam mais?",
        schema_context="- products: Products available for sale.",
        max_rows=50,
    )

    assert "Gere apenas consultas SELECT." in prompt
    assert "Nunca consulte tabelas internas" in prompt
    assert "Sempre use LIMIT, no maximo 50." in prompt
    assert "Quais produtos venderam mais?" in prompt
    assert "products" in prompt


def test_sql_agent_generates_and_validates_safe_mock_sql() -> None:
    result = DataAnalystSqlAgent().answer("Quais produtos venderam mais este mes?")

    assert result.status == "success"
    assert result.generated_sql is not None
    assert result.safety_result is not None
    assert result.safety_result.is_valid is True
    assert result.safety_result.detected_tables == ("products", "order_items", "orders")
    assert result.provider_used == "mock"
    assert result.recognized_intent == "top_products"


def test_sql_agent_returns_clarification_when_provider_has_no_sql() -> None:
    result = DataAnalystSqlAgent().answer("Mostre uma analise geral.")

    assert result.status == "needs_clarification"
    assert result.generated_sql is None
    assert result.safety_result is None


def test_sql_agent_blocks_unsafe_sql_generated_by_provider() -> None:
    result = DataAnalystSqlAgent(provider=UnsafeProvider()).answer("Apague pedidos cancelados.")

    assert result.status == "blocked"
    assert result.generated_sql == "DELETE FROM orders WHERE status = 'cancelled'"
    assert result.safety_result is not None
    assert result.safety_result.is_valid is False
    assert result.safety_result.reason == "Comando DELETE detectado."


def test_sql_agent_schema_context_excludes_internal_tables() -> None:
    schema_context = DataAnalystSqlAgent().build_schema_context()

    assert "products" in schema_context
    assert "orders" in schema_context
    assert "users" not in schema_context
    assert "query_logs" not in schema_context
    assert "query_feedback" not in schema_context


def test_sql_agent_sends_safety_rules_and_schema_to_provider() -> None:
    provider = PromptCapturingProvider()

    DataAnalystSqlAgent(provider=provider).answer("Quais produtos venderam mais?")

    assert provider.received_prompt is not None
    assert "Gere apenas consultas SELECT." in provider.received_prompt
    assert "products" in provider.received_prompt
    assert "Quais produtos venderam mais?" in provider.received_prompt
