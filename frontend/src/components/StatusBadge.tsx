import type { QueryStatus } from "../lib/types";

interface StatusBadgeProps {
  status: QueryStatus;
}

const statusLabels: Record<QueryStatus, string> = {
  success: "Aprovada",
  blocked: "Bloqueada",
  needs_clarification: "Requer contexto",
  error: "Erro",
};

const statusClasses: Record<QueryStatus, string> = {
  success: "bg-emerald-100 text-emerald-800",
  blocked: "bg-red-100 text-red-800",
  needs_clarification: "bg-amber-100 text-amber-800",
  error: "bg-slate-200 text-slate-700",
};

export function StatusBadge({ status }: StatusBadgeProps): JSX.Element {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${statusClasses[status]}`}>{statusLabels[status]}</span>;
}
