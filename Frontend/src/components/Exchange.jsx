import { useId, useState } from "react";

const MARKER = /(\[\d+\])/g;

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The answer text with each [n] marker turned into a key that points at its margin note. */
function AnswerText({ text, citations, activeKey, onKey }) {
  const parts = String(text || "").split(MARKER);
  return (
    <p className="answer">
      {parts.map((part, i) => {
        const match = /^\[(\d+)\]$/.exec(part);
        const n = match ? Number(match[1]) : 0;
        if (n >= 1 && n <= citations.length) {
          return (
            <button
              key={i}
              type="button"
              className={"key" + (activeKey === n ? " is-active" : "")}
              onClick={() => onKey(n)}
              aria-label={"Source " + n}
              aria-pressed={activeKey === n}
            >
              {n}
            </button>
          );
        }
        return part;
      })}
    </p>
  );
}

function Note({ id, n, citation, active, open, onToggle }) {
  const hasPage = citation.page !== null && citation.page !== undefined && citation.page !== "";
  return (
    <article id={id} className={"note" + (active ? " is-active" : "") + (open ? " is-open" : "")}>
      <div className="note-head">
        <span className="note-key">{n}</span>
        {hasPage && <span className="note-meta">p. {citation.page}</span>}
        {typeof citation.score === "number" && (
          <span className="note-match" title={"Similarity " + citation.score}>
            {Math.round(citation.score * 100)}% match
          </span>
        )}
      </div>
      <p className="note-text">{citation.content}</p>
      {String(citation.content || "").length > 220 && (
        <button type="button" className="note-toggle" onClick={onToggle} aria-expanded={open}>
          {open ? "Show less" : "Show full passage"}
        </button>
      )}
    </article>
  );
}

/**
 * One question and its answer, set as a page of an annotated edition: the answer on the left,
 * a bracket in the rail, and the passages it stands on in the margin.
 */
export default function Exchange({ question, content, citations = [] }) {
  const uid = useId();
  const [activeKey, setActiveKey] = useState(null);
  const [openNotes, setOpenNotes] = useState({});
  const hasNotes = citations.length > 0;

  function onKey(n) {
    const next = activeKey === n ? null : n;
    setActiveKey(next);
    if (next !== null) {
      setOpenNotes((prev) => ({ ...prev, [n]: true }));
      const el = document.getElementById(uid + "-note-" + n);
      el?.scrollIntoView({ block: "nearest", behavior: reducedMotion() ? "auto" : "smooth" });
    }
  }

  return (
    <section className={"exchange" + (hasNotes ? "" : " no-notes")}>
      <div className="exchange-main">
        {question && <h3 className="question">{question}</h3>}
        <AnswerText text={content} citations={citations} activeKey={activeKey} onKey={onKey} />
      </div>
      <div className="exchange-rail" aria-hidden="true" />
      {hasNotes && (
        <aside className="exchange-margin" aria-label="Sources for this answer">
          {citations.map((c, i) => (
            <Note
              key={i}
              id={uid + "-note-" + (i + 1)}
              n={i + 1}
              citation={c}
              active={activeKey === i + 1}
              open={Boolean(openNotes[i + 1])}
              onToggle={() => setOpenNotes((prev) => ({ ...prev, [i + 1]: !prev[i + 1] }))}
            />
          ))}
        </aside>
      )}
    </section>
  );
}
