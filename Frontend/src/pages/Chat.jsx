import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, clearTokens } from "../api.js";
import Brand from "../components/Brand.jsx";
import Exchange from "../components/Exchange.jsx";
import ProfileMenu from "../components/ProfileMenu.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";
import { useDocumentTitle } from "../utils/useDocumentTitle.js";

const STARTERS = [
  "Summarise this document in five sentences.",
  "What are the key findings or conclusions?",
  "List the important dates, names and figures.",
];

/** Pair each user message with the assistant reply that follows it. */
function toExchanges(messages) {
  const out = [];
  for (let i = 0; i < messages.length; i += 1) {
    const m = messages[i];
    if (m.role !== "user") {
      out.push({ id: m.id, question: null, reply: m });
      continue;
    }
    const next = messages[i + 1];
    if (next && next.role !== "user") {
      out.push({ id: m.id, question: m.content, reply: next });
      i += 1;
    } else {
      out.push({ id: m.id, question: m.content, reply: null });
    }
  }
  return out;
}

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState(null);
  useDocumentTitle(conversation ? conversation.document_title : "Chat");

  // Who is signed in, for the account menu. A failure here is not worth an error banner.
  const loadUser = () => api.me().then(setUser).catch(() => {});
  useEffect(() => {
    loadUser();
  }, []);

  function logout() {
    clearTokens();
    navigate("/login");
  }

  useEffect(() => {
    api
      .getConversation(conversationId)
      .then((data) => {
        setConversation(data);
        setMessages(data.messages || []);
      })
      .catch((err) => {
        if (err.status === 404) navigate("/");
        else setError(err.message);
      });
  }, [conversationId]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, thinking]);

  // Grow the composer with its content, up to a few lines.
  useEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [question]);

  async function submit(text) {
    const value = text.trim();
    if (!value || thinking) return;
    setQuestion("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: value, id: "temp-" + Date.now() }]);
    setThinking(true);
    try {
      const assistant = await api.ask(conversationId, value);
      setMessages((prev) => [...prev, assistant]);
    } catch (err) {
      // Keep the user's words: put the question back so they can retry, not retype.
      setMessages((prev) => prev.filter((m) => !String(m.id).startsWith("temp-")));
      setQuestion(value);
      setError(err.message || "Something went wrong. Your question is still in the box; try again.");
    } finally {
      setThinking(false);
    }
  }

  function onKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(question);
    }
  }

  const exchanges = toExchanges(messages);
  const empty = exchanges.length === 0 && !thinking;

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="link-btn">
          ‹ Library
        </Link>
        <h1 className="running-head" title={conversation?.document_title || ""}>
          {conversation ? conversation.document_title : "Loading…"}
        </h1>
        <div className="topbar-right">
          <Brand />
          <ThemeToggle />
          <ProfileMenu user={user} onSignOut={logout} changePassword={api.changePassword} onPasswordChanged={loadUser} />
        </div>
      </header>

      <div className="chat-scroll" ref={scrollRef}>
        <div className="sheet">
          {empty && (
            <div className="starter">
              <h2>Ask this document anything.</h2>
              <p>Answers cite the passages they come from, so you can check them against the page.</p>
              <ul className="starter-list">
                {STARTERS.map((s) => (
                  <li key={s}>
                    <button type="button" onClick={() => submit(s)}>
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {exchanges.map((ex) =>
            ex.reply ? (
              <Exchange
                key={ex.id}
                question={ex.question}
                content={ex.reply.content}
                citations={ex.reply.citations || []}
              />
            ) : (
              <section key={ex.id} className="exchange no-notes">
                <div className="exchange-main">
                  <h3 className="question">{ex.question}</h3>
                </div>
              </section>
            )
          )}

          {thinking && (
            <p className="reading" role="status">
              Finding the passages…
            </p>
          )}
        </div>
      </div>

      <div className="composer-bar">
        {error && (
          <div className="error-banner chat-error" role="alert">
            {error}
          </div>
        )}
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            submit(question);
          }}
        >
          <label className="sr-only" htmlFor="question">
            Ask a question about this document
          </label>
          <div className="composer-row">
            <textarea
              id="question"
              ref={inputRef}
              rows={1}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask a question about this document…"
            />
            <button className="btn primary" type="submit" disabled={thinking || !question.trim()}>
              Ask
            </button>
          </div>
          <p className="composer-hint">Enter to ask · Shift+Enter for a new line</p>
        </form>
      </div>
    </div>
  );
}
