from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_current_user, get_db
from app.db.base import Base
from app.main import app
from app.models.query_feedback import QueryFeedback
from app.models.query_log import QueryLog
from app.models.user import User
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
    return User(id=1, name="Feedback User", email="feedback@datatalk.ai", hashed_password="hash", role="analyst")


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


def create_query_log(*, user_id: int = 1) -> QueryLog:
    with TestingSessionLocal() as db:
        query_log = QueryRepository().create_log(
            db,
            user_id=user_id,
            question="Quais produtos venderam mais?",
            generated_sql="SELECT name FROM products LIMIT 5",
            status="success",
            blocked_reason=None,
            answer_summary="Produtos mais vendidos.",
            execution_time_ms=12,
            provider_used="mock",
            model_used="mock-rule-based",
        )
        return query_log


def test_create_feedback_saves_and_normalizes_comment() -> None:
    query_log = create_query_log()

    response = client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": 5, "is_helpful": True, "comment": "  Resposta muito boa.  "},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["query_log_id"] == query_log.id
    assert payload["user_id"] == 1
    assert payload["rating"] == 5
    assert payload["is_helpful"] is True
    assert payload["comment"] == "Resposta muito boa."

    with TestingSessionLocal() as db:
        feedback = db.scalar(select(QueryFeedback))

    assert feedback is not None
    assert feedback.query_log_id == query_log.id
    assert feedback.user_id == 1


def test_list_feedback_returns_feedback_for_owned_query() -> None:
    query_log = create_query_log()
    client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": 4, "is_helpful": True, "comment": None},
    )
    client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": 2, "is_helpful": False, "comment": "Precisa melhorar"},
    )

    response = client.get(f"/queries/{query_log.id}/feedback")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert [item["rating"] for item in payload] == [2, 4]


@pytest.mark.parametrize("rating", [0, 6])
def test_create_feedback_rejects_rating_outside_range(rating: int) -> None:
    query_log = create_query_log()

    response = client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": rating, "is_helpful": True},
    )

    assert response.status_code == 422


def test_feedback_hides_other_users_queries() -> None:
    with TestingSessionLocal() as db:
        db.add(
            User(
                id=2,
                name="Other User",
                email="other-feedback@datatalk.ai",
                hashed_password="hash",
                role="viewer",
            )
        )
        db.commit()
    query_log = create_query_log(user_id=2)

    create_response = client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": 5, "is_helpful": True},
    )
    list_response = client.get(f"/queries/{query_log.id}/feedback")

    assert create_response.status_code == 404
    assert list_response.status_code == 404


def test_feedback_requires_authentication() -> None:
    app.dependency_overrides.pop(get_current_user)
    query_log = create_query_log()

    response = client.post(
        f"/queries/{query_log.id}/feedback",
        json={"rating": 5, "is_helpful": True},
    )

    assert response.status_code == 401
