import pytest

from app.providers.factory import UnsupportedLlmProviderError, get_llm_provider
from app.providers.mock_provider import MockProvider
from app.services.sql_safety_service import SqlSafetyService

validator = SqlSafetyService()


@pytest.mark.parametrize(
    ("question", "expected_intent", "expected_tables"),
    [
        (
            "Quais produtos venderam mais este mes?",
            "top_products",
            ("products", "order_items", "orders"),
        ),
        (
            "Qual canal trouxe mais receita?",
            "revenue_by_channel",
            ("sales_channels", "orders"),
        ),
        (
            "Quais clientes compraram mais nos ultimos 30 dias?",
            "top_customers",
            ("customers", "orders"),
        ),
        (
            "Qual campanha teve melhor desempenho?",
            "campaign_performance",
            ("campaigns", "orders"),
        ),
    ],
)
def test_known_questions_return_safe_simulated_sql(
    question: str,
    expected_intent: str,
    expected_tables: tuple[str, ...],
) -> None:
    result = MockProvider().generate(question)

    assert result.status == "success"
    assert result.recognized_intent == expected_intent
    assert result.generated_sql is not None
    assert result.provider_used == "mock"
    assert result.model_used == "mock-datatalk-v1"

    safety_result = validator.validate(result.generated_sql)
    assert safety_result.is_valid is True
    assert safety_result.detected_tables == expected_tables


def test_question_matching_is_case_and_accent_insensitive() -> None:
    result = MockProvider().generate("QUAL CANAL TROUXE MAIS RECEITA?")

    assert result.status == "success"
    assert result.recognized_intent == "revenue_by_channel"


def test_unknown_question_requests_clarification_without_sql() -> None:
    result = MockProvider().generate("Mostre uma analise geral.")

    assert result.status == "needs_clarification"
    assert result.generated_sql is None
    assert result.recognized_intent is None


def test_mock_provider_uses_configured_default_limit_without_api_key() -> None:
    result = MockProvider(default_limit=5).generate("Quais produtos venderam mais?")

    assert result.generated_sql is not None
    assert result.generated_sql.endswith("LIMIT 5")


@pytest.mark.parametrize("default_limit", [0, 101])
def test_mock_provider_rejects_limit_outside_safe_range(default_limit: int) -> None:
    with pytest.raises(ValueError, match="default_limit must be between"):
        MockProvider(default_limit=default_limit)


def test_factory_returns_mock_provider() -> None:
    provider = get_llm_provider(" mock ")

    assert isinstance(provider, MockProvider)


def test_factory_rejects_provider_not_implemented_yet() -> None:
    with pytest.raises(UnsupportedLlmProviderError, match="is not implemented"):
        get_llm_provider("gemini")
