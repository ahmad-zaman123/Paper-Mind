import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, clearTokens } from "../api.js";

function StatusPill({ status }) {
  return <span className={"pill pill-" + status}>{status}</span>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const fileInput = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const [docs, convos] = await Promise.all([api.listDocuments(), api.listConversations()]);
      setDocuments(docs.results || []);
      setConversations(convos.results || []);
    } catch (err) {
      if (err.status === 401) return logout();
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  // Poll while any document is still processing so status flips to ready live.
  useEffect(() => {
    const isProcessing = documents.some((doc) => doc.status === "processing");
    if (!isProcessing) return undefined;
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, [documents]);

  function logout() {
    clearTokens();
    navigate("/login");
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function startChat(documentId) {
    try {
      const conversation = await api.createConversation(documentId);
      navigate("/c/" + conversation.id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeDocument(id) {
    if (!confirm("Delete this document and its chats?")) return;
    try {
      await api.deleteDocument(id);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">DocChat</div>
        <button className="link-btn" onClick={logout}>
          Sign out
        </button>
      </header>

      <main className="dashboard">
        <section className="panel">
          <div className="panel-head">
            <h2>Your documents</h2>
            <label className="btn primary small">
              {uploading ? "Uploading & indexing…" : "Upload"}
              <input
                ref={fileInput}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleUpload}
                disabled={uploading}
                hidden
              />
            </label>
          </div>

          {error && <div className="error-banner">{error}</div>}

          {loading ? (
            <p className="muted">Loading…</p>
          ) : documents.length === 0 ? (
            <p className="muted">No documents yet. Upload a PDF, Word, or text file to begin.</p>
          ) : (
            <ul className="list">
              {documents.map((doc) => (
                <li key={doc.id} className="list-row">
                  <div className="list-main">
                    <span className="list-title">{doc.title}</span>
                    <span className="list-meta">
                      <StatusPill status={doc.status} /> · {doc.chunk_count} chunks · {doc.page_count} pages
                    </span>
                    {doc.status === "failed" && doc.error_message && (
                      <span className="list-error">{doc.error_message}</span>
                    )}
                  </div>
                  <div className="list-actions">
                    <button
                      className="btn primary small"
                      disabled={doc.status !== "ready"}
                      onClick={() => startChat(doc.id)}
                    >
                      Chat
                    </button>
                    <button className="btn ghost small" onClick={() => removeDocument(doc.id)}>
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Recent chats</h2>
          </div>
          {conversations.length === 0 ? (
            <p className="muted">Your conversations will appear here.</p>
          ) : (
            <ul className="list">
              {conversations.map((c) => (
                <li
                  key={c.id}
                  className="list-row clickable"
                  onClick={() => navigate("/c/" + c.id)}
                >
                  <div className="list-main">
                    <span className="list-title">{c.title || "Untitled chat"}</span>
                    <span className="list-meta">
                      {c.document_title} · {c.message_count} messages
                    </span>
                  </div>
                  <span className="chevron">›</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
