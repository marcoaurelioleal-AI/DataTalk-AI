import { LogOut } from "lucide-react";

import type { User } from "../lib/types";

interface HeaderProps {
  user: User;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps): JSX.Element {
  return (
    <header className="flex min-h-20 items-center justify-between border-b border-line bg-white px-5 md:px-8">
      <div>
        <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">Workspace de análise</p>
        <p className="mt-1 text-sm font-medium text-ink">Dados de negócio com SQL validado</p>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-semibold text-ink">{user.name}</p>
          <p className="text-xs text-slate-500">{user.role}</p>
        </div>
        <span className="grid size-9 place-items-center rounded-full bg-emerald-100 text-sm font-bold text-accentdark" aria-hidden="true">
          {user.name.slice(0, 1).toUpperCase()}
        </span>
        <button
          type="button"
          onClick={onLogout}
          title="Sair"
          aria-label="Sair"
          className="grid size-9 place-items-center rounded-md text-slate-500 transition-colors hover:bg-red-50 hover:text-red-700"
        >
          <LogOut size={18} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
