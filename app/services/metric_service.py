import re
from collections import Counter

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.catalog_repository import QUERYABLE_TABLE_NAMES
from app.repositories.metric_repository import MetricRepository
from app.schemas.metric import (
    BlockedReasonMetric,
    DailyQueryMetric,
    MetricsOverviewResponse,
    QueryMetricsResponse,
    QuestionMetric,
    StatusMetric,
    TableMetric,
    TableMetricsResponse,
)

TABLE_REFERENCE_PATTERN = re.compile(
    r'\b(?:from|join)\s+(?:"?[a-zA-Z_][\w]*"?\.)?"?([a-zA-Z_][\w]*)"?',
    re.IGNORECASE,
)


class MetricService:
    def __init__(self, metric_repository: MetricRepository | None = None) -> None:
        self.metric_repository = metric_repository or MetricRepository()

    def get_overview(self, db: Session, current_user: User) -> MetricsOverviewResponse:
        (
            total_queries,
            successful_queries,
            blocked_queries,
            average_execution_time_ms,
            positive_feedback,
        ) = self.metric_repository.get_overview(db, user_id=current_user.id)
        success_rate = (successful_queries / total_queries * 100) if total_queries else 0.0
        return MetricsOverviewResponse(
            total_queries=total_queries,
            successful_queries=successful_queries,
            blocked_queries=blocked_queries,
            success_rate=round(success_rate, 2),
            average_execution_time_ms=round(average_execution_time_ms, 2),
            positive_feedback=positive_feedback,
        )

    def get_query_metrics(self, db: Session, current_user: User) -> QueryMetricsResponse:
        user_id = current_user.id
        return QueryMetricsResponse(
            by_status=[
                StatusMetric(status=status, count=count)
                for status, count in self.metric_repository.get_status_counts(db, user_id=user_id)
            ],
            blocked_reasons=[
                BlockedReasonMetric(reason=reason, count=count)
                for reason, count in self.metric_repository.get_blocked_reason_counts(db, user_id=user_id)
            ],
            most_common_questions=[
                QuestionMetric(question=question, count=count)
                for question, count in self.metric_repository.get_common_questions(db, user_id=user_id)
            ],
            queries_by_day=[
                DailyQueryMetric(date=query_date, count=count)
                for query_date, count in self.metric_repository.get_queries_by_day(db, user_id=user_id)
            ],
        )

    def get_table_metrics(self, db: Session, current_user: User) -> TableMetricsResponse:
        table_counter: Counter[str] = Counter()
        for sql in self.metric_repository.get_successful_sql(db, user_id=current_user.id):
            referenced_tables = {
                table_name.lower()
                for table_name in TABLE_REFERENCE_PATTERN.findall(sql)
                if table_name.lower() in QUERYABLE_TABLE_NAMES
            }
            table_counter.update(referenced_tables)

        tables = [
            TableMetric(table_name=table_name, count=count)
            for table_name, count in sorted(table_counter.items(), key=lambda item: (-item[1], item[0]))
        ]
        return TableMetricsResponse(tables=tables)
