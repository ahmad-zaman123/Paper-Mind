import { Link } from "react-router-dom";

function LogoMark() {
  return (
    <span className="logo-mark" aria-hidden="true">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
        <path
          d="M6 3h8l4 4v14H6V3z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M14 3v4h4" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        <path
          d="M9 12h6M9 15.5h6M9 8.5h2"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

export default function Landing() {
  return (
    <div className="landing">
      <div className="landing-glow" aria-hidden="true" />

      <header className="landing-nav">
        <div className="landing-logo">
          <LogoMark />
          <span className="brand">Paper-Mind</span>
        </div>
        <Link to="/login" className="link-btn">
          Sign in
        </Link>
      </header>

      <main className="landing-hero">
        <div className="hero-copy">
          <span className="landing-eyebrow">Retrieval-augmented Q&amp;A</span>
          <h1 className="landing-title">
            Chat with your <span className="grad">documents</span>.
          </h1>
          <p className="landing-lede">
            Upload a PDF, ask questions in plain English, and get answers grounded in the
            document — with citations back to the exact passages.
          </p>
          <div className="landing-cta">
            <Link to="/login" state={{ register: true }} className="btn primary">
              Get started — it&apos;s free
            </Link>
            <Link to="/login" state={{ demo: true }} className="btn outline">
              Try the live demo
            </Link>
          </div>
        </div>

        <div className="hero-preview" aria-hidden="true">
          <div className="preview-card">
            <div className="preview-head">
              <span className="preview-dot" />
              <span className="preview-dot" />
              <span className="preview-dot" />
              <span className="preview-file">research-paper.pdf</span>
            </div>
            <div className="preview-body">
              <div className="bubble-row from-user">
                <div className="bubble">Which models does it use?</div>
              </div>
              <div className="bubble-row from-assistant">
                <div className="bubble">
                  It embeds chunks with <strong>gemini-embedding-001</strong> and writes
                  answers with <strong>gemini-2.5-flash</strong>, grounded only in your
                  document.
                  <span className="preview-cite">About Paper-Mind · p.1 · 0.89</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
