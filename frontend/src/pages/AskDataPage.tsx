import { Check, Copy, Send, ShieldAlert, ThumbsDown, ThumbsUp } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { EmptyState } from "../components/EmptyState";
import { QueryResultVisualization } from "../components/QueryResultVisualization";
import { StatusBadge } from "../components/StatusBadge";
import { askQuestion, getApiErrorMessage, submitFeedback } from "../lib/api";
import { formatDuration } from "../lib/format";
import type { AskQueryResponse } from "../lib/types";

const exampleQuestions = [
  "Quais produtos venderam mais este mês?",
  "Qual canal trouxe mais receita?",
  "Quais clientes compraram mais?",
];

export function AskDataPage(): JSX.Element {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const copiedTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (copiedTimerRef.current !== null) {
        window.clearTimeout(copiedTimerRef.current);
      }
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setFeedbackMessage(null);
    setIsSubmitting(true);
    try {
      setResult(await askQuestion(question));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleFeedback(isHelpful: boolean): Promise<void> {
    if (!result) {
      return;
    }
    try {
      await submitFeedback(result.query_id, isHelpful);
      setFeedbackMessage("Feedback registrado.");
    } catch (feedbackError) {
      setFeedbackMessage(getApiErrorMessage(feedbackError));
    }
  }

  async function copySql(): Promise<void> {
    if (!result?.generated_sql) {
      return;
    }
    await navigator.clipboard.writeText(result.generated_sql);
    setCopied(true);
    if (copiedTimerRef.current !== null) {
      window.clearTimeout(copiedTimerRef.current);
    }
    copiedTimerRef.current = window.setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="space-y-7">
      <section>
        <p className="text-xs font-semibold uppercase tracking-widest text-accent">Consultar dados</p>
        <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">Faça uma pergunta para o agente</h1>
        <p className="mt-2 text-sm text-slate-600">A consulta gerada passa pela validação de segurança antes de ser processada.</p>
      </section>

      <form onSubmit={handleSubmit} className="rounded-lg border border-line bg-panel p-5 shadow-panel">
        <label htmlFor="question" className="text-sm font-semibold text-ink">Pergunta de negócio</label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          minLength={3}
          maxLength={1000}
          required
          placeholder="Ex.: Quais produtos tiveram maior volume de vendas no último mês?"
          className="mt-3 min-h-32 w-full resize-y rounded-md border border-line bg-slate-50 p-3 text-sm leading-6 text-ink outline-none transition focus:border-accent focus:bg-white focus:ring-2 focus:ring-emerald-100"
        />
        <div className="mt-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div className="flex flex-wrap gap-2">
            {exampleQuestions.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setQuestion(example)}
                className="rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-emerald-300 hover:text-accentdark"
              >
                {example}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={isSubmitting || question.trim().length < 3}
            className="flex h-10 shrink-0 items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white transition hover:bg-accentdark disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Send size={16} aria-hidden="true" />
            {isSubmitting ? "Consultando..." : "Consultar dados"}
          </button>
        </div>
        {error && <p role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
      </form>

      {!result && !error && <EmptyState icon={Send} title="Aguardando uma pergunta" description="A resposta, o SQL gerado e o status da validação aparecerão neste espaço." />}

      {result && (
        <section className="space-y-5">
          <article className="rounded-lg border border-line bg-panel p-5 shadow-panel">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h2 className="text-lg font-semibold text-ink">Resposta do agente</h2>
                  <StatusBadge status={result.status} />
                </div>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">{result.answer}</p>
              </div>
              <span className="shrink-0 text-xs font-medium text-slate-500">{formatDuration(result.metadata.execution_time_ms)}</span>
            </div>
            {result.blocked_reason && (
              <p className="mt-4 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                <ShieldAlert size={17} className="mt-0.5 shrink-0" aria-hidden="true" />
                {result.blocked_reason}
              </p>
            )}
            <div className="mt-5 flex items-center gap-2 border-t border-line pt-4">
              <span className="text-sm text-slate-600">Esta resposta foi útil?</span>
              <button type="button" title="Resposta útil" aria-label="Resposta útil" onClick={() => void handleFeedback(true)} className="grid size-8 place-items-center rounded-md text-slate-500 hover:bg-emerald-100 hover:text-emerald-800">
                <ThumbsUp size={16} aria-hidden="true" />
              </button>
              <button type="button" title="Resposta não útil" aria-label="Resposta não útil" onClick={() => void handleFeedback(false)} className="grid size-8 place-items-center rounded-md text-slate-500 hover:bg-red-100 hover:text-red-800">
                <ThumbsDown size={16} aria-hidden="true" />
              </button>
              {feedbackMessage && <span className="text-xs font-medium text-slate-500">{feedbackMessage}</span>}
            </div>
          </article>

          {result.generated_sql && (
            <article className="overflow-hidden rounded-lg border border-line bg-panel shadow-panel">
              <div className="flex items-center justify-between border-b border-line px-5 py-3">
                <h2 className="text-sm font-semibold text-ink">SQL gerado</h2>
                <button type="button" onClick={() => void copySql()} title="Copiar SQL" aria-label="Copiar SQL" className="grid size-8 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-ink">
                  {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
                </button>
              </div>
              <pre className="overflow-x-auto bg-slate-950 p-5 text-xs leading-6 text-emerald-100"><code>{result.generated_sql}</code></pre>
            </article>
          )}

          <QueryResultVisualization columns={result.columns} rows={result.rows} chart={result.chart} />

          {result.columns.length > 0 && (
            <article className="overflow-hidden rounded-lg border border-line bg-panel shadow-panel">
              <div className="border-b border-line px-5 py-3">
                <h2 className="text-sm font-semibold text-ink">Resultado tabular</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                    <tr>{result.columns.map((column) => <th key={column} className="px-5 py-3 font-semibold">{column}</th>)}</tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {result.rows.map((row) => (
                      <tr key={`${result.query_id}-${result.columns.map((column) => String(row[column] ?? "")).join("|")}`} className="text-slate-700">
                        {result.columns.map((column) => <td key={column} className="px-5 py-3">{String(row[column] ?? "-")}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {result.rows.length === 0 && <p className="px-5 py-6 text-center text-sm text-slate-500">Nenhum registro encontrado.</p>}
              </div>
            </article>
          )}
        </section>
      )}
    </div>
  );
}
