import unicodedata
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.llm_provider import LlmProviderResult


@dataclass(frozen=True)
class MockScenario:
    intent: str
    keyword_groups: tuple[tuple[str, ...], ...]
    sql_template: str
    answer: str

    def matches(self, normalized_question: str) -> bool:
        return all(any(keyword in normalized_question for keyword in group) for group in self.keyword_groups)


MOCK_SCENARIOS = (
    MockScenario(
        intent="top_products",
        keyword_groups=(("produto",), ("vend",)),
        sql_template=(
            "SELECT p.name AS product_name, SUM(oi.quantity) AS total_sold "
            "FROM products p "
            "JOIN order_items oi ON oi.product_id = p.id "
            "JOIN orders o ON o.id = oi.order_id "
            "WHERE o.status = 'paid' "
            "GROUP BY p.name "
            "ORDER BY total_sold DESC "
            "LIMIT {limit}"
        ),
        answer="Consulta simulada para listar os produtos mais vendidos.",
    ),
    MockScenario(
        intent="revenue_by_channel",
        keyword_groups=(("receita", "faturamento"), ("canal",)),
        sql_template=(
            "SELECT sc.name AS channel_name, SUM(o.total_amount) AS total_revenue "
            "FROM sales_channels sc "
            "JOIN orders o ON o.sales_channel_id = sc.id "
            "WHERE o.status = 'paid' "
            "GROUP BY sc.name "
            "ORDER BY total_revenue DESC "
            "LIMIT {limit}"
        ),
        answer="Consulta simulada para comparar a receita por canal de vendas.",
    ),
    MockScenario(
        intent="top_customers",
        keyword_groups=(("cliente",), ("compr", "gast")),
        sql_template=(
            "SELECT c.name AS customer_name, SUM(o.total_amount) AS total_spent "
            "FROM customers c "
            "JOIN orders o ON o.customer_id = c.id "
            "WHERE o.status = 'paid' "
            "GROUP BY c.name "
            "ORDER BY total_spent DESC "
            "LIMIT {limit}"
        ),
        answer="Consulta simulada para listar os clientes com maior volume de compras.",
    ),
    MockScenario(
        intent="campaign_performance",
        keyword_groups=(("campanha",), ("desempenho", "receita", "resultado")),
        sql_template=(
            "SELECT c.name AS campaign_name, SUM(o.total_amount) AS total_revenue "
            "FROM campaigns c "
            "JOIN orders o ON o.campaign_id = c.id "
            "WHERE o.status = 'paid' "
            "GROUP BY c.name "
            "ORDER BY total_revenue DESC "
            "LIMIT {limit}"
        ),
        answer="Consulta simulada para comparar o desempenho das campanhas.",
    ),
)


class MockProvider:
    name = "mock"
    model_name = "mock-datatalk-v1"

    def __init__(self, default_limit: int | None = None) -> None:
        self.default_limit = settings.default_query_limit if default_limit is None else default_limit
        if not 1 <= self.default_limit <= settings.query_max_rows:
            raise ValueError(f"default_limit must be between 1 and {settings.query_max_rows}.")

    def generate(self, question: str) -> LlmProviderResult:
        normalized_question = self._normalize_question(question)
        for scenario in MOCK_SCENARIOS:
            if scenario.matches(normalized_question):
                return LlmProviderResult(
                    status="success",
                    answer=scenario.answer,
                    generated_sql=scenario.sql_template.format(limit=self.default_limit),
                    provider_used=self.name,
                    model_used=self.model_name,
                    recognized_intent=scenario.intent,
                )

        return LlmProviderResult(
            status="needs_clarification",
            answer=(
                "Sua pergunta esta ampla. Deseja analisar produtos vendidos, receita por canal, "
                "clientes com maior volume de compras ou desempenho de campanhas?"
            ),
            generated_sql=None,
            provider_used=self.name,
            model_used=self.model_name,
            recognized_intent=None,
        )

    def _normalize_question(self, question: str) -> str:
        normalized_question = unicodedata.normalize("NFKD", question)
        without_accents = "".join(character for character in normalized_question if not unicodedata.combining(character))
        return " ".join(without_accents.lower().split())
