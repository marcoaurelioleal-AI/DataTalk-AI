import { BarChart3, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "../components/EmptyState";
import { getApiErrorMessage, getQueryMetrics, getTableMetrics } from "../lib/api";
import type { QueryMetrics, TableMetrics } from "../lib/types";

interface MetricsData {
  queryMetrics: QueryMetrics;
  tableMetrics: TableMetrics;
}

export function MetricsPage(): JSX.Element {
  const [data, setData] = useState<MetricsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    async function loadMetrics(): Promise<void> {
      try {
        const [queryMetrics, tableMetrics] = await Promise.all([getQueryMetrics(), getTableMetrics()]);
        if (isCurrent) {
          setData({ queryMetrics, tableMetrics });
        }
      } catch (loadError) {
        if (isCurrent) {
          setError(getApiErrorMessage(loadError));
        }
      }
    }
    void loadMetrics();
    return () => {
      isCurrent = false;
    };
  }, []);

  if (error) {
    return <EmptyState icon={ShieldAlert} title="Não foi possível carregar as métricas" description={error} />;
  }

  if (!data) {
    return <EmptyState icon={BarChart3} title="Carregando métricas" description="Calculando os indicadores do seu workspace." />;
  }

  const dailyData = data.queryMetrics.queries_by_day.map((item) => ({ date: item.date, total: item.count }));
  const blockedData = data.queryMetrics.blocked_reasons.map((item) => ({ reason: item.reason, total: item.count }));
  const tablesData = data.tableMetrics.tables.map((item) => ({ table: item.table_name, total: item.count }));

  return (
    <div className="space-y-7">
      <section>
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">Métricas</p>
        <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">Uso, segurança e cobertura dos dados</h1>
        <p className="mt-2 text-sm text-slate-600">Indicadores construídos a partir do histórico e do feedback do usuário.</p>
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Perguntas por dia</h2>
          <p className="mt-1 text-sm text-slate-500">Evolução do volume de consultas.</p>
          <div className="mt-6 h-64">
            {dailyData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dailyData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "#f0f5f1" }} />
                  <Bar dataKey="total" fill="#157b63" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState icon={BarChart3} title="Sem volume registrado" description="As consultas aparecerão neste gráfico." />}
          </div>
        </article>

        <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
          <h2 className="text-base font-semibold text-ink">Motivos de bloqueio</h2>
          <p className="mt-1 text-sm text-slate-500">Ocorrências identificadas pelo SQL Safety Validator.</p>
          <div className="mt-6 h-64">
            {blockedData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={blockedData} layout="vertical" margin={{ top: 4, right: 12, left: 12, bottom: 0 }}>
                  <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="reason" type="category" width={128} tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "#fff1f2" }} />
                  <Bar dataKey="total" fill="#e05d5d" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState icon={ShieldAlert} title="Nenhum bloqueio registrado" description="O histórico de bloqueios aparecerá aqui." />}
          </div>
        </article>

        <article className="rounded-lg border border-line bg-panel p-5 shadow-panel xl:col-span-2">
          <h2 className="text-base font-semibold text-ink">Tabelas mais consultadas</h2>
          <p className="mt-1 text-sm text-slate-500">Uso das tabelas permitidas pelo catálogo.</p>
          <div className="mt-6 h-64">
            {tablesData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tablesData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="table" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "#f0f5f1" }} />
                  <Bar dataKey="total" fill="#168aad" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState icon={BarChart3} title="Sem tabelas consultadas" description="Tabelas usadas em SQL aprovado aparecerão aqui." />}
          </div>
        </article>
      </section>
    </div>
  );
}
