# DocChat

Chat with your documents. Upload a PDF, ask questions in plain English, and get
answers grounded in the document — with citations back to the exact passages.

Retrieval-augmented generation (RAG) built on Django REST Framework, Postgres +
pgvector for vector search, and Google Gemini for embeddings and answers.

## Stack

- **Backend:** Django 4.2 + Django REST Framework, JWT auth
- **Vector search:** PostgreSQL + pgvector (Neon in production)
- **AI:** Google Gemini — `text-embedding-004` (embeddings) + `gemini-2.0-flash` (answers)
- **Frontend:** React + Vite *(added in Phase 5)*
- **Deploy:** Vercel + Neon

## How it works

```
Upload PDF → extract text → chunk → embed each chunk → store vectors in pgvector
Ask a question → embed question → nearest-neighbour search → build context → Gemini answers with citations
```

## Local development (Backend)

```bash
cd Backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # defaults run on local SQLite; set GEMINI_API_KEY for AI features
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

- API docs: http://127.0.0.1:8000/api/docs/
- Get a free Gemini key at https://aistudio.google.com (AI Studio, not Vertex AI).

## Local development (Frontend)

```bash
cd Frontend
npm install
cp .env.example .env          # VITE_API_URL points at the backend (default: local Django)
npm run dev                   # http://localhost:5173
```

React + Vite single-page app: email auth, document upload, and a chat view that
renders grounded answers with clickable citation chips. Talks to the backend via
JWT bearer tokens (with automatic access-token refresh).

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create an account |
| POST | `/api/auth/token/` | Obtain JWT access + refresh |
| POST | `/api/auth/token/refresh/` | Refresh the access token |
| GET | `/api/auth/me/` | Current user |
| POST | `/api/documents/` | Upload a document (PDF/DOCX/TXT/MD); chunks + embeds it |
| GET | `/api/documents/` | List your documents with status and chunk count |
| GET | `/api/documents/{id}/` | Document detail with a text preview |
| DELETE | `/api/documents/{id}/` | Delete a document and its chunks |
| POST | `/api/documents/{id}/ask/` | One-shot question; returns a grounded answer with citations |
| POST | `/api/conversations/` | Start a chat over a document |
| GET | `/api/conversations/` | List your conversations |
| GET | `/api/conversations/{id}/` | Conversation with its full message history |
| DELETE | `/api/conversations/{id}/` | Delete a conversation |
| POST | `/api/conversations/{id}/ask/` | Ask within a chat; remembers prior turns, persists messages |

### Asking a question

```http
POST /api/documents/{id}/ask/
{ "question": "How much was the third quarter invoice?" }

200 OK
{
  "answer": "The third quarter invoice was 4200 dollars, due within 30 days [1, 2].",
  "citations": [
    { "chunk_index": 3, "page": 0, "content": "...", "score": 0.80 }
  ]
}
```
