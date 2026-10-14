import { useId, useState } from "react";

// Matches [1] and also the grouped form models often write: [1, 2] or [1,2,3].
const MARKER = /(\[\d+(?:\s*,\s*\d+)*\])/g;

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The answer text with each [n] marker turned into keys that point at their margin notes. */
function AnswerText({ text, citations, activeKey, onKey }) {
  const parts = String(text || "").split(MARKER);
  return (
    <p className="answer">
      {parts.map((part, i) => {
        if (!part.startsWith("[")) return part;
        const numbers = part
          .slice(1, -1)
          .split(",")
          .map((value) => Number(value.trim()));
        const valid = numbers.filter((n) => n >= 1 && n <= citations.length);
        // Not a citation we know about: leave the text exactly as the model wrote it.
        if (valid.length === 0) return part;
        return valid.map((n) => (
          <button
            key={i + "-" + n}
            type="button"
            className={"key" + (activeKey === n ? " is-active" : "")}
            onClick={() => onKey(n)}
            aria-label={"Source " + n}
            aria-pressed={activeKey === n}
          >
            {n}
          </button>
        ));
      })}
    </p>
  );
}

function Note({ id, n, citation, active, open, onToggle }) {
  // Documents without real pages (text, Markdown) report page 0; that is not a page.
  const hasPage = Number(citation.page) > 0;
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
      <p className="note-text">
        {/^[a-z]/.test(String(citation.content || "").trimStart()) ? "… " : ""}
        {citation.content}
      </p>
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
