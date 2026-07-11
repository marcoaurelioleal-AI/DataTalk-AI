import { LoaderCircle } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";

import { AppShell } from "./components/AppShell";
import { clearStoredToken, getApiErrorMessage, getCurrentUser, getStoredToken, login } from "./lib/api";
import type { AppView, User } from "./lib/types";
import { LoginPage } from "./pages/LoginPage";

const DashboardPage = lazy(async () => ({ default: (await import("./pages/DashboardPage")).DashboardPage }));
const AskDataPage = lazy(async () => ({ default: (await import("./pages/AskDataPage")).AskDataPage }));
const CatalogPage = lazy(async () => ({ default: (await import("./pages/CatalogPage")).CatalogPage }));
const HistoryPage = lazy(async () => ({ default: (await import("./pages/HistoryPage")).HistoryPage }));
const MetricsPage = lazy(async () => ({ default: (await import("./pages/MetricsPage")).MetricsPage }));

function renderView(view: AppView): JSX.Element {
  switch (view) {
    case "ask":
      return <AskDataPage />;
    case "catalog":
      return <CatalogPage />;
    case "history":
      return <HistoryPage />;
    case "metrics":
      return <MetricsPage />;
    default:
      return <DashboardPage />;
  }
}

export function App(): JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [activeView, setActiveView] = useState<AppView>("dashboard");
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    let isCurrent = true;
    async function restoreSession(): Promise<void> {
      if (!getStoredToken()) {
        if (isCurrent) {
          setIsCheckingSession(false);
        }
        return;
      }
      try {
        const currentUser = await getCurrentUser();
        if (isCurrent) {
          setUser(currentUser);
        }
      } catch {
        clearStoredToken();
      } finally {
        if (isCurrent) {
          setIsCheckingSession(false);
        }
      }
    }
    void restoreSession();
    return () => {
      isCurrent = false;
    };
  }, []);

  async function handleLogin(email: string, password: string): Promise<void> {
    try {
      await login(email, password);
      setUser(await getCurrentUser());
      setActiveView("dashboard");
    } catch (error) {
      clearStoredToken();
      throw new Error(getApiErrorMessage(error));
    }
  }

  function handleLogout(): void {
    clearStoredToken();
    setUser(null);
    setActiveView("dashboard");
  }

  if (isCheckingSession) {
    return (
      <main className="grid min-h-screen place-items-center bg-canvas">
        <LoaderCircle className="animate-spin text-accent" size={26} aria-label="Carregando sessão" />
      </main>
    );
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <AppShell user={user} activeView={activeView} onViewChange={setActiveView} onLogout={handleLogout}>
      <Suspense
        fallback={
          <div className="grid min-h-80 place-items-center">
            <LoaderCircle className="animate-spin text-accent" size={24} aria-label="Carregando página" />
          </div>
        }
      >
        {renderView(activeView)}
      </Suspense>
    </AppShell>
  );
}
