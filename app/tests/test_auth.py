from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_db
from app.core.security import verify_password
from app.db.base import Base
from app.main import app
from app.models.user import User

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
client = TestClient(app)

REGISTER_PAYLOAD = {
    "name": "Test User",
    "email": "test@datatalk.ai",
    "password": "strong-password",
}


def override_get_db() -> Generator[Session, None, None]:
    with TestingSessionLocal() as db:
        yield db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


def register_user() -> None:
    response = client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201


def test_register_hashes_password() -> None:
    register_user()

    with TestingSessionLocal() as db:
        user = db.scalar(select(User).where(User.email == REGISTER_PAYLOAD["email"]))

    assert user is not None
    assert user.hashed_password != REGISTER_PAYLOAD["password"]
    assert verify_password(REGISTER_PAYLOAD["password"], user.hashed_password)


def test_login_with_valid_credentials_returns_token_and_allows_protected_access() -> None:
    register_user()

    login_response = client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )

    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})

    assert me_response.status_code == 200
    assert me_response.json()["email"] == REGISTER_PAYLOAD["email"]


def test_login_with_invalid_password_returns_401() -> None:
    register_user()

    response = client.post(
        "/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_users_me_requires_authentication() -> None:
    response = client.get("/users/me")

    assert response.status_code == 401
