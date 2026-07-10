import type { PropsWithChildren } from "react";

import type { AppView, User } from "../lib/types";
import { Header } from "./Header";
import { Navigation } from "./Navigation";

interface AppShellProps extends PropsWithChildren {
  user: User;
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  onLogout: () => void;
}

export function AppShell({ user, activeView, onViewChange, onLogout, children }: AppShellProps): JSX.Element {
  return (
    <div className="min-h-screen bg-canvas md:flex">
      <Navigation activeView={activeView} onChange={onViewChange} />
      <div className="min-w-0 flex-1">
        <Header user={user} onLogout={onLogout} />
        <main className="mx-auto w-full max-w-screen-2xl px-5 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}
