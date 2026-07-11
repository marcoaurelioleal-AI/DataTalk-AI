from time import perf_counter
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.agents.sql_agent import DataAnalystSqlAgent
from app.core.config import settings
from app.models.user import User
from app.repositories.query_repository import QueryRepository
from app.schemas.query import AskQueryRequest, AskQueryResponse, ChartSuggestion, QueryResponseMetadata
from app.services.chart_service import ChartRecommendationService
from app.services.result_summarizer_service import ResultSummarizerService
from app.services.sql_execution_service import (
    SqlExecutionError,
    SqlExecutionRejectedError,
    SqlExecutionService,
)


class QueryOrchestratorService:
    def __init__(
        self,
        agent: DataAnalystSqlAgent | None = None,
        query_repository: QueryRepository | None = None,
        sql_execution_service: SqlExecutionService | None = None,
        result_summarizer_service: ResultSummarizerService | None = None,
        chart_service: ChartRecommendationService | None = None,
    ) -> None:
        self.agent = agent or DataAnalystSqlAgent()
        self.query_repository = query_repository or QueryRepository()
        self.sql_execution_service = sql_execution_service or SqlExecutionService()
        self.result_summarizer_service = result_summarizer_service or ResultSummarizerService()
        self.chart_service = chart_service or ChartRecommendationService()

    def ask(self, db: Session, current_user: User, request: AskQueryRequest) -> AskQueryResponse:
        started_at = perf_counter()
        agent_started_at = perf_counter()
        try:
            agent_result = self.agent.answer(request.question)
        except Exception:
            agent_time_ms = self._elapsed_ms(agent_started_at)
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="error",
                answer="Não foi possível gerar uma consulta segura neste momento.",
                generated_sql=None,
                blocked_reason=None,
                provider_used=settings.llm_provider,
                model_used="unavailable",
                agent_time_ms=agent_time_ms,
            )

        agent_time_ms = self._elapsed_ms(agent_started_at)

        blocked_reason = None
        if agent_result.status == "blocked" and agent_result.safety_result:
            blocked_reason = agent_result.safety_result.reason

        if agent_result.status != "success":
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status=agent_result.status,
                answer=agent_result.answer,
                generated_sql=agent_result.generated_sql,
                blocked_reason=blocked_reason,
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
            )

        if agent_result.generated_sql is None:
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="error",
                answer="Não foi possível gerar uma consulta segura neste momento.",
                generated_sql=None,
                blocked_reason=None,
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
            )

        try:
            execution_result = self.sql_execution_service.execute(agent_result.generated_sql)
        except SqlExecutionRejectedError as error:
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="blocked",
                answer="Não posso executar essa consulta porque ela não passou pela validação final de segurança.",
                generated_sql=agent_result.generated_sql,
                blocked_reason=str(error),
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
            )
        except SqlExecutionError:
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="error",
                answer="Não foi possível concluir a consulta com segurança.",
                generated_sql=agent_result.generated_sql,
                blocked_reason=None,
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
            )
        except Exception:
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="error",
                answer="Não foi possível concluir a consulta com segurança.",
                generated_sql=agent_result.generated_sql,
                blocked_reason=None,
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
            )

        try:
            answer = self.result_summarizer_service.summarize(execution_result)
            chart = self.chart_service.recommend(execution_result)
        except Exception:
            return self._persist_response(
                db,
                current_user=current_user,
                request=request,
                started_at=started_at,
                status="error",
                answer="Não foi possível preparar a resposta da consulta.",
                generated_sql=agent_result.generated_sql,
                blocked_reason=None,
                provider_used=agent_result.provider_used,
                model_used=agent_result.model_used,
                agent_time_ms=agent_time_ms,
                database_time_ms=execution_result.execution_time_ms,
            )

        return self._persist_response(
            db,
            current_user=current_user,
            request=request,
            started_at=started_at,
            status="success",
            answer=answer,
            generated_sql=agent_result.generated_sql,
            blocked_reason=None,
            provider_used=agent_result.provider_used,
            model_used=agent_result.model_used,
            agent_time_ms=agent_time_ms,
            database_time_ms=execution_result.execution_time_ms,
            columns=execution_result.columns,
            rows=execution_result.rows,
            chart=chart,
        )

    def _persist_response(
        self,
        db: Session,
        *,
        current_user: User,
        request: AskQueryRequest,
        started_at: float,
        status: Literal["success", "blocked", "error", "needs_clarification"],
        answer: str,
        generated_sql: str | None,
        blocked_reason: str | None,
        provider_used: str,
        model_used: str,
        agent_time_ms: int,
        database_time_ms: int | None = None,
        columns: list[str] | None = None,
        rows: list[dict[str, Any]] | None = None,
        chart: ChartSuggestion | None = None,
    ) -> AskQueryResponse:
        component_time_ms = agent_time_ms + (database_time_ms or 0)
        execution_time_ms = max(self._elapsed_ms(started_at), component_time_ms)
        query_log = self.query_repository.create_log(
            db,
            user_id=current_user.id,
            question=request.question,
            generated_sql=generated_sql,
            status=status,
            blocked_reason=blocked_reason,
            answer_summary=answer,
            execution_time_ms=execution_time_ms,
            provider_used=provider_used,
            model_used=model_used,
        )

        return AskQueryResponse(
            query_id=query_log.id,
            status=status,
            answer=answer,
            generated_sql=generated_sql,
            blocked_reason=blocked_reason,
            columns=columns or [],
            rows=rows or [],
            chart=chart or ChartSuggestion(type="table"),
            metadata=QueryResponseMetadata(
                provider_used=provider_used,
                model_used=model_used,
                execution_time_ms=execution_time_ms,
                agent_time_ms=agent_time_ms,
                database_time_ms=database_time_ms,
            ),
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, round((perf_counter() - started_at) * 1000))
