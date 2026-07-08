# Paper-Mind

[![CI](https://github.com/ahmad-zaman123/Paper-Mind/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmad-zaman123/Paper-Mind/actions/workflows/ci.yml)

**🔗 Live demo: [paper-mind-sage.vercel.app](https://paper-mind-sage.vercel.app)**

Chat with your documents. Upload a PDF, ask questions in plain English, and get
answers grounded in the document — with citations back to the exact passages.

Retrieval-augmented generation (RAG) built on Django REST Framework, Postgres +
pgvector for vector search, and Google Gemini for embeddings and answers.

## Features

- **Upload** PDF, Word, or text files — text is extracted, chunked, and embedded automatically
- **Ask** questions in natural language and get answers grounded in your document
- **Citations** — every answer links back to the exact source passages, with similarity scores
- **Conversations** that remember prior turns, so follow-up questions work
- **Private by default** — JWT auth; each user only sees their own documents

## How it works

```
Upload → extract text → chunk → embed each chunk → store vectors in pgvector
Ask → embed question → nearest-neighbour search → build context → Gemini answers with citations
```

## Tech stack

- **Backend:** Django 4.2 + Django REST Framework, JWT auth
- **Vector search:** PostgreSQL + pgvector (Neon in production)
- **AI:** Google Gemini — `gemini-embedding-001` (embeddings) + `gemini-2.5-flash` (answers)
- **Frontend:** React + Vite
- **Deploy:** Vercel + Neon

## API

Interactive Swagger docs at `/api/docs/` —
[live](https://paper-mind-backend-olive.vercel.app/api/docs/). JSON schema at `/api/schema/`.

## Run locally

### Backend

```bash
cd Backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # defaults run on local SQLite; set GEMINI_API_KEY for AI features
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com) (AI Studio, not Vertex AI).

### Frontend

```bash
cd Frontend
npm install
cp .env.example .env          # VITE_API_URL points at the backend (default: local Django)
npm run dev                   # http://localhost:5173
```
