import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api.js";

function Citations({ items }) {
  const [open, setOpen] = useState(null);
  if (!items || items.length === 0) return null;
  return (
    <div className="citations">
      {items.map((c, i) => (
        <div key={i} className="citation">
          <button
            className={"cite-chip" + (open === i ? " active" : "")}
            onClick={() => setOpen(open === i ? null : i)}
            title={"Similarity " + c.score}
          >
            [{i + 1}] · {Math.round(c.score * 100)}%
          </button>
          {open === i && <div className="cite-body">{c.content}</div>}
        </div>
      ))}
    </div>
  );
}

function Bubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={"bubble-row " + (isUser ? "from-user" : "from-assistant")}>
      <div className="bubble">
        <div className="bubble-text">{message.content}</div>
        {!isUser && <Citations items={message.citations} />}
      </div>
    </div>
  );
}

export default function Chat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const [conversation, setConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState("");

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

  async function send(event) {
    event.preventDefault();
    const text = question.trim();
    if (!text || thinking) return;
    setQuestion("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: text, id: "temp-" + Date.now() }]);
    setThinking(true);
    try {
      const assistant = await api.ask(conversationId, text);
      setMessages((prev) => [...prev, assistant]);
    } catch (err) {
      setError(err.message);
    } finally {
      setThinking(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="link-btn">
          ‹ Back
        </Link>
        <div className="chat-title">
          {conversation ? conversation.document_title : "Loading…"}
        </div>
        <span />
      </header>

      <div className="chat-scroll" ref={scrollRef}>
        <div className="chat-inner">
          {messages.length === 0 && !thinking && (
            <p className="muted center">Ask anything about this document.</p>
          )}
          {messages.map((m) => (
            <Bubble key={m.id} message={m} />
          ))}
          {thinking && (
            <div className="bubble-row from-assistant">
              <div className="bubble thinking">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
              </div>
            </div>
          )}
        </div>
      </div>

      {error && <div className="error-banner chat-error">{error}</div>}

      <form className="composer" onSubmit={send}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about this document…"
        />
        <button className="btn primary" type="submit" disabled={thinking || !question.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
