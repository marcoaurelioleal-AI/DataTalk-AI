import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AskQueryResponse } from "../lib/types";
import { AskDataPage } from "./AskDataPage";

const { askQuestion, submitFeedback } = vi.hoisted(() => ({
  askQuestion: vi.fn(),
  submitFeedback: vi.fn(),
}));

vi.mock("../lib/api", () => ({
  askQuestion,
  getApiErrorMessage: () => "Nao foi possivel concluir a consulta.",
  submitFeedback,
}));

const successfulResponse: AskQueryResponse = {
  query_id: 101,
  status: "success",
  answer: "Notebook Pro liderou as vendas no periodo.",
  generated_sql: "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON oi.product_id = p.id GROUP BY p.name ORDER BY total_sold DESC LIMIT 5",
  blocked_reason: null,
  columns: ["product_name", "total_sold"],
  rows: [{ product_name: "Notebook Pro", total_sold: 128 }],
  chart: { type: "bar", x: "product_name", y: "total_sold" },
  metadata: { provider_used: "mock", model_used: "mock-data-analyst", execution_time_ms: 1250 },
};

const blockedResponse: AskQueryResponse = {
  ...successfulResponse,
  query_id: 102,
  status: "blocked",
  answer: "A operação foi bloqueada por segurança.",
  generated_sql: "DELETE FROM orders WHERE status = 'cancelled'",
  blocked_reason: "Comando DELETE detectado.",
  columns: [],
  rows: [],
  chart: { type: "table", x: null, y: null },
};

const clarificationResponse: AskQueryResponse = {
  ...successfulResponse,
  query_id: 103,
  status: "needs_clarification",
  answer: "Você deseja analisar vendas por período, produto ou canal?",
  generated_sql: null,
  blocked_reason: null,
  columns: [],
  rows: [],
  chart: { type: "table", x: null, y: null },
};

describe("AskDataPage", () => {
  beforeEach(() => {
    askQuestion.mockReset();
    submitFeedback.mockReset();
  });

  it("renders the generated result after a successful question", async () => {
    askQuestion.mockResolvedValue(successfulResponse);
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Quais produtos venderam mais?");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(await screen.findByText(successfulResponse.answer)).toBeInTheDocument();
    expect(screen.getByText("Aprovada")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Gráfico de barras" })).toBeInTheDocument();
    expect(screen.getAllByText("Notebook Pro")).toHaveLength(2);
    expect(screen.getByText("1.250 ms")).toBeInTheDocument();
  });

  it("registers feedback for the returned query", async () => {
    askQuestion.mockResolvedValue(successfulResponse);
    submitFeedback.mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Quais produtos venderam mais?");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));
    await screen.findByText(successfulResponse.answer);
    await user.click(screen.getByRole("button", { name: "Resposta útil" }));

    expect(submitFeedback).toHaveBeenCalledWith(successfulResponse.query_id, true);
    expect(await screen.findByText("Feedback registrado.")).toBeInTheDocument();
  });

  it("shows a loading state while the query is pending", async () => {
    let resolveQuery: (response: AskQueryResponse) => void = () => undefined;
    askQuestion.mockReturnValue(new Promise((resolve) => { resolveQuery = resolve; }));
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Quais produtos venderam mais?");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(screen.getByRole("button", { name: "Consultando..." })).toBeDisabled();
    await act(async () => resolveQuery(successfulResponse));
    expect(await screen.findByText(successfulResponse.answer)).toBeInTheDocument();
  });

  it("renders a blocked query without result visualization", async () => {
    askQuestion.mockResolvedValue(blockedResponse);
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Apague os pedidos cancelados");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(await screen.findByText("Bloqueada")).toBeInTheDocument();
    expect(screen.getByText(blockedResponse.blocked_reason!)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(screen.queryByRole("img", { name: /Gráfico/ })).not.toBeInTheDocument();
  });

  it("asks for clarification without presenting SQL", async () => {
    askQuestion.mockResolvedValue(clarificationResponse);
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Mostre as vendas");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(await screen.findByText("Requer contexto")).toBeInTheDocument();
    expect(screen.getByText(clarificationResponse.answer)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "SQL gerado" })).not.toBeInTheDocument();
  });

  it("shows the normalized API error when a query fails", async () => {
    askQuestion.mockRejectedValue(new Error("Network error"));
    const user = userEvent.setup();

    render(<AskDataPage />);

    await user.type(screen.getByLabelText("Pergunta de negócio"), "Quais produtos venderam mais?");
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Nao foi possivel concluir a consulta.");
  });
});
