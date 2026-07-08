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

## API (Phase 0)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create an account |
| POST | `/api/auth/token/` | Obtain JWT access + refresh |
| POST | `/api/auth/token/refresh/` | Refresh the access token |
| GET | `/api/auth/me/` | Current user (authenticated) |
