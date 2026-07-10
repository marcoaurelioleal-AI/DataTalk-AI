import { DatabaseZap } from "lucide-react";

interface BrandMarkProps {
  compact?: boolean;
}

export function BrandMark({ compact = false }: BrandMarkProps): JSX.Element {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-accent text-white shadow-sm">
        <DatabaseZap size={19} aria-hidden="true" />
      </span>
      {!compact && (
        <span className="leading-tight">
          <strong className="block text-sm font-semibold tracking-wide text-ink">DataTalk</strong>
          <span className="block text-xs font-medium text-slate-500">AI workspace</span>
        </span>
      )}
    </div>
  );
}
