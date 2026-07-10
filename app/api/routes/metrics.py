from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.metric import MetricsOverviewResponse, QueryMetricsResponse, TableMetricsResponse
from app.services.metric_service import MetricService

router = APIRouter(prefix="/metrics", tags=["metrics"])
metric_service = MetricService()


@router.get("/overview", response_model=MetricsOverviewResponse)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricsOverviewResponse:
    return metric_service.get_overview(db, current_user)


@router.get("/queries", response_model=QueryMetricsResponse)
def get_query_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryMetricsResponse:
    return metric_service.get_query_metrics(db, current_user)


@router.get("/tables", response_model=TableMetricsResponse)
def get_table_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TableMetricsResponse:
    return metric_service.get_table_metrics(db, current_user)
