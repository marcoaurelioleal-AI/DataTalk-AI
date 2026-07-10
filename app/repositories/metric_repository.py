from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.query_feedback import QueryFeedback
from app.models.query_log import QueryLog


class MetricRepository:
    def get_overview(self, db: Session, *, user_id: int) -> tuple[int, int, int, float, int]:
        statement = select(
            func.count(QueryLog.id),
            func.coalesce(func.sum(case((QueryLog.status == "success", 1), else_=0)), 0),
            func.coalesce(func.sum(case((QueryLog.status == "blocked", 1), else_=0)), 0),
            func.avg(QueryLog.execution_time_ms),
        ).where(QueryLog.user_id == user_id)
        total_queries, successful_queries, blocked_queries, average_execution_time_ms = db.execute(statement).one()

        positive_feedback_statement = select(func.count(QueryFeedback.id)).where(
            QueryFeedback.user_id == user_id,
            QueryFeedback.is_helpful.is_(True),
        )
        positive_feedback = db.scalar(positive_feedback_statement) or 0
        return (
            int(total_queries or 0),
            int(successful_queries or 0),
            int(blocked_queries or 0),
            float(average_execution_time_ms or 0),
            int(positive_feedback),
        )

    def get_status_counts(self, db: Session, *, user_id: int) -> list[tuple[str, int]]:
        statement = (
            select(QueryLog.status, func.count(QueryLog.id))
            .where(QueryLog.user_id == user_id)
            .group_by(QueryLog.status)
            .order_by(func.count(QueryLog.id).desc(), QueryLog.status.asc())
        )
        return [(status, int(count)) for status, count in db.execute(statement)]

    def get_blocked_reason_counts(self, db: Session, *, user_id: int) -> list[tuple[str, int]]:
        statement = (
            select(QueryLog.blocked_reason, func.count(QueryLog.id))
            .where(
                QueryLog.user_id == user_id,
                QueryLog.status == "blocked",
                QueryLog.blocked_reason.is_not(None),
            )
            .group_by(QueryLog.blocked_reason)
            .order_by(func.count(QueryLog.id).desc(), QueryLog.blocked_reason.asc())
        )
        return [(reason, int(count)) for reason, count in db.execute(statement) if reason is not None]

    def get_common_questions(self, db: Session, *, user_id: int, limit: int = 10) -> list[tuple[str, int]]:
        statement = (
            select(QueryLog.question, func.count(QueryLog.id))
            .where(QueryLog.user_id == user_id)
            .group_by(QueryLog.question)
            .order_by(func.count(QueryLog.id).desc(), QueryLog.question.asc())
            .limit(limit)
        )
        return [(question, int(count)) for question, count in db.execute(statement)]

    def get_queries_by_day(self, db: Session, *, user_id: int) -> list[tuple[str, int]]:
        query_date = func.date(QueryLog.created_at)
        statement = (
            select(query_date, func.count(QueryLog.id))
            .where(QueryLog.user_id == user_id)
            .group_by(query_date)
            .order_by(query_date.asc())
        )
        return [(query_date, int(count)) for query_date, count in db.execute(statement)]

    def get_successful_sql(self, db: Session, *, user_id: int) -> list[str]:
        statement = select(QueryLog.generated_sql).where(
            QueryLog.user_id == user_id,
            QueryLog.status == "success",
            QueryLog.generated_sql.is_not(None),
        )
        return [sql for sql in db.scalars(statement) if sql is not None]
