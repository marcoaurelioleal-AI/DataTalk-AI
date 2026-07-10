from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.query_feedback import QueryFeedback
from app.models.user import User
from app.schemas.feedback import CreateFeedbackRequest, FeedbackResponse
from app.services.feedback_service import FeedbackService, QueryNotFoundError

router = APIRouter(prefix="/queries", tags=["feedback"])
feedback_service = FeedbackService()


def _query_not_found(error: QueryNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Query history item not found.",
    )


@router.post("/{query_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    query_id: int,
    request: CreateFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryFeedback:
    try:
        return feedback_service.create(db, current_user, query_id, request)
    except QueryNotFoundError as error:
        raise _query_not_found(error) from error


@router.get("/{query_id}/feedback", response_model=list[FeedbackResponse])
def list_feedback(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QueryFeedback]:
    try:
        return feedback_service.list_for_query(db, current_user, query_id)
    except QueryNotFoundError as error:
        raise _query_not_found(error) from error
