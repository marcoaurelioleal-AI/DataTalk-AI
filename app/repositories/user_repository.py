from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def get_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)

    def create(self, db: Session, *, name: str, email: str, hashed_password: str, role: str) -> User:
        user = User(name=name, email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
