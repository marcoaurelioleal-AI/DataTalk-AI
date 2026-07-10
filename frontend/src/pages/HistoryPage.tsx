import { Clock3, History, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { StatusBadge } from "../components/StatusBadge";
import { getApiErrorMessage, getQueryHistory } from "../lib/api";
import { formatDate, formatDuration } from "../lib/format";
import type { QueryHistoryItem } from "../lib/types";

export function HistoryPage(): JSX.Element {
  const [history, setHistory] = useState<QueryHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    async function loadHistory(): Promise<void> {
      try {
        const response = await getQueryHistory();
        if (isCurrent) {
          setHistory(response);
        }
      } catch (loadError) {
        if (isCurrent) {
          setError(getApiErrorMessage(loadError));
        }
      }
    }
    void loadHistory();
    return () => {
      isCurrent = false;
    };
  }, []);

  if (error) {
    return <EmptyState icon={ShieldAlert} title="NÃ£o foi possÃ­vel carregar o histÃ³rico" description={error} />;
  }

  return (
    <div className="space-y-7">
      <section className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">HistÃ³rico</p>
          <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">Consultas registradas</h1>
          <p className="mt-2 text-sm text-slate-600">Cada solicitaÃ§Ã£o mantÃ©m a pergunta, o SQL, o status e a duraÃ§Ã£o para auditoria.</p>
        </div>
        {history && <span className="text-sm font-medium text-slate-500">{history.length.toLocaleString("pt-BR")} registros</span>}
      </section>

      <section className="overflow-hidden rounded-lg border border-line bg-panel shadow-panel">
        {!history ? (
          <EmptyState icon={History} title="Carregando histÃ³rico" description="Buscando as consultas do seu workspace." />
        ) : history.length === 0 ? (
          <EmptyState icon={History} title="Nenhuma consulta registrada" description="As perguntas feitas ao agente aparecerÃ£o neste histÃ³rico." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-[760px] w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-semibold">Pergunta</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                  <th className="px-5 py-3 font-semibold">Data</th>
                  <th className="px-5 py-3 font-semibold">DuraÃ§Ã£o</th>
                  <th className="px-5 py-3 font-semibold">Provider</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {history.map((item) => (
                  <tr key={item.id} className="align-top text-slate-700">
                    <td className="max-w-md px-5 py-4">
                      <p className="font-medium text-ink">{item.question}</p>
                      {item.generated_sql && <p className="mt-1 line-clamp-1 font-mono text-xs text-slate-500">{item.generated_sql}</p>}
                      {item.blocked_reason && <p className="mt-1 text-xs text-red-700">{item.blocked_reason}</p>}
                    </td>
                    <td className="px-5 py-4"><StatusBadge status={item.status} /></td>
                    <td className="whitespace-nowrap px-5 py-4 text-slate-600">{formatDate(item.created_at)}</td>
                    <td className="whitespace-nowrap px-5 py-4">
                      <span className="inline-flex items-center gap-1.5 text-slate-600"><Clock3 size={15} aria-hidden="true" />{formatDuration(item.execution_time_ms)}</span>
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-slate-500">{item.provider_used ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
