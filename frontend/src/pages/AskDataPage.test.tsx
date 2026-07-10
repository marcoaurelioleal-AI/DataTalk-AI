import { render, screen } from "@testing-library/react";
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
    expect(screen.getByText("Notebook Pro")).toBeInTheDocument();
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
});
