import { BookOpen, Database, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage, getCatalogSchema, getCatalogTables } from "../lib/api";
import type { CatalogTableSchema, CatalogTableSummary } from "../lib/types";

export function CatalogPage(): JSX.Element {
  const [tables, setTables] = useState<CatalogTableSummary[]>([]);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [schema, setSchema] = useState<CatalogTableSchema | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    async function loadTables(): Promise<void> {
      try {
        const response = await getCatalogTables();
        if (isCurrent) {
          setTables(response);
          setSelectedTable(response[0]?.name ?? null);
        }
      } catch (loadError) {
        if (isCurrent) {
          setError(getApiErrorMessage(loadError));
        }
      }
    }
    void loadTables();
    return () => {
      isCurrent = false;
    };
  }, []);

  useEffect(() => {
    let isCurrent = true;
    if (selectedTable === null) {
      setSchema(null);
      return undefined;
    }
    const tableName: string = selectedTable;
    async function loadSchema(): Promise<void> {
      try {
        const response = await getCatalogSchema(tableName);
        if (isCurrent) {
          setSchema(response);
        }
      } catch (loadError) {
        if (isCurrent) {
          setError(getApiErrorMessage(loadError));
        }
      }
    }
    void loadSchema();
    return () => {
      isCurrent = false;
    };
  }, [selectedTable]);

  if (error) {
    return <EmptyState icon={ShieldAlert} title="Não foi possível carregar o catálogo" description={error} />;
  }

  return (
    <div className="space-y-7">
      <section>
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">Catálogo de dados</p>
        <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">Tabelas disponíveis para análise</h1>
        <p className="mt-2 text-sm text-slate-600">O agente usa somente as tabelas expostas neste catálogo autorizado.</p>
      </section>

      <section className="grid gap-5 lg:grid-cols-[minmax(15rem,0.7fr)_minmax(0,1.3fr)]">
        <article className="overflow-hidden rounded-lg border border-line bg-panel shadow-panel">
          <div className="border-b border-line px-5 py-4">
            <h2 className="text-sm font-semibold text-ink">Tabelas permitidas</h2>
          </div>
          <div className="divide-y divide-line">
            {tables.map((table) => (
              <button
                type="button"
                key={table.name}
                onClick={() => setSelectedTable(table.name)}
                className={`flex w-full items-start gap-3 px-5 py-4 text-left transition ${selectedTable === table.name ? "bg-emerald-50" : "hover:bg-slate-50"}`}
              >
                <Database size={17} className={selectedTable === table.name ? "mt-0.5 text-accent" : "mt-0.5 text-slate-400"} aria-hidden="true" />
                <span>
                  <span className="block font-mono text-sm font-semibold text-ink">{table.name}</span>
                  <span className="mt-1 block text-xs leading-5 text-slate-500">{table.description}</span>
                </span>
              </button>
            ))}
            {!tables.length && <EmptyState icon={BookOpen} title="Carregando tabelas" description="Buscando o catálogo autorizado." />}
          </div>
        </article>

        <article className="overflow-hidden rounded-lg border border-line bg-panel shadow-panel">
          {schema ? (
            <>
              <div className="border-b border-line px-5 py-4">
                <p className="font-mono text-sm font-semibold text-ink">{schema.name}</p>
                <p className="mt-1 text-sm text-slate-500">{schema.description}</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>
                      <th className="px-5 py-3 font-semibold">Coluna</th>
                      <th className="px-5 py-3 font-semibold">Tipo</th>
                      <th className="px-5 py-3 font-semibold">Descrição</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {schema.columns.map((column) => (
                      <tr key={column.name} className="text-slate-700">
                        <td className="px-5 py-3 font-mono text-xs font-semibold text-ink">{column.name}</td>
                        <td className="px-5 py-3 font-mono text-xs text-slate-500">{column.type}</td>
                        <td className="px-5 py-3">{column.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <EmptyState icon={Database} title="Selecione uma tabela" description="As colunas e os tipos permitidos aparecerão aqui." />
          )}
        </article>
      </section>
    </div>
  );
}
