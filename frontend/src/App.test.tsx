import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { User } from "./lib/types";
import { App } from "./App";

const apiMocks = vi.hoisted(() => ({
  clearStoredToken: vi.fn(),
  getApiErrorMessage: vi.fn(() => "Não foi possível entrar."),
  getCurrentUser: vi.fn(),
  getStoredToken: vi.fn(),
  login: vi.fn(),
}));

vi.mock("./lib/api", () => apiMocks);
vi.mock("./pages/DashboardPage", () => ({ DashboardPage: () => <h1>Painel autenticado</h1> }));
vi.mock("./pages/AskDataPage", () => ({ AskDataPage: () => <h1>Consulta protegida</h1> }));
vi.mock("./pages/CatalogPage", () => ({ CatalogPage: () => <h1>Catálogo protegido</h1> }));
vi.mock("./pages/HistoryPage", () => ({ HistoryPage: () => <h1>Histórico protegido</h1> }));
vi.mock("./pages/MetricsPage", () => ({ MetricsPage: () => <h1>Métricas protegidas</h1> }));

const currentUser: User = {
  id: 1,
  name: "Analyst DataTalk",
  email: "analyst@datatalk.ai",
  role: "analyst",
  is_active: true,
  created_at: "2026-07-11T12:00:00Z",
};

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.getStoredToken.mockReturnValue(null);
  });

  it("keeps protected content hidden when there is no stored token", async () => {
    render(<App />);

    expect(await screen.findByRole("heading", { name: "Entre no seu workspace" })).toBeInTheDocument();
    expect(screen.queryByText("Painel autenticado")).not.toBeInTheDocument();
    expect(apiMocks.getCurrentUser).not.toHaveBeenCalled();
  });

  it("shows session loading and restores a valid user", async () => {
    apiMocks.getStoredToken.mockReturnValue("valid-token");
    apiMocks.getCurrentUser.mockResolvedValue(currentUser);

    render(<App />);

    expect(screen.getByLabelText("Carregando sessão")).toBeInTheDocument();
    expect(await screen.findByRole("heading", { name: "Painel autenticado" })).toBeInTheDocument();
  });

  it("clears an invalid token before returning to login", async () => {
    apiMocks.getStoredToken.mockReturnValue("expired-token");
    apiMocks.getCurrentUser.mockRejectedValue(new Error("Token expirado"));

    render(<App />);

    expect(await screen.findByRole("heading", { name: "Entre no seu workspace" })).toBeInTheDocument();
    expect(apiMocks.clearStoredToken).toHaveBeenCalledOnce();
  });

  it("opens the protected dashboard after a successful login", async () => {
    apiMocks.login.mockResolvedValue({ access_token: "token", token_type: "bearer" });
    apiMocks.getCurrentUser.mockResolvedValue(currentUser);
    const user = userEvent.setup();

    render(<App />);

    await screen.findByRole("heading", { name: "Entre no seu workspace" });
    await user.click(screen.getByRole("button", { name: "Entrar no workspace" }));

    expect(await screen.findByRole("heading", { name: "Painel autenticado" })).toBeInTheDocument();
    expect(apiMocks.login).toHaveBeenCalledWith("analyst@datatalk.ai", "analyst123");
  });

  it("navigates between protected views for a restored session", async () => {
    apiMocks.getStoredToken.mockReturnValue("valid-token");
    apiMocks.getCurrentUser.mockResolvedValue(currentUser);
    const user = userEvent.setup();

    render(<App />);

    await screen.findByRole("heading", { name: "Painel autenticado" });
    await user.click(screen.getByRole("button", { name: "Consultar dados" }));

    expect(await screen.findByRole("heading", { name: "Consulta protegida" })).toBeInTheDocument();
  });
});
