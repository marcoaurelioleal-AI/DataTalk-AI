from typing import Any, TypedDict

from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, StateGraph

from app.schemas.sql_agent import SqlAgentResult


class SqlAgentWorkflowState(TypedDict):
    payload: Any


class SqlAgentWorkflow:
    def __init__(
        self,
        *,
        prepare_step: Runnable[Any, Any],
        generate_step: Runnable[Any, Any],
        validate_step: Runnable[Any, Any],
    ) -> None:
        self.prepare_step = prepare_step
        self.generate_step = generate_step
        self.validate_step = validate_step

        builder = StateGraph(SqlAgentWorkflowState)
        builder.add_node("prepare_sql_context", self._prepare)
        builder.add_node("generate_sql", self._generate)
        builder.add_node("validate_sql", self._validate)
        builder.add_node("success", self._complete)
        builder.add_node("blocked", self._complete)
        builder.add_node("needs_clarification", self._complete)
        builder.add_edge(START, "prepare_sql_context")
        builder.add_edge("prepare_sql_context", "generate_sql")
        builder.add_edge("generate_sql", "validate_sql")
        builder.add_conditional_edges(
            "validate_sql",
            self._route_result,
            {
                "success": "success",
                "blocked": "blocked",
                "needs_clarification": "needs_clarification",
            },
        )
        builder.add_edge("success", END)
        builder.add_edge("blocked", END)
        builder.add_edge("needs_clarification", END)
        self.graph = builder.compile(name="datatalk_sql_agent")

    def invoke(self, payload: Any, config: RunnableConfig | None = None) -> Any:
        final_state = self.graph.invoke({"payload": payload}, config=config)
        return final_state["payload"]

    def _prepare(self, state: SqlAgentWorkflowState) -> SqlAgentWorkflowState:
        return {"payload": self.prepare_step.invoke(state["payload"])}

    def _generate(self, state: SqlAgentWorkflowState) -> SqlAgentWorkflowState:
        return {"payload": self.generate_step.invoke(state["payload"])}

    def _validate(self, state: SqlAgentWorkflowState) -> SqlAgentWorkflowState:
        return {"payload": self.validate_step.invoke(state["payload"])}

    def _route_result(self, state: SqlAgentWorkflowState) -> str:
        result = state["payload"]
        if not isinstance(result, SqlAgentResult):
            raise TypeError("validate_step must return SqlAgentResult")
        return result.status

    def _complete(self, state: SqlAgentWorkflowState) -> SqlAgentWorkflowState:
        return state
