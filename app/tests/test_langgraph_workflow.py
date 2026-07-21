import pytest
from langchain_core.runnables import RunnableLambda

from app.agents.langgraph_workflow import SqlAgentWorkflow
from app.schemas.sql_agent import SqlAgentResult


def build_agent_result(status: str) -> SqlAgentResult:
    return SqlAgentResult(
        status=status,
        answer="Resultado de teste.",
        generated_sql="SELECT id FROM products LIMIT 1" if status != "needs_clarification" else None,
        provider_used="test",
        model_used="test-model",
        recognized_intent=None,
        schema_context="products",
        agent_prompt="safe prompt",
        safety_result=None,
    )


def test_sql_agent_workflow_runs_only_the_safe_generation_path() -> None:
    calls: list[str] = []

    def prepare(payload: dict[str, object]) -> dict[str, object]:
        calls.append("prepare")
        return {**payload, "prompt": "safe prompt"}

    def generate(payload: dict[str, object]) -> dict[str, object]:
        calls.append("generate")
        return {**payload, "sql": "SELECT id FROM products LIMIT 1"}

    def validate(payload: dict[str, object]) -> SqlAgentResult:
        calls.append("validate")
        return build_agent_result("success")

    workflow = SqlAgentWorkflow(
        prepare_step=RunnableLambda(prepare),
        generate_step=RunnableLambda(generate),
        validate_step=RunnableLambda(validate),
    )

    result = workflow.invoke({"question": "Liste produtos"})

    assert result.status == "success"
    assert calls == ["prepare", "generate", "validate"]
    assert set(workflow.graph.get_graph().nodes) == {
        "__start__",
        "prepare_sql_context",
        "generate_sql",
        "validate_sql",
        "success",
        "blocked",
        "needs_clarification",
        "__end__",
    }
    assert "execute_sql" not in workflow.graph.get_graph().nodes


@pytest.mark.parametrize("status", ["success", "blocked", "needs_clarification"])
def test_sql_agent_workflow_routes_each_result_to_its_terminal_node(status: str) -> None:
    workflow = SqlAgentWorkflow(
        prepare_step=RunnableLambda(lambda payload: payload),
        generate_step=RunnableLambda(lambda payload: payload),
        validate_step=RunnableLambda(lambda payload: build_agent_result(status)),
    )

    updates = list(workflow.graph.stream({"payload": {"question": "Teste"}}, stream_mode="updates"))
    visited_nodes = [next(iter(update)) for update in updates]

    assert visited_nodes == [
        "prepare_sql_context",
        "generate_sql",
        "validate_sql",
        status,
    ]
