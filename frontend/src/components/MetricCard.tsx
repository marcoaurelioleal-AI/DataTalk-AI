import type { LucideIcon } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  tone: "green" | "blue" | "amber" | "rose" | "teal";
}

const toneClasses = {
  green: "bg-emerald-100 text-emerald-700",
  blue: "bg-sky-100 text-sky-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
  teal: "bg-teal-100 text-teal-700",
} as const;

export function MetricCard({ label, value, icon: Icon, tone }: MetricCardProps): JSX.Element {
  return (
    <article className="min-h-32 rounded-lg border border-line bg-panel p-4 shadow-panel">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <span className={`grid size-8 place-items-center rounded-md ${toneClasses[tone]}`}>
          <Icon size={16} aria-hidden="true" />
        </span>
      </div>
      <p className="mt-5 text-2xl font-semibold text-ink">{value}</p>
    </article>
  );
}
