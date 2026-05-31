from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest


class UserAlreadyExistsError(Exception):
    pass


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None) -> None:
        self.user_repository = user_repository or UserRepository()

    def register(self, db: Session, request: RegisterRequest) -> User:
        if self.user_repository.get_by_email(db, request.email):
            raise UserAlreadyExistsError

        return self.user_repository.create(
            db,
            name=request.name,
            email=request.email,
            hashed_password=hash_password(request.password),
            role="viewer",
        )

    def authenticate(self, db: Session, email: str, password: str) -> User | None:
        user = self.user_repository.get_by_email(db, email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
