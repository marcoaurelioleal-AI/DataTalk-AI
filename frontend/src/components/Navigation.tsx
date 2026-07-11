import {
  BarChart3,
  BookOpen,
  History,
  LayoutDashboard,
  MessageSquareText,
  type LucideIcon,
} from "lucide-react";

import type { AppView } from "../lib/types";
import { BrandMark } from "./BrandMark";

interface NavigationProps {
  activeView: AppView;
  onChange: (view: AppView) => void;
}

interface NavigationItem {
  label: string;
  view: AppView;
  icon: LucideIcon;
}

const navigationItems: NavigationItem[] = [
  { label: "Visão geral", view: "dashboard", icon: LayoutDashboard },
  { label: "Consultar dados", view: "ask", icon: MessageSquareText },
  { label: "Catálogo", view: "catalog", icon: BookOpen },
  { label: "Histórico", view: "history", icon: History },
  { label: "Métricas", view: "metrics", icon: BarChart3 },
];

export function Navigation({ activeView, onChange }: NavigationProps): JSX.Element {
  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-line bg-white md:min-h-screen md:w-64 md:border-b-0 md:border-r">
      <div className="flex h-20 items-center px-5 md:px-6">
        <BrandMark />
      </div>
      <nav aria-label="Navegação principal" className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:px-4">
        {navigationItems.map(({ label, view, icon: Icon }) => {
          const isActive = activeView === view;
          return (
            <button
              key={view}
              type="button"
              onClick={() => onChange(view)}
              className={`flex h-10 shrink-0 items-center gap-3 rounded-md px-3 text-sm font-medium transition-colors ${
                isActive ? "bg-emerald-50 text-accentdark" : "text-slate-600 hover:bg-slate-100 hover:text-ink"
              }`}
            >
              <Icon size={17} aria-hidden="true" />
              {label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
