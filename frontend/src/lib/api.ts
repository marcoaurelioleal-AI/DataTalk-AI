import axios from "axios";

import type {
  AskQueryResponse,
  CatalogTableSchema,
  CatalogTableSummary,
  MetricsOverview,
  QueryHistoryItem,
  QueryMetrics,
  TableMetrics,
  TokenResponse,
  User,
} from "./types";

const TOKEN_KEY = "datatalk_access_token";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return "Não foi possível concluir a solicitação. Tente novamente.";
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", { email, password });
  window.localStorage.setItem(TOKEN_KEY, data.access_token);
  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await api.get<User>("/users/me");
  return data;
}

export async function getOverview(): Promise<MetricsOverview> {
  const { data } = await api.get<MetricsOverview>("/metrics/overview");
  return data;
}

export async function getQueryMetrics(): Promise<QueryMetrics> {
  const { data } = await api.get<QueryMetrics>("/metrics/queries");
  return data;
}

export async function getTableMetrics(): Promise<TableMetrics> {
  const { data } = await api.get<TableMetrics>("/metrics/tables");
  return data;
}

export async function askQuestion(question: string): Promise<AskQueryResponse> {
  const { data } = await api.post<AskQueryResponse>("/queries/ask", { question });
  return data;
}

export async function getCatalogTables(): Promise<CatalogTableSummary[]> {
  const { data } = await api.get<CatalogTableSummary[]>("/catalog/tables");
  return data;
}

export async function getCatalogSchema(tableName: string): Promise<CatalogTableSchema> {
  const { data } = await api.get<CatalogTableSchema>(`/catalog/tables/${tableName}/schema`);
  return data;
}

export async function getQueryHistory(): Promise<QueryHistoryItem[]> {
  const { data } = await api.get<QueryHistoryItem[]>("/queries/history");
  return data;
}

export async function submitFeedback(queryId: number, isHelpful: boolean): Promise<void> {
  await api.post(`/queries/${queryId}/feedback`, {
    rating: isHelpful ? 5 : 1,
    is_helpful: isHelpful,
  });
}
