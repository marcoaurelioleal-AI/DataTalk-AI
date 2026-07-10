from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.query_feedback import QueryFeedback


class FeedbackRepository:
    def create(
        self,
        db: Session,
        *,
        query_log_id: int,
        user_id: int,
        rating: int,
        is_helpful: bool,
        comment: str | None,
    ) -> QueryFeedback:
        feedback = QueryFeedback(
            query_log_id=query_log_id,
            user_id=user_id,
            rating=rating,
            is_helpful=is_helpful,
            comment=comment,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    def list_by_query_and_user(
        self,
        db: Session,
        *,
        query_log_id: int,
        user_id: int,
    ) -> list[QueryFeedback]:
        statement = (
            select(QueryFeedback)
            .where(
                QueryFeedback.query_log_id == query_log_id,
                QueryFeedback.user_id == user_id,
            )
            .order_by(QueryFeedback.created_at.desc(), QueryFeedback.id.desc())
        )
        return list(db.scalars(statement))
