from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_current_user, get_db
from app.db.base import Base
from app.main import app
from app.models.query_log import QueryLog
from app.models.user import User
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.query_repository import QueryRepository

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
client = TestClient(app)


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as db:
        yield db


def get_test_user() -> User:
    return User(id=1, name="Metrics User", email="metrics@datatalk.ai", hashed_password="hash", role="analyst")


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


def create_query_log(
    *,
    user_id: int = 1,
    question: str,
    generated_sql: str | None,
    status: str,
    blocked_reason: str | None,
    execution_time_ms: int,
) -> QueryLog:
    with TestingSessionLocal() as db:
        return QueryRepository().create_log(
            db,
            user_id=user_id,
            question=question,
            generated_sql=generated_sql,
            status=status,
            blocked_reason=blocked_reason,
            answer_summary="Resumo",
            execution_time_ms=execution_time_ms,
            provider_used="mock",
            model_used="mock-rule-based",
        )


def seed_metrics_data() -> None:
    product_query = create_query_log(
        question="Produtos mais vendidos",
        generated_sql=(
            "SELECT p.name FROM products p "
            "JOIN order_items oi ON oi.product_id = p.id LIMIT 5"
        ),
        status="success",
        blocked_reason=None,
        execution_time_ms=100,
    )
    customer_query = create_query_log(
        question="Clientes ativos",
        generated_sql="SELECT c.name FROM customers c LIMIT 10",
        status="success",
        blocked_reason=None,
        execution_time_ms=200,
    )
    create_query_log(
        question="Excluir pedidos",
        generated_sql="DELETE FROM orders WHERE id = 1",
        status="blocked",
        blocked_reason="Comando DELETE detectado.",
        execution_time_ms=50,
    )
    create_query_log(
        question="Editar pedido",
        generated_sql="UPDATE orders SET status = 'paid'",
        status="blocked",
        blocked_reason="Comando UPDATE detectado.",
        execution_time_ms=40,
    )
    create_query_log(
        question="Produtos mais vendidos",
        generated_sql=None,
        status="needs_clarification",
        blocked_reason=None,
        execution_time_ms=10,
    )

    with TestingSessionLocal() as db:
        feedback_repository = FeedbackRepository()
        feedback_repository.create(
            db,
            query_log_id=product_query.id,
            user_id=1,
            rating=5,
            is_helpful=True,
            comment=None,
        )
        feedback_repository.create(
            db,
            query_log_id=customer_query.id,
            user_id=1,
            rating=2,
            is_helpful=False,
            comment=None,
        )

        db.add(
            User(
                id=2,
                name="Other User",
                email="other-metrics@datatalk.ai",
                hashed_password="hash",
                role="viewer",
            )
        )
        db.commit()

    other_user_query = create_query_log(
        user_id=2,
        question="Consulta de outro usuario",
        generated_sql="SELECT id FROM campaigns LIMIT 1",
        status="success",
        blocked_reason=None,
        execution_time_ms=999,
    )
    with TestingSessionLocal() as db:
        FeedbackRepository().create(
            db,
            query_log_id=other_user_query.id,
            user_id=2,
            rating=5,
            is_helpful=True,
            comment=None,
        )


def test_metrics_overview_is_calculated_for_current_user() -> None:
    seed_metrics_data()

    response = client.get("/metrics/overview")

    assert response.status_code == 200
    assert response.json() == {
        "total_queries": 5,
        "successful_queries": 2,
        "blocked_queries": 2,
        "success_rate": 40.0,
        "average_execution_time_ms": 80.0,
        "positive_feedback": 1,
    }


def test_query_metrics_expose_statuses_reasons_questions_and_daily_counts() -> None:
    seed_metrics_data()

    response = client.get("/metrics/queries")

    assert response.status_code == 200
    payload = response.json()
    assert {item["status"]: item["count"] for item in payload["by_status"]} == {
        "success": 2,
        "blocked": 2,
        "needs_clarification": 1,
    }
    assert {item["reason"]: item["count"] for item in payload["blocked_reasons"]} == {
        "Comando DELETE detectado.": 1,
        "Comando UPDATE detectado.": 1,
    }
    assert payload["most_common_questions"][0] == {"question": "Produtos mais vendidos", "count": 2}
    assert len(payload["queries_by_day"]) == 1
    assert payload["queries_by_day"][0]["count"] == 5


def test_table_metrics_include_only_allowed_tables_from_successful_queries() -> None:
    seed_metrics_data()

    response = client.get("/metrics/tables")

    assert response.status_code == 200
    assert response.json() == {
        "tables": [
            {"table_name": "customers", "count": 1},
            {"table_name": "order_items", "count": 1},
            {"table_name": "products", "count": 1},
        ]
    }


def test_empty_metrics_return_zeroes_and_empty_collections() -> None:
    overview_response = client.get("/metrics/overview")
    query_response = client.get("/metrics/queries")
    table_response = client.get("/metrics/tables")

    assert overview_response.status_code == 200
    assert overview_response.json() == {
        "total_queries": 0,
        "successful_queries": 0,
        "blocked_queries": 0,
        "success_rate": 0.0,
        "average_execution_time_ms": 0.0,
        "positive_feedback": 0,
    }
    assert query_response.json() == {
        "by_status": [],
        "blocked_reasons": [],
        "most_common_questions": [],
        "queries_by_day": [],
    }
    assert table_response.json() == {"tables": []}


def test_metrics_require_authentication() -> None:
    app.dependency_overrides.pop(get_current_user)

    response = client.get("/metrics/overview")

    assert response.status_code == 401
