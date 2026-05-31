from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: int | str, expires_delta: timedelta | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    return jwt.encode(
        {"sub": str(subject), "exp": expires_at},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token subject is missing.")
    return str(subject)
