from time import perf_counter

from sqlalchemy.orm import Session

from app.agents.sql_agent import DataAnalystSqlAgent
from app.models.user import User
from app.repositories.query_repository import QueryRepository
from app.schemas.query import AskQueryRequest, AskQueryResponse, ChartSuggestion, QueryResponseMetadata


class QueryOrchestratorService:
    def __init__(
        self,
        agent: DataAnalystSqlAgent | None = None,
        query_repository: QueryRepository | None = None,
    ) -> None:
        self.agent = agent or DataAnalystSqlAgent()
        self.query_repository = query_repository or QueryRepository()

    def ask(self, db: Session, current_user: User, request: AskQueryRequest) -> AskQueryResponse:
        started_at = perf_counter()
        agent_result = self.agent.answer(request.question)
        execution_time_ms = max(0, round((perf_counter() - started_at) * 1000))

        blocked_reason = None
        if agent_result.status == "blocked" and agent_result.safety_result:
            blocked_reason = agent_result.safety_result.reason

        query_log = self.query_repository.create_log(
            db,
            user_id=current_user.id,
            question=request.question,
            generated_sql=agent_result.generated_sql,
            status=agent_result.status,
            blocked_reason=blocked_reason,
            answer_summary=agent_result.answer,
            execution_time_ms=execution_time_ms,
            provider_used=agent_result.provider_used,
            model_used=agent_result.model_used,
        )

        return AskQueryResponse(
            query_id=query_log.id,
            status=agent_result.status,
            answer=agent_result.answer,
            generated_sql=agent_result.generated_sql,
            blocked_reason=blocked_reason,
            columns=[],
            rows=[],
            chart=ChartSuggestion(type="table"),
            metadata=QueryResponseMetadata(
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                execution_time_ms=execution_time_ms,
            ),
        )
