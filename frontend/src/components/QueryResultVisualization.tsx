import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AskQueryResponse } from "../lib/types";

interface QueryResultVisualizationProps {
  columns: string[];
  rows: Array<Record<string, unknown>>;
  chart: AskQueryResponse["chart"];
}

const chartLabels = {
  bar: "Gráfico de barras",
  line: "Gráfico de linha",
  pie: "Gráfico de participação",
} as const;

const pieColors = ["#157b63", "#168aad", "#e6a23c", "#7c6db0", "#d05a6e", "#4f7cac"];
const numberFormatter = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 });

function shortenLabel(value: unknown): string {
  const label = String(value ?? "-");
  return label.length > 18 ? `${label.slice(0, 17)}…` : label;
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function QueryResultVisualization({ columns, rows, chart }: QueryResultVisualizationProps): JSX.Element | null {
  if (chart.type === "table" || !chart.x || !chart.y || !columns.includes(chart.x) || !columns.includes(chart.y)) {
    return null;
  }
  const xKey = chart.x;
  const yKey = chart.y;

  if (rows.length === 0) {
    return (
      <article className="rounded-lg border border-line bg-panel px-5 py-8 text-center shadow-panel">
        <h2 className="text-sm font-semibold text-ink">Visualização</h2>
        <p className="mt-2 text-sm text-slate-500">Nenhum registro para visualizar.</p>
      </article>
    );
  }

  const data = rows
    .map((row) => ({ ...row, [yKey]: toNumber(row[yKey]) }))
    .filter((row) => row[yKey] !== null);

  if (data.length === 0) {
    return null;
  }

  if (chart.type === "metric") {
    const first = data[0];
    return (
      <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
        <h2 className="text-sm font-semibold text-ink">Métrica principal</h2>
        <div className="mt-4 border-l-4 border-accent pl-4">
          <p className="text-3xl font-semibold text-ink">{numberFormatter.format(first[yKey] as number)}</p>
          <p className="mt-1 text-sm text-slate-500">{String(first[xKey] ?? yKey)}</p>
        </div>
      </article>
    );
  }

  const label = chartLabels[chart.type];
  const commonAxis = (
    <>
      <CartesianGrid stroke="#e5ece7" strokeDasharray="3 3" vertical={false} />
      <XAxis dataKey={xKey} tickFormatter={shortenLabel} tick={{ fill: "#64748b", fontSize: 12 }} />
      <YAxis tickFormatter={(value) => numberFormatter.format(Number(value))} tick={{ fill: "#64748b", fontSize: 12 }} />
      <Tooltip formatter={(value) => numberFormatter.format(Number(value))} />
    </>
  );

  return (
    <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
      <h2 className="text-sm font-semibold text-ink">{label}</h2>
      <div className="mt-4 h-72 min-w-0" role="img" aria-label={label}>
        <ResponsiveContainer width="100%" height="100%">
          {chart.type === "bar" ? (
            <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
              {commonAxis}
              <Bar dataKey={yKey} fill="#157b63" radius={[4, 4, 0, 0]} maxBarSize={54} />
            </BarChart>
          ) : chart.type === "line" ? (
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              {commonAxis}
              <Line type="monotone" dataKey={yKey} stroke="#168aad" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
            </LineChart>
          ) : (
            <PieChart>
              <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="46%" outerRadius="72%" paddingAngle={2}>
                {data.map((row, index) => (
                  <Cell key={`${String(row[xKey])}-${index}`} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => numberFormatter.format(Number(value))} />
              <Legend verticalAlign="bottom" iconType="circle" />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </article>
  );
}
