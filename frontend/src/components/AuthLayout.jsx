import "./AuthLayout.css";

export default function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth-brand">
        <div className="auth-logo">
          <span className="auth-logo-mark" aria-hidden="true">A</span>
          <span className="auth-logo-name">AshRAG</span>
        </div>

        <div className="auth-pitch">
          <p className="eyebrow">Runs on your machine</p>
          <h2>
            Ask your PDFs
            <br />
            real questions.
          </h2>
          <p className="auth-pitch-body">
            Upload a document, ask about it in plain language, and get answers
            drawn from its own pages. Nothing leaves your computer.
          </p>
        </div>

        <p className="auth-brand-foot mono">llama 3.1 · qwen 2.5 · local</p>
      </aside>

      <main className="auth-main">
        <div className="auth-card">
          <header className="auth-header">
            <h1>{title}</h1>
            {subtitle && <p>{subtitle}</p>}
          </header>

          {children}

          {footer && <p className="auth-footer">{footer}</p>}
        </div>
      </main>
    </div>
  );
}