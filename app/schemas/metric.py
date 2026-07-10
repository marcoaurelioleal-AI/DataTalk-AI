from datetime import date

from pydantic import BaseModel, Field


class MetricsOverviewResponse(BaseModel):
    total_queries: int
    successful_queries: int
    blocked_queries: int
    success_rate: float
    average_execution_time_ms: float
    positive_feedback: int


class StatusMetric(BaseModel):
    status: str
    count: int


class BlockedReasonMetric(BaseModel):
    reason: str
    count: int


class QuestionMetric(BaseModel):
    question: str
    count: int


class DailyQueryMetric(BaseModel):
    date: date
    count: int


class QueryMetricsResponse(BaseModel):
    by_status: list[StatusMetric] = Field(default_factory=list)
    blocked_reasons: list[BlockedReasonMetric] = Field(default_factory=list)
    most_common_questions: list[QuestionMetric] = Field(default_factory=list)
    queries_by_day: list[DailyQueryMetric] = Field(default_factory=list)


class TableMetric(BaseModel):
    table_name: str
    count: int


class TableMetricsResponse(BaseModel):
    tables: list[TableMetric] = Field(default_factory=list)
