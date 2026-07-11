from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

def create_database_engine(database_url: str) -> Engine:
    connect_args = {"connect_timeout": 2} if make_url(database_url).get_backend_name() == "postgresql" else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


engine = create_database_engine(settings.database_url)
query_engine = create_database_engine(settings.query_database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def get_session() -> Session:
    return SessionLocal()
