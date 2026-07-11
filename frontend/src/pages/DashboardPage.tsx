import { Activity, CircleCheckBig, Clock3, MessageCircleHeart, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { getApiErrorMessage, getOverview, getQueryMetrics, getTableMetrics } from "../lib/api";
import { formatDuration, formatPercent } from "../lib/format";
import type { MetricsOverview, QueryMetrics, TableMetrics } from "../lib/types";

interface DashboardData {
  overview: MetricsOverview;
  queryMetrics: QueryMetrics;
  tableMetrics: TableMetrics;
}

export function DashboardPage(): JSX.Element {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    async function loadDashboard(): Promise<void> {
      try {
        const [overview, queryMetrics, tableMetrics] = await Promise.all([getOverview(), getQueryMetrics(), getTableMetrics()]);
        if (isCurrent) {
          setData({ overview, queryMetrics, tableMetrics });
        }
      } catch (loadError) {
        if (isCurrent) {
          setError(getApiErrorMessage(loadError));
        }
      }
    }
    void loadDashboard();
    return () => {
      isCurrent = false;
    };
  }, []);

  if (error) {
    return <EmptyState icon={ShieldAlert} title="Não foi possível carregar a visão geral" description={error} />;
  }

  if (!data) {
    return <EmptyState icon={Activity} title="Carregando métricas" description="Buscando a atividade mais recente do seu workspace." />;
  }

  const { overview, queryMetrics, tableMetrics } = data;
  const statusData = queryMetrics.by_status.map((item) => ({ name: item.status, total: item.count }));
  const tableData = tableMetrics.tables.slice(0, 5).map((item) => ({ name: item.table_name, total: item.count }));

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-accent">Visão geral</p>
          <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">Atividade do workspace</h1>
          <p className="mt-2 text-sm text-slate-600">Acompanhe o uso do agente, a segurança das consultas e o retorno recebido.</p>
        </div>
        <p className="text-sm font-medium text-slate-500">Taxa de sucesso: <span className="text-accentdark">{formatPercent(overview.success_rate)}</span></p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Perguntas" value={overview.total_queries.toLocaleString("pt-BR")} icon={Activity} tone="blue" />
        <MetricCard label="Aprovadas" value={overview.successful_queries.toLocaleString("pt-BR")} icon={CircleCheckBig} tone="green" />
        <MetricCard label="Bloqueadas" value={overview.blocked_queries.toLocaleString("pt-BR")} icon={ShieldAlert} tone="rose" />
        <MetricCard label="Tempo médio" value={formatDuration(overview.average_execution_time_ms)} icon={Clock3} tone="amber" />
        <MetricCard label="Feedback positivo" value={overview.positive_feedback.toLocaleString("pt-BR")} icon={MessageCircleHeart} tone="teal" />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
          <div>
            <h2 className="text-base font-semibold text-ink">Consultas por status</h2>
            <p className="mt-1 text-sm text-slate-500">Distribuição das solicitações registradas.</p>
          </div>
          <div className="mt-6 h-64">
            {statusData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "#f0f5f1" }} />
                  <Bar dataKey="total" fill="#157b63" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={Activity} title="Sem consultas ainda" description="As consultas feitas pelo agente aparecerão aqui." />
            )}
          </div>
        </article>

        <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
          <div>
            <h2 className="text-base font-semibold text-ink">Tabelas mais consultadas</h2>
            <p className="mt-1 text-sm text-slate-500">Apenas tabelas permitidas e queries aprovadas.</p>
          </div>
          <div className="mt-6 h-64">
            {tableData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tableData} layout="vertical" margin={{ top: 4, right: 16, left: 12, bottom: 0 }}>
                  <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="name" type="category" width={92} tick={{ fill: "#475569", fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: "#f0f5f1" }} />
                  <Bar dataKey="total" fill="#168aad" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState icon={Activity} title="Sem tabelas consultadas" description="Tabelas aprovadas pelo validador aparecerão aqui." />
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
