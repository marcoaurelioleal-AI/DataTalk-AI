from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.query_log import QueryLog


class QueryRepository:
    def create_log(
        self,
        db: Session,
        *,
        user_id: int,
        question: str,
        generated_sql: str | None,
        status: str,
        blocked_reason: str | None,
        answer_summary: str | None,
        execution_time_ms: int,
        provider_used: str | None,
        model_used: str | None,
    ) -> QueryLog:
        query_log = QueryLog(
            user_id=user_id,
            question=question,
            generated_sql=generated_sql,
            status=status,
            blocked_reason=blocked_reason,
            answer_summary=answer_summary,
            execution_time_ms=execution_time_ms,
            provider_used=provider_used,
            model_used=model_used,
        )
        db.add(query_log)
        db.commit()
        db.refresh(query_log)
        return query_log

    def list_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list[QueryLog]:
        statement = (
            select(QueryLog)
            .where(QueryLog.user_id == user_id)
            .order_by(QueryLog.created_at.desc(), QueryLog.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(statement))

    def get_by_id_for_user(self, db: Session, *, query_id: int, user_id: int) -> QueryLog | None:
        statement = select(QueryLog).where(QueryLog.id == query_id, QueryLog.user_id == user_id)
        return db.scalar(statement)
