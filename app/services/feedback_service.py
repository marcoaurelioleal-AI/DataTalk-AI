from sqlalchemy.orm import Session

from app.models.query_feedback import QueryFeedback
from app.models.user import User
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.query_repository import QueryRepository
from app.schemas.feedback import CreateFeedbackRequest


class QueryNotFoundError(Exception):
    pass


class FeedbackService:
    def __init__(
        self,
        feedback_repository: FeedbackRepository | None = None,
        query_repository: QueryRepository | None = None,
    ) -> None:
        self.feedback_repository = feedback_repository or FeedbackRepository()
        self.query_repository = query_repository or QueryRepository()

    def _ensure_owned_query(self, db: Session, *, query_id: int, user_id: int) -> None:
        query_log = self.query_repository.get_by_id_for_user(db, query_id=query_id, user_id=user_id)
        if query_log is None:
            raise QueryNotFoundError

    def create(
        self,
        db: Session,
        current_user: User,
        query_id: int,
        request: CreateFeedbackRequest,
    ) -> QueryFeedback:
        self._ensure_owned_query(db, query_id=query_id, user_id=current_user.id)
        return self.feedback_repository.create(
            db,
            query_log_id=query_id,
            user_id=current_user.id,
            rating=request.rating,
            is_helpful=request.is_helpful,
            comment=request.comment,
        )

    def list_for_query(
        self,
        db: Session,
        current_user: User,
        query_id: int,
    ) -> list[QueryFeedback]:
        self._ensure_owned_query(db, query_id=query_id, user_id=current_user.id)
        return self.feedback_repository.list_by_query_and_user(
            db,
            query_log_id=query_id,
            user_id=current_user.id,
        )
