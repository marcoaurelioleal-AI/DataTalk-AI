import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("shows the human-readable label for each query status", () => {
    const { rerender } = render(<StatusBadge status="success" />);
    expect(screen.getByText("Aprovada")).toBeInTheDocument();

    rerender(<StatusBadge status="blocked" />);
    expect(screen.getByText("Bloqueada")).toBeInTheDocument();

    rerender(<StatusBadge status="needs_clarification" />);
    expect(screen.getByText("Requer contexto")).toBeInTheDocument();

    rerender(<StatusBadge status="error" />);
    expect(screen.getByText("Erro")).toBeInTheDocument();
  });
});
