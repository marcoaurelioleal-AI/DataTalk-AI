from typing import TypedDict

from langchain_core.runnables import RunnableLambda

from app.agents.langgraph_workflow import SqlAgentWorkflow
from app.agents.prompts import build_sql_agent_prompt, render_schema_context
from app.providers.base import LlmProvider
from app.providers.factory import get_llm_provider
from app.schemas.catalog import CatalogTableSchema, CatalogTableSummary
from app.schemas.llm_provider import LlmProviderResult
from app.schemas.sql_agent import SqlAgentResult
from app.schemas.sql_safety import SqlSafetyResult
from app.services.catalog_service import CatalogService
from app.services.sql_safety_service import SqlSafetyService


class SqlChainInput(TypedDict):
    question: str


class PreparedSqlContext(SqlChainInput):
    schema_context: str
    agent_prompt: str


class GeneratedSqlContext(PreparedSqlContext):
    provider_result: LlmProviderResult


class DataAnalystSqlAgent:
    def __init__(
        self,
        provider: LlmProvider | None = None,
        catalog_service: CatalogService | None = None,
        safety_service: SqlSafetyService | None = None,
    ) -> None:
        self.provider = provider or get_llm_provider()
        self.catalog_service = catalog_service or CatalogService()
        self.safety_service = safety_service or SqlSafetyService()
        self.prepare_step = RunnableLambda(self._prepare_sql_context, name="prepare_sql_context")
        self.generate_step = RunnableLambda(self._generate_sql, name="generate_sql")
        self.validate_step = RunnableLambda(self._validate_sql, name="validate_sql")
        self.chain = self.prepare_step | self.generate_step | self.validate_step
        self.workflow = SqlAgentWorkflow(
            prepare_step=self.prepare_step,
            generate_step=self.generate_step,
            validate_step=self.validate_step,
        )

    def list_tables_tool(self) -> list[CatalogTableSummary]:
        return self.catalog_service.list_tables()

    def get_schema_tool(self, table_name: str) -> CatalogTableSchema:
        return self.catalog_service.get_table_schema(table_name)

    def generate_sql_tool(self, question: str, prompt: str | None = None):
        return self.provider.generate(question, prompt=prompt)

    def validate_sql_tool(self, sql: str) -> SqlSafetyResult:
        return self.safety_service.validate(sql)

    def build_schema_context(self) -> str:
        schemas = [self.get_schema_tool(table.name) for table in self.list_tables_tool()]
        return render_schema_context(schemas)

    def build_prompt(self, question: str) -> str:
        return build_sql_agent_prompt(question, self.build_schema_context(), self.safety_service.max_rows)

    def answer(self, question: str) -> SqlAgentResult:
        return self.workflow.invoke(
            {"question": question},
            config={
                "tags": ["datatalk-sql-agent"],
                "metadata": {"provider": self.provider.name, "model": self.provider.model_name},
            },
        )

    def _prepare_sql_context(self, chain_input: SqlChainInput) -> PreparedSqlContext:
        question = chain_input["question"]
        schema_context = self.build_schema_context()
        return {
            "question": question,
            "schema_context": schema_context,
            "agent_prompt": build_sql_agent_prompt(
                question,
                schema_context,
                self.safety_service.max_rows,
            ),
        }

    def _generate_sql(self, context: PreparedSqlContext) -> GeneratedSqlContext:
        return {
            **context,
            "provider_result": self.generate_sql_tool(
                context["question"],
                context["agent_prompt"],
            ),
        }

    def _validate_sql(self, context: GeneratedSqlContext) -> SqlAgentResult:
        provider_result = context["provider_result"]
        schema_context = context["schema_context"]
        agent_prompt = context["agent_prompt"]

        if provider_result.generated_sql is None:
            return SqlAgentResult(
                status="needs_clarification",
                answer=provider_result.answer,
                generated_sql=None,
                provider_used=provider_result.provider_used,
                model_used=provider_result.model_used,
                recognized_intent=provider_result.recognized_intent,
                schema_context=schema_context,
                agent_prompt=agent_prompt,
                safety_result=None,
            )

        safety_result = self.validate_sql_tool(provider_result.generated_sql)
        if not safety_result.is_valid:
            return SqlAgentResult(
                status="blocked",
                answer="Nao posso executar essa operacao. O sistema permite apenas consultas de leitura seguras.",
                generated_sql=provider_result.generated_sql,
                provider_used=provider_result.provider_used,
                model_used=provider_result.model_used,
                recognized_intent=provider_result.recognized_intent,
                schema_context=schema_context,
                agent_prompt=agent_prompt,
                safety_result=safety_result,
            )

        return SqlAgentResult(
            status="success",
            answer=provider_result.answer,
            generated_sql=safety_result.normalized_sql,
            provider_used=provider_result.provider_used,
            model_used=provider_result.model_used,
            recognized_intent=provider_result.recognized_intent,
            schema_context=schema_context,
            agent_prompt=agent_prompt,
            safety_result=safety_result,
        )
