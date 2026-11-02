import { useId, useState } from "react";

// Matches [1] and also the grouped form models often write: [1, 2] or [1,2,3].
const MARKER = /(\[\d+(?:\s*,\s*\d+)*\])/g;

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The citation numbers an answer actually uses, in the order of the margin notes. */
function citedNumbers(text, citations) {
  const used = new Set();
  for (const marker of String(text || "").match(MARKER) || []) {
    for (const value of marker.slice(1, -1).split(",")) used.add(Number(value.trim()));
  }
  return citations.map((_, i) => i + 1).filter((n) => used.has(n));
}

const BULLET = /^\s*[*-]\s+/;

/** Split an answer into paragraphs and bullet lists. The model sometimes writes Markdown despite the prompt. */
function toBlocks(text) {
  const blocks = [];
  for (const line of String(text || "").replace(/\*\*(.+?)\*\*/g, "$1").split("\n")) {
    const last = blocks[blocks.length - 1];
    if (BULLET.test(line)) {
      const item = line.replace(BULLET, "");
      if (last?.items) last.items.push(item);
      else blocks.push({ items: [item] });
    } else if (last && !last.items) {
      last.text += "\n" + line;
    } else if (line.trim()) {
      blocks.push({ text: line });
    }
  }
  return blocks;
}

/** The answer text with each [n] marker turned into keys that point at their margin notes. */
function AnswerText({ text, citations, activeKey, onKey }) {
  const shared = { citations, activeKey, onKey };
  return toBlocks(text).map((block, i) =>
    block.items ? (
      <ul key={i} className="answer answer-list">
        {block.items.map((item, j) => (
          <li key={j}>
            <Marked text={item} {...shared} />
          </li>
        ))}
      </ul>
    ) : (
      <p key={i} className="answer">
        <Marked text={block.text.trimEnd()} {...shared} />
      </p>
    )
  );
}

function Marked({ text, citations, activeKey, onKey }) {
  const parts = text.split(MARKER);
  return (
    <>
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
    </>
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
  // Retrieval always returns its nearest passages; only the ones the answer relies on are its sources.
  const uncited = Boolean(citations[0]?.uncited);
  const cited = uncited ? [1] : citedNumbers(content, citations);
  const hasNotes = cited.length > 0;

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
          {uncited && <p className="note-uncited">This answer didn't cite a passage. Closest passage:</p>}
          {cited.map((n) => (
            <Note
              key={n}
              id={uid + "-note-" + n}
              n={n}
              citation={citations[n - 1]}
              active={activeKey === n}
              open={Boolean(openNotes[n])}
              onToggle={() => setOpenNotes((prev) => ({ ...prev, [n]: !prev[n] }))}
            />
          ))}
        </aside>
      )}
    </section>
  );
}
