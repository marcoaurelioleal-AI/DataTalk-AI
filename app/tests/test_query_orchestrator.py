from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
import app.api.routes.queries as query_routes
from app.api.deps import get_current_user, get_db
from app.db.base import Base
from app.main import app
from app.models.query_log import QueryLog
from app.models.user import User
from app.providers.base import LlmProviderError
from app.repositories.query_repository import QueryRepository
from app.schemas.query import AskQueryRequest
from app.schemas.sql_agent import SqlAgentResult
from app.schemas.sql_execution import SqlExecutionResult
from app.schemas.sql_safety import SqlSafetyResult
from app.services.query_orchestrator_service import QueryOrchestratorService
from app.services.sql_execution_service import SqlExecutionError, SqlExecutionRejectedError

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
client = TestClient(app)


class FakeExecutionService:
    def __init__(
        self,
        result: SqlExecutionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.executed_sql: list[str] = []

    def execute(self, sql: str) -> SqlExecutionResult:
        self.executed_sql.append(sql)
        if self.error:
            raise self.error
        assert self.result is not None
        return self.result


class FakeAgent:
    def __init__(self, result: SqlAgentResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    def answer(self, question: str) -> SqlAgentResult:
        if self.error:
            raise self.error
        assert self.result is not None
        return self.result


def make_execution_result() -> SqlExecutionResult:
    rows = [
        {"product_name": "Notebook Pro", "total_sold": 128},
        {"product_name": "Smartwatch X", "total_sold": 96},
        {"product_name": "Mouse Gamer", "total_sold": 80},
    ]
    return SqlExecutionResult(
        columns=["product_name", "total_sold"],
        rows=rows,
        row_count=len(rows),
        execution_time_ms=17,
    )


def make_agent_result(status: str) -> SqlAgentResult:
    generated_sql = "SELECT p.name AS product_name, 1 AS total_sold FROM products p LIMIT 3"
    safety_result = SqlSafetyResult(
        is_valid=status == "success",
        reason="Comando DELETE detectado." if status == "blocked" else None,
        original_sql=generated_sql,
        normalized_sql=generated_sql,
        detected_tables=("products",),
    )
    return SqlAgentResult(
        status=status,
        answer="Provider answer",
        generated_sql=None if status == "needs_clarification" else generated_sql,
        provider_used="mock",
        model_used="mock-datatalk-v1",
        recognized_intent="top_products" if status == "success" else None,
        schema_context="products schema",
        agent_prompt="agent prompt",
        safety_result=None if status == "needs_clarification" else safety_result,
    )


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as db:
        yield db


def get_test_user() -> User:
    return User(id=1, name="Query User", email="query@datatalk.ai", hashed_password="hash", role="analyst")


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as db:
        db.add(get_test_user())
        db.commit()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = get_test_user
    yield
    app.dependency_overrides.clear()


def get_query_logs() -> list[QueryLog]:
    with TestingSessionLocal() as db:
        return list(db.scalars(select(QueryLog).order_by(QueryLog.id)))


def test_ask_query_executes_safe_sql_summarizes_rows_and_saves_log(monkeypatch: pytest.MonkeyPatch) -> None:
    execution_service = FakeExecutionService(result=make_execution_result())
    monkeypatch.setattr(
        query_routes.query_orchestrator_service,
        "sql_execution_service",
        execution_service,
        raising=False,
    )

    response = client.post("/queries/ask", json={"question": "Quais produtos venderam mais este mes?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query_id"] == 1
    assert payload["status"] == "success"
    assert payload["generated_sql"].startswith("SELECT")
    assert payload["blocked_reason"] is None
    assert payload["columns"] == ["product_name", "total_sold"]
    assert payload["rows"] == make_execution_result().rows
    assert payload["answer"] == (
        "Ranking por total sold: Notebook Pro (128), Smartwatch X (96) e Mouse Gamer (80)."
    )
    assert payload["chart"] == {"type": "bar", "x": "product_name", "y": "total_sold"}
    assert payload["metadata"]["provider_used"] == "mock"
    assert payload["metadata"]["agent_time_ms"] >= 0
    assert payload["metadata"]["database_time_ms"] == 17
    assert payload["metadata"]["execution_time_ms"] >= 17
    assert execution_service.executed_sql == [payload["generated_sql"]]

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].question == "Quais produtos venderam mais este mes?"
    assert logs[0].status == "success"
    assert logs[0].generated_sql == payload["generated_sql"]
    assert logs[0].blocked_reason is None
    assert logs[0].answer_summary == payload["answer"]
    assert logs[0].execution_time_ms == payload["metadata"]["execution_time_ms"]


@pytest.mark.parametrize("agent_status", ["blocked", "needs_clarification"])
def test_orchestrator_never_executes_non_success_agent_results(agent_status: str) -> None:
    execution_service = FakeExecutionService(result=make_execution_result())
    service = QueryOrchestratorService(
        agent=FakeAgent(result=make_agent_result(agent_status)),
        sql_execution_service=execution_service,
    )

    with TestingSessionLocal() as db:
        response = service.ask(db, get_test_user(), AskQueryRequest(question="Pergunta valida"))

    assert response.status == agent_status
    assert response.columns == []
    assert response.rows == []
    assert response.chart.type == "table"
    assert response.metadata.database_time_ms is None
    assert execution_service.executed_sql == []


def test_orchestrator_logs_controlled_database_error_without_exposing_details() -> None:
    execution_service = FakeExecutionService(
        error=SqlExecutionError("password=secret internal database failure")
    )
    service = QueryOrchestratorService(
        agent=FakeAgent(result=make_agent_result("success")),
        sql_execution_service=execution_service,
    )

    with TestingSessionLocal() as db:
        response = service.ask(db, get_test_user(), AskQueryRequest(question="Pergunta valida"))

    assert response.status == "error"
    assert response.answer == "Não foi possível concluir a consulta com segurança."
    assert "secret" not in response.answer
    assert response.columns == []
    assert response.rows == []
    assert response.metadata.database_time_ms is None

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].status == "error"
    assert logs[0].answer_summary == response.answer
    assert "secret" not in (logs[0].answer_summary or "")


def test_orchestrator_sanitizes_and_logs_unexpected_execution_error() -> None:
    execution_service = FakeExecutionService(error=RuntimeError("unexpected secret driver failure"))
    service = QueryOrchestratorService(
        agent=FakeAgent(result=make_agent_result("success")),
        sql_execution_service=execution_service,
    )

    with TestingSessionLocal() as db:
        response = service.ask(db, get_test_user(), AskQueryRequest(question="Pergunta valida"))

    assert response.status == "error"
    assert response.answer == "Não foi possível concluir a consulta com segurança."
    assert "secret" not in response.answer

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].status == "error"
    assert logs[0].answer_summary == response.answer


def test_orchestrator_logs_final_revalidation_rejection_as_blocked() -> None:
    execution_service = FakeExecutionService(
        error=SqlExecutionRejectedError("Tabela interna 'users' não pode ser consultada.")
    )
    service = QueryOrchestratorService(
        agent=FakeAgent(result=make_agent_result("success")),
        sql_execution_service=execution_service,
    )

    with TestingSessionLocal() as db:
        response = service.ask(db, get_test_user(), AskQueryRequest(question="Pergunta valida"))

    assert response.status == "blocked"
    assert response.blocked_reason == "Tabela interna 'users' não pode ser consultada."
    assert response.columns == []
    assert response.rows == []

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].status == "blocked"
    assert logs[0].blocked_reason == response.blocked_reason


def test_orchestrator_logs_controlled_provider_error() -> None:
    execution_service = FakeExecutionService(result=make_execution_result())
    service = QueryOrchestratorService(
        agent=FakeAgent(
            error=LlmProviderError(
                "safe provider failure",
                provider_used="gemini",
                model_used="gemini-2.5-flash",
                category="unavailable",
                retryable=True,
                attempts=3,
            )
        ),
        sql_execution_service=execution_service,
    )

    with TestingSessionLocal() as db:
        response = service.ask(db, get_test_user(), AskQueryRequest(question="Pergunta valida"))

    assert response.status == "error"
    assert response.answer == "Nao foi possivel gerar uma consulta segura neste momento."
    assert "leaked-secret" not in response.answer
    assert response.generated_sql is None
    assert response.metadata.provider_used == "gemini"
    assert response.metadata.model_used == "gemini-2.5-flash"
    assert execution_service.executed_sql == []

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].status == "error"
    assert logs[0].generated_sql is None
    assert logs[0].provider_used == "gemini"
    assert logs[0].model_used == "gemini-2.5-flash"


def test_ask_query_saves_needs_clarification_without_sql() -> None:
    response = client.post("/queries/ask", json={"question": "Mostre uma analise geral."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "needs_clarification"
    assert payload["generated_sql"] is None

    logs = get_query_logs()
    assert len(logs) == 1
    assert logs[0].status == "needs_clarification"
    assert logs[0].generated_sql is None


def test_ask_query_requires_authentication() -> None:
    app.dependency_overrides.pop(get_current_user)

    response = client.post("/queries/ask", json={"question": "Quais produtos venderam mais?"})

    assert response.status_code == 401


def test_ask_query_rejects_short_question() -> None:
    response = client.post("/queries/ask", json={"question": "oi"})

    assert response.status_code == 422


def test_query_history_returns_only_current_user_logs_in_reverse_order() -> None:
    repository = QueryRepository()
    with TestingSessionLocal() as db:
        db.add(
            User(
                id=2,
                name="Other User",
                email="other@datatalk.ai",
                hashed_password="hash",
                role="viewer",
            )
        )
        db.commit()
        repository.create_log(
            db,
            user_id=1,
            question="Primeira pergunta",
            generated_sql="SELECT id FROM products LIMIT 1",
            status="success",
            blocked_reason=None,
            answer_summary="Primeiro resumo",
            execution_time_ms=10,
            provider_used="mock",
            model_used="mock-rule-based",
        )
        repository.create_log(
            db,
            user_id=2,
            question="Pergunta de outro usuario",
            generated_sql=None,
            status="needs_clarification",
            blocked_reason=None,
            answer_summary="Outro resumo",
            execution_time_ms=5,
            provider_used="mock",
            model_used="mock-rule-based",
        )
        repository.create_log(
            db,
            user_id=1,
            question="Segunda pergunta",
            generated_sql="SELECT name FROM products LIMIT 2",
            status="success",
            blocked_reason=None,
            answer_summary="Segundo resumo",
            execution_time_ms=20,
            provider_used="mock",
            model_used="mock-rule-based",
        )

    response = client.get("/queries/history")

    assert response.status_code == 200
    payload = response.json()
    assert [item["question"] for item in payload] == ["Segunda pergunta", "Primeira pergunta"]
    assert all(item["question"] != "Pergunta de outro usuario" for item in payload)
    assert payload[0]["answer_summary"] == "Segundo resumo"
    assert payload[0]["provider_used"] == "mock"


def test_query_history_supports_limit_and_offset() -> None:
    repository = QueryRepository()
    with TestingSessionLocal() as db:
        for index in range(3):
            repository.create_log(
                db,
                user_id=1,
                question=f"Pergunta {index}",
                generated_sql="SELECT id FROM products LIMIT 1",
                status="success",
                blocked_reason=None,
                answer_summary=f"Resumo {index}",
                execution_time_ms=index,
                provider_used="mock",
                model_used="mock-rule-based",
            )

    response = client.get("/queries/history?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["question"] == "Pergunta 1"


def test_query_history_detail_returns_item_for_owner() -> None:
    repository = QueryRepository()
    with TestingSessionLocal() as db:
        query_log = repository.create_log(
            db,
            user_id=1,
            question="Detalhar pergunta",
            generated_sql=None,
            status="needs_clarification",
            blocked_reason=None,
            answer_summary="Detalhe da resposta",
            execution_time_ms=7,
            provider_used="mock",
            model_used="mock-rule-based",
        )
        query_id = query_log.id

    response = client.get(f"/queries/{query_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == query_id
    assert payload["question"] == "Detalhar pergunta"
    assert payload["generated_sql"] is None
    assert payload["status"] == "needs_clarification"
    assert payload["answer_summary"] == "Detalhe da resposta"
    assert payload["execution_time_ms"] == 7
    assert payload["provider_used"] == "mock"
    assert payload["model_used"] == "mock-rule-based"


def test_query_history_detail_hides_other_users_logs() -> None:
    repository = QueryRepository()
    with TestingSessionLocal() as db:
        db.add(
            User(
                id=2,
                name="Other User",
                email="other@datatalk.ai",
                hashed_password="hash",
                role="viewer",
            )
        )
        db.commit()
        query_log = repository.create_log(
            db,
            user_id=2,
            question="Consulta privada",
            generated_sql=None,
            status="needs_clarification",
            blocked_reason=None,
            answer_summary="Privado",
            execution_time_ms=3,
            provider_used="mock",
            model_used="mock-rule-based",
        )
        query_id = query_log.id

    response = client.get(f"/queries/{query_id}")

    assert response.status_code == 404


def test_query_history_returns_not_found_for_unknown_query() -> None:
    response = client.get("/queries/999")

    assert response.status_code == 404


def test_query_history_requires_authentication() -> None:
    app.dependency_overrides.pop(get_current_user)

    response = client.get("/queries/history")

    assert response.status_code == 401
