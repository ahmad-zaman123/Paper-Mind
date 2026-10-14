import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, clearTokens } from "../api.js";
import Brand from "../components/Brand.jsx";

const STATUS_LABEL = { ready: "Ready", processing: "Indexing", failed: "Failed" };

function Status({ status }) {
  return <span className={"status status-" + status}>{STATUS_LABEL[status] || status}</span>;
}

function keyFor(index) {
  return String.fromCharCode(65 + (index % 26));
}

export default function Dashboard() {
  const navigate = useNavigate();
  const fileInput = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [over, setOver] = useState(false);
  const [confirmId, setConfirmId] = useState(null);
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

  // Poll while any document is still processing so its status flips to ready live.
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

  async function upload(file) {
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
    setConfirmId(null);
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
        <Brand />
        <button className="link-btn" onClick={logout}>
          Sign out
        </button>
      </header>

      <main className="dashboard">
        <section aria-labelledby="library-h">
          <div className="panel-head">
            <h2 id="library-h">Library</h2>
            <span className="count">
              {documents.length} {documents.length === 1 ? "document" : "documents"}
            </span>
          </div>

          <div
            className={"dropzone" + (over ? " is-over" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setOver(false);
              upload(e.dataTransfer.files?.[0]);
            }}
          >
            <p>
              {uploading ? "Uploading and indexing…" : "Drop a file here, or choose one."}
              <small>PDF, Word, text or Markdown, up to 10 MB.</small>
            </p>
            <label className="btn primary small">
              {uploading ? "Please wait" : "Upload"}
              <input
                ref={fileInput}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(e) => upload(e.target.files?.[0])}
                disabled={uploading}
                hidden
              />
            </label>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              {error}
            </div>
          )}

          {loading ? (
            <p className="empty muted">Loading your library…</p>
          ) : documents.length === 0 ? (
            <div className="empty">
              <strong>Nothing here yet.</strong>
              Upload a document and ask it a question. Each answer will point to the passages behind it.
            </div>
          ) : (
            <ul className="index">
              {documents.map((doc, i) => (
                <li key={doc.id} className="index-row">
                  <span className="index-key" aria-hidden="true">
                    {keyFor(i)}
                  </span>
                  <span className="index-title">{doc.title}</span>
                  <div className="index-actions">
                    <button
                      className="btn primary small"
                      disabled={doc.status !== "ready"}
                      onClick={() => startChat(doc.id)}
                    >
                      {doc.status === "processing" ? "Indexing…" : "Ask"}
                    </button>
                    {confirmId === doc.id ? (
                      <>
                        <button className="btn outline small" onClick={() => removeDocument(doc.id)}>
                          Delete document and chats
                        </button>
                        <button className="btn ghost small" onClick={() => setConfirmId(null)}>
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button className="btn ghost small" onClick={() => setConfirmId(doc.id)}>
                        Delete
                      </button>
                    )}
                  </div>
                  <div className="index-meta">
                    <Status status={doc.status} />
                    <span>{doc.page_count} pages</span>
                    <span>{doc.chunk_count} passages</span>
                  </div>
                  {doc.status === "failed" && doc.error_message && (
                    <span className="index-error">{doc.error_message}</span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="chats-h">
          <div className="panel-head">
            <h2 id="chats-h">Conversations</h2>
          </div>
          {conversations.length === 0 ? (
            <p className="empty muted">Your conversations will appear here.</p>
          ) : (
            <ul className="index">
              {conversations.map((c) => (
                <li
                  key={c.id}
                  className="index-row clickable"
                  style={{ gridTemplateColumns: "minmax(0, 1fr)" }}
                  onClick={() => navigate("/c/" + c.id)}
                >
                  <button
                    type="button"
                    className="link-btn index-title"
                    style={{ textAlign: "left", textDecoration: "none" }}
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate("/c/" + c.id);
                    }}
                  >
                    {c.title || "Untitled conversation"}
                  </button>
                  <span className="index-meta" style={{ gridColumn: 1 }}>
                    <span>{c.document_title}</span>
                    <span>{c.message_count} messages</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
