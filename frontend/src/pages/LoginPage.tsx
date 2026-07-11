import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { useState, type FormEvent } from "react";

import { BrandMark } from "../components/BrandMark";

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<void>;
}

export function LoginPage({ onLogin }: LoginPageProps): JSX.Element {
  const [email, setEmail] = useState("analyst@datatalk.ai");
  const [password, setPassword] = useState("analyst123");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await onLogin(email, password);
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : "Não foi possível entrar.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen bg-canvas lg:grid lg:grid-cols-[minmax(0,1.08fr)_minmax(26rem,0.92fr)]">
      <section
      aria-hidden="true"
      className="relative hidden min-h-screen overflow-hidden bg-ink bg-cover bg-bottom lg:block"
      style={{ backgroundImage: "url('/images/datatalk-login-workspace.png')" }}
      >
        <div className="relative z-10 p-10 text-white">
          <BrandMark compact />
          <h1 className="mt-12 max-w-md text-4xl font-semibold leading-tight">DataTalk AI</h1>
          <p className="mt-3 max-w-md text-sm leading-6 text-emerald-50/80">Consulta de dados de negócio com geração de SQL rastreável e validação de segurança.</p>
        </div>
      </section>
      <section className="flex min-h-screen items-center justify-center p-5 sm:p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden">
            <BrandMark />
          </div>
          <div className="mt-12 lg:mt-0">
            <p className="text-xs font-semibold uppercase tracking-widest text-accent">Acesso seguro</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink">Entre no seu workspace</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">Use sua conta para consultar os dados e acompanhar as decisões geradas pelo agente.</p>
          </div>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-ink">
              E-mail
              <span className="relative mt-2 block">
                <Mail className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={17} aria-hidden="true" />
                <input
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  className="h-11 w-full rounded-md border border-line bg-white pl-10 pr-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-emerald-100"
                />
              </span>
            </label>
            <label className="block text-sm font-medium text-ink">
              Senha
              <span className="relative mt-2 block">
                <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={17} aria-hidden="true" />
                <input
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  className="h-11 w-full rounded-md border border-line bg-white pl-10 pr-3 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-emerald-100"
                />
              </span>
            </label>
            {error && <p role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex h-11 w-full items-center justify-center gap-2 rounded-md bg-accent px-4 text-sm font-semibold text-white transition hover:bg-accentdark disabled:cursor-wait disabled:opacity-70"
            >
              {isSubmitting ? "Entrando..." : "Entrar no workspace"}
              <ArrowRight size={17} aria-hidden="true" />
            </button>
          </form>
          <p className="mt-7 text-xs leading-5 text-slate-500">Conta demo preenchida: analyst@datatalk.ai</p>
        </div>
      </section>
    </main>
  );
}
