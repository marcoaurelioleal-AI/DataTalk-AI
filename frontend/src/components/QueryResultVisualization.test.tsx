import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { QueryResultVisualization } from "./QueryResultVisualization";

const columns = ["category", "amount"];
const rows = [
  { category: "Enterprise", amount: 12500.75 },
  { category: "SMB", amount: 8200 },
];

describe("QueryResultVisualization", () => {
  it.each([
    ["bar", "Gráfico de barras"],
    ["line", "Gráfico de linha"],
    ["pie", "Gráfico de participação"],
  ] as const)("renders a %s chart when its axes are valid", (type, label) => {
    render(
      <QueryResultVisualization
        columns={columns}
        rows={rows}
        chart={{ type, x: "category", y: "amount" }}
      />,
    );

    expect(screen.getByRole("img", { name: label })).toBeInTheDocument();
  });

  it("renders the first numeric value as a metric", () => {
    render(
      <QueryResultVisualization
        columns={columns}
        rows={rows}
        chart={{ type: "metric", x: "category", y: "amount" }}
      />,
    );

    expect(screen.getByText("Métrica principal")).toBeInTheDocument();
    expect(screen.getByText("12.500,75")).toBeInTheDocument();
    expect(screen.getByText("Enterprise")).toBeInTheDocument();
  });

  it("does not render a chart when table is recommended", () => {
    const { container } = render(
      <QueryResultVisualization
        columns={columns}
        rows={rows}
        chart={{ type: "table", x: null, y: null }}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("falls back silently when an axis is missing or has no numeric values", () => {
    const { container } = render(
      <QueryResultVisualization
        columns={columns}
        rows={[{ category: "Enterprise", amount: "unknown" }]}
        chart={{ type: "bar", x: "missing", y: "amount" }}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it("shows an empty-result state when valid columns have no rows", () => {
    render(
      <QueryResultVisualization
        columns={columns}
        rows={[]}
        chart={{ type: "bar", x: "category", y: "amount" }}
      />,
    );

    expect(screen.getByText("Nenhum registro para visualizar.")).toBeInTheDocument();
  });
});
