import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "./LoginPage";

describe("LoginPage", () => {
  it("submits the credentials entered by the user", async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<LoginPage onLogin={onLogin} />);

    const email = screen.getByLabelText("E-mail");
    const password = screen.getByLabelText("Senha");
    await user.clear(email);
    await user.type(email, "viewer@datatalk.ai");
    await user.clear(password);
    await user.type(password, "viewer123");
    await user.click(screen.getByRole("button", { name: "Entrar no workspace" }));

    expect(onLogin).toHaveBeenCalledWith("viewer@datatalk.ai", "viewer123");
  });

  it("shows a login error returned by the application", async () => {
    const onLogin = vi.fn().mockRejectedValue(new Error("Credenciais invalidas."));
    const user = userEvent.setup();

    render(<LoginPage onLogin={onLogin} />);

    await user.click(screen.getByRole("button", { name: "Entrar no workspace" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Credenciais invalidas.");
  });

  it("prevents duplicate submissions while login is pending", async () => {
    let finishLogin: () => void = () => undefined;
    const onLogin = vi.fn(() => new Promise<void>((resolve) => { finishLogin = resolve; }));
    const user = userEvent.setup();

    render(<LoginPage onLogin={onLogin} />);

    await user.click(screen.getByRole("button", { name: "Entrar no workspace" }));

    expect(screen.getByRole("button", { name: "Entrando..." })).toBeDisabled();
    expect(onLogin).toHaveBeenCalledOnce();
    await act(async () => finishLogin());
  });
});
