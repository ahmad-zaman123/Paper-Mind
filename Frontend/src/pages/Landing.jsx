import { Link } from "react-router-dom";

import Brand from "../components/Brand.jsx";
import Exchange from "../components/Exchange.jsx";

// A synthetic example, labelled as such on the page.
const EXAMPLE = {
  question: "Which models does it use?",
  content:
    "It embeds each passage with gemini-embedding-001 [1] and writes the answer with gemini-2.5-flash, grounded only in your document [2].",
  citations: [
    {
      page: 1,
      score: 0.89,
      content:
        "Each document is split into overlapping passages. Every passage is embedded with gemini-embedding-001 and stored as a vector for similarity search.",
    },
    {
      page: 2,
      score: 0.84,
      content:
        "Answers are generated with gemini-2.5-flash from the retrieved passages only. If the document does not contain the answer, the assistant says so.",
    },
  ],
};

export default function Landing() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <Brand />
        <Link to="/login" className="link-btn">
          Sign in
        </Link>
      </header>

      <main className="landing-main">
        <div>
          <h1 className="landing-title">Chat with your documents.</h1>
          <p className="landing-lede">
            Upload a PDF, ask questions in plain English, and get answers grounded in the document,
            with citations back to the exact passages.
          </p>
          <div className="landing-cta">
            <Link to="/login" state={{ register: true }} className="btn primary">
              Get started — it&apos;s free
            </Link>
            <Link to="/login" state={{ demo: true }} className="btn outline">
              Try the live demo
            </Link>
          </div>

          <dl className="landing-steps">
            <div>
              <dt>Upload</dt>
              <dd>PDF, Word, text or Markdown, up to 10 MB.</dd>
            </div>
            <div>
              <dt>Ask</dt>
              <dd>In plain English. Follow-up questions remember the conversation.</dd>
            </div>
            <div>
              <dt>Check</dt>
              <dd>Every answer cites the passages it used, with page and match score.</dd>
            </div>
          </dl>
        </div>

        <figure className="specimen" style={{ margin: 0 }}>
          <div className="specimen-file">
            <span>about-paper-mind.pdf</span>
            <span>Example</span>
          </div>
          <Exchange {...EXAMPLE} />
          <figcaption className="specimen-caption">
            An example answer. The numbered keys point to the passages in the margin.
          </figcaption>
        </figure>
      </main>
    </div>
  );
}
