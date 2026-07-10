import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  icon: LucideIcon;
}

export function EmptyState({ title, description, icon: Icon }: EmptyStateProps): JSX.Element {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center px-5 text-center">
      <span className="grid size-10 place-items-center rounded-md bg-slate-100 text-slate-500">
        <Icon size={20} aria-hidden="true" />
      </span>
      <h3 className="mt-4 text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-1 max-w-sm text-sm leading-6 text-slate-500">{description}</p>
    </div>
  );
}
