from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.repositories.query_repository import QueryRepository
from app.schemas.query import AskQueryRequest, AskQueryResponse, QueryHistoryItem
from app.services.query_orchestrator_service import QueryOrchestratorService

router = APIRouter(prefix="/queries", tags=["queries"])
query_orchestrator_service = QueryOrchestratorService()
query_repository = QueryRepository()


@router.post("/ask", response_model=AskQueryResponse)
def ask_query(
    request: AskQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AskQueryResponse:
    return query_orchestrator_service.ask(db, current_user, request)


@router.get("/history", response_model=list[QueryHistoryItem])
def list_query_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[QueryHistoryItem]:
    return query_repository.list_by_user(
        db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )


@router.get("/{query_id}", response_model=QueryHistoryItem)
def get_query_history_item(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryHistoryItem:
    query_log = query_repository.get_by_id_for_user(
        db,
        query_id=query_id,
        user_id=current_user.id,
    )
    if query_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query history item not found.",
        )
    return query_log
