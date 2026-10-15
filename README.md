<h1 align="center">📄 Paper-Mind</h1>

<p align="center">
  <b>Chat with your documents.</b><br/>
  Upload a file, ask in plain English, and get answers grounded in it, with citations back to the exact passages.
</p>

<p align="center">
  <a href="https://github.com/ahmad-zaman123/Paper-Mind/actions/workflows/ci.yml"><img src="https://github.com/ahmad-zaman123/Paper-Mind/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://paper-mind-sage.vercel.app"><img src="https://img.shields.io/badge/live-paper--mind--sage.vercel.app-000?logo=vercel&logoColor=white&style=flat-square" alt="Live demo" /></a>
  <img src="https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white&style=flat-square" alt="Django 4.2" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black&style=flat-square" alt="React 18" />
  <img src="https://img.shields.io/badge/pgvector-Postgres-4169E1?logo=postgresql&logoColor=white&style=flat-square" alt="pgvector" />
  <img src="https://img.shields.io/badge/Gemini-2.5%20Flash-8E75B2?logo=googlegemini&logoColor=white&style=flat-square" alt="Gemini" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT license" /></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick start</a> ·
  <a href="#-how-it-works">How it works</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-api">API</a> ·
  <a href="#-deployment--ci">Deployment</a>
</p>

<p align="center">
  <img src="docs/screenshots/chat.png" alt="Paper-Mind answering a question with citations" width="860" />
</p>

---

## 🧭 What is Paper-Mind?

A retrieval-augmented generation (RAG) app for question answering over your own files. It extracts and chunks your document, embeds each chunk, and stores the vectors in Postgres with **pgvector**. When you ask something, it retrieves the closest passages and has **Google Gemini** answer from them only, showing which passages it used.

| 📤 Upload | 💬 Ask | 🔎 Verify |
|---|---|---|
| PDF, Word, text or Markdown up to 10 MB, extracted and indexed automatically | Natural-language questions, with follow-ups that remember the conversation | Every answer cites the exact passages and similarity scores behind it |

## 🚀 Quick start

**Prerequisites:** Python 3.11, Node 18+, a [Gemini API key](https://aistudio.google.com) (free tier, from AI Studio, not Vertex AI), and **PostgreSQL with the `pgvector` extension** for question answering (see below).

Run the backend and frontend in two terminals, backend first.

**1. Backend** → `http://127.0.0.1:8009`

```bash
cd Backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # set GEMINI_API_KEY and DATABASE_URL
python manage.py migrate
python manage.py runserver 8009   # the frontend expects port 8009
```

**2. Frontend** → `http://localhost:5173`

```bash
cd Frontend
npm install
cp .env.example .env              # VITE_API_URL=http://127.0.0.1:8009
npm run dev
```

> **Database note.** With no `DATABASE_URL` the backend falls back to SQLite, which is enough to register, sign in and upload. Retrieval uses pgvector's cosine distance, so **asking questions needs PostgreSQL with the `vector` extension**. The quickest local option is Docker:
>
> ```bash
> docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=papermind pgvector/pgvector:pg16
> # DATABASE_URL=postgresql://postgres:postgres@localhost:5432/papermind
> ```
>
> A free [Neon](https://neon.tech) database (pgvector included) works too, using its pooled URL with `?sslmode=require`.

<details>
<summary><b>🔧 Environment variables</b> (<code>Backend/.env</code>)</summary>
<br/>

| Key | Required | Notes |
|---|---|---|
| `GEMINI_API_KEY` | **yes** (for AI) | From [aistudio.google.com](https://aistudio.google.com). |
| `DATABASE_URL` | **yes** (for Q&A) | Postgres with pgvector. Unset falls back to SQLite. |
| `SECRET_KEY` | prod | Django secret key. `.env.example` ships an insecure dev default. |
| `DEBUG` | no | `True` for local dev. |
| `CORS_ALLOWED_ORIGINS` | no | Frontend origins allowed to call the API. Defaults to the local Vite server. |
| `GEMINI_EMBEDDING_MODEL` | no | Defaults to `models/gemini-embedding-001`. |
| `GEMINI_CHAT_MODEL` | no | Defaults to `models/gemini-2.5-flash`. |

Frontend: `VITE_API_URL` points at the backend (default `http://127.0.0.1:8009`).

</details>

<details>
<summary><b>🔑 Demo account</b> (live site)</summary>
<br/>

Sign in with **`demo@paper-mind.app`** / **`demo1234`**. It comes pre-loaded with a document and a chat, so you can ask a question and see a cited answer straight away. The account is shared, so don't upload anything private to it; register your own to try your files.

</details>

## 🧩 How it works

```
 Upload ─▶ extract text ─▶ chunk (800 chars, 100 overlap) ─▶ embed ─▶ pgvector
                                                                         │
 Ask ───▶ embed question ─▶ nearest 5 chunks (cosine) ─▶ prompt Gemini ──┘
                                      │
                                      └─▶ answer + citations (page, passage, score)
```

| Setting | Value |
|---|---|
| Accepted files | `pdf`, `docx`, `txt`, `md` |
| Max upload | 10 MB |
| Chunking | 800 characters, 100 overlap, at most 400 chunks per document |
| Retrieval | Top 5 chunks by cosine distance, HNSW index |
| Embeddings | `gemini-embedding-001`, 768 dimensions |
| Answers | `gemini-2.5-flash`, grounded in the retrieved chunks and prior turns |

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 📤 Upload anything readable
PDF, Word, text and Markdown. Text is extracted, chunked and embedded as part of the upload, and a document ends up ready or failed (with the reason).

### 💬 Grounded answers
Questions are answered from your document's retrieved passages, not from the model's memory.

</td>
<td width="50%" valign="top">

### 🔎 Citations
Each answer links back to the exact passages used, with their page and similarity score.

### 🧵 Conversations
Prior turns are kept, so follow-up questions work.

### 🔒 Private by default
JWT authentication, and each user only sees their own documents.

</td>
</tr>
</table>

## 🔌 API

Interactive Swagger docs at **`/api/docs/`** ([live](https://paper-mind-backend-olive.vercel.app/api/docs/)), JSON schema at `/api/schema/`. Everything needs a JWT except registration and login.

| Area | Endpoints |
|---|---|
| **Auth** | `POST /api/auth/register/`, `/auth/token/`, `/auth/token/refresh/`, `GET /auth/me/` |
| **Documents** | `GET`, `POST /api/documents/`, `GET`, `DELETE /api/documents/<id>/` |
| **Ask a document** | `POST /api/documents/<id>/ask/` |
| **Conversations** | `GET`, `POST /api/conversations/`, `GET`, `DELETE /api/conversations/<id>/` |
| **Ask in a conversation** | `POST /api/conversations/<id>/ask/` |

## 🛠️ Tech stack

| Layer | Tech |
|---|---|
| **Backend** | Django 4.2, Django REST Framework, JWT auth |
| **Vector search** | PostgreSQL + pgvector (Neon in production) |
| **AI** | Google Gemini: `gemini-embedding-001` and `gemini-2.5-flash` |
| **Frontend** | React 18, Vite |
| **Deployment** | Vercel + Neon |

## 🗂️ Project structure

```
Paper-Mind/
├── Backend/
│   ├── apps/
│   │   ├── documents/      upload, extraction, chunking, embeddings, retrieval
│   │   ├── conversations/  chat history and follow-ups
│   │   ├── users/          accounts and JWT
│   │   └── core/           shared models
│   └── config/settings/    base · dev · prod
└── Frontend/
    └── src/pages/          Landing · Login · Dashboard · Chat
```

## ☁️ Deployment & CI

- **Vercel** for the backend (`Backend/api/index.py`) and frontend, with **Neon** Postgres (enable pgvector and use the pooled URL).
- **CI** (`ci.yml`) runs `manage.py check`, a missing-migrations check and the frontend build on every push and pull request.

## 📄 License

[MIT](LICENSE) © 2026 Ahmad Zaman
