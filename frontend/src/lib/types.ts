export type AppView = "dashboard" | "ask" | "catalog" | "history" | "metrics";

export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CatalogColumn {
  name: string;
  type: string;
  description: string;
  queryable: boolean;
}

export interface CatalogTableSummary {
  name: string;
  description: string;
  queryable: boolean;
}

export interface CatalogTableSchema extends CatalogTableSummary {
  columns: CatalogColumn[];
}

export type QueryStatus = "success" | "blocked" | "needs_clarification" | "error";

export interface AskQueryResponse {
  query_id: number;
  status: Exclude<QueryStatus, "error">;
  answer: string;
  generated_sql: string | null;
  blocked_reason: string | null;
  columns: string[];
  rows: Array<Record<string, unknown>>;
  chart: {
    type: "bar" | "line" | "pie" | "table" | "metric";
    x: string | null;
    y: string | null;
  };
  metadata: {
    provider_used: string;
    model_used: string;
    execution_time_ms: number;
  };
}

export interface QueryHistoryItem {
  id: number;
  question: string;
  generated_sql: string | null;
  status: QueryStatus;
  blocked_reason: string | null;
  answer_summary: string | null;
  execution_time_ms: number | null;
  provider_used: string | null;
  model_used: string | null;
  created_at: string;
}

export interface MetricsOverview {
  total_queries: number;
  successful_queries: number;
  blocked_queries: number;
  success_rate: number;
  average_execution_time_ms: number;
  positive_feedback: number;
}

export interface CountMetric {
  count: number;
}

export interface StatusMetric extends CountMetric {
  status: string;
}

export interface BlockedReasonMetric extends CountMetric {
  reason: string;
}

export interface QuestionMetric extends CountMetric {
  question: string;
}

export interface DailyQueryMetric extends CountMetric {
  date: string;
}

export interface TableMetric extends CountMetric {
  table_name: string;
}

export interface QueryMetrics {
  by_status: StatusMetric[];
  blocked_reasons: BlockedReasonMetric[];
  most_common_questions: QuestionMetric[];
  queries_by_day: DailyQueryMetric[];
}

export interface TableMetrics {
  tables: TableMetric[];
}
