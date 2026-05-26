# 🛠️ Tech Stack & Versi — Incident Management System

**INaAI Competition 2026 · Full-stack Developer Track**

---

## Detected System Environment

| Tool | Versi Terdeteksi |
|---|---|
| Python | 3.12.0 |
| Node.js | v20.12.0 |
| npm | 10.5.0 |
| pip | 25.3 |
| Docker | 28.0.4 |
| Git | 2.47.1 |

---

## Full Tech Stack

### 🖥️ Frontend

| Teknologi | Versi | Fungsi |
|---|---|---|
| **Next.js** | 14.x | React framework dengan SSR, App Router |
| **React** | 18.x | UI library |
| **TypeScript** | 5.x | Static typing untuk JavaScript |
| **TailwindCSS** | 3.4.x | Utility-first CSS framework |
| **Recharts** | 2.x | Charting library untuk analytics |
| **next-auth** / custom JWT | - | Authentication di frontend |

### ⚙️ Backend

| Teknologi | Versi | Fungsi |
|---|---|---|
| **FastAPI** | 0.115.x | Async web framework, auto OpenAPI |
| **Uvicorn** | 0.34.x | ASGI server untuk FastAPI |
| **Pydantic** | 2.x | Data validation & serialization |
| **SQLAlchemy** | 2.x | Async ORM untuk PostgreSQL |
| **Alembic** | 1.14.x | Database schema migration |
| **PyJWT** | 2.x | JWT token encode/decode |
| **Passlib[bcrypt]** | 1.7.x | Password hashing |
| **httpx** | 0.28.x | Async HTTP client (untuk Gemini API) |
| **redis[hiredis]** | 5.x | Redis async client untuk Python |
| **structlog** | 24.x | Structured logging |
| **python-multipart** | 0.x | Form data parsing |

### 🗄️ Database & Infrastructure

| Teknologi | Versi | Fungsi |
|---|---|---|
| **PostgreSQL** | 16 | Primary relational database |
| **Redis** | 7.4 | Cache, distributed lock (SET NX), Pub/Sub event bus |

### 🤖 AI / LLM

| Teknologi | Versi | Fungsi |
|---|---|---|
| **Gemini 2.0 Flash** | API (Google AI Studio) | Post-mortem generator, incident clustering, recurrence prediction |
| **google-generativeai** | 0.8.x | Python SDK untuk Gemini API |

### 🐳 DevOps & CI/CD

| Teknologi | Versi | Fungsi |
|---|---|---|
| **Docker** | 28.0.4 | Containerization setiap service |
| **Docker Compose** | v2 | Orchestrasi multi-container |
| **GitHub Actions** | - | CI/CD pipeline (lint → test → build → deploy) |

### 🧪 Testing

| Teknologi | Versi | Fungsi |
|---|---|---|
| **pytest** | 8.x | Python test framework |
| **pytest-asyncio** | 0.24.x | Async test support |
| **pytest-cov** | 5.x | Coverage reporting |
| **ruff** | 0.8.x | Python linter (extremely fast) |

### 📦 Deploy Target

| Platform | Tier | Fungsi |
|---|---|---|
| **Railway** / **Render** | Free tier | Cloud deployment (Docker-native) |

---

## Arsitektur Service

```
┌──────────────────────────────────────────────────────────┐
│                    4 Microservices                        │
├──────────────┬──────────────┬──────────────┬─────────────┤
│  Incident    │ Notification │  Escalation  │  Analytics  │
│  Service     │  Service     │  Service     │  Service    │
│              │              │              │             │
│ • CRUD       │ • WebSocket  │ • Timer mgmt │ • Gemini AI │
│ • Locking    │ • Push alert │ • Auto-assign│ • Clustering│
│ • Status FSM │ • Broadcast  │ • Escalation │ • Postmortem│
└──────┬───────┴──────┬───────┴──────┬───────┴──────┬──────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                            │
              ┌─────────────┴─────────────┐
              │   Redis Pub/Sub Event Bus  │
              └─────────────┬─────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  PostgreSQL  │   │    Redis     │   │  Gemini 2.0  │
│   16 (DB)    │   │  7.4 (Cache) │   │  Flash (AI)  │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## Event Contracts

| Event | Channel | Trigger |
|---|---|---|
| `incident.created` | `events:incident` | New incident created |
| `incident.acknowledged` | `events:incident` | Engineer acknowledges |
| `incident.resolved` | `events:incident` | Incident resolved |
| `incident.escalated` | `events:incident` | Auto-escalation fired |

---

## Docker Compose Services

| Service | Port | Image |
|---|---|---|
| `backend` | 8000 | Custom (FastAPI + Uvicorn) |
| `frontend` | 3000 | Custom (Next.js) |
| `postgres` | 5432 | postgres:16-alpine |
| `redis` | 6379 | redis:7.4-alpine |

---

> 📌 **Note**: Semua versi di atas adalah versi yang digunakan saat development dimulai (25 Mei 2026). Versi minor/patch bisa berubah saat `pip install` atau `npm install` mengambil latest compatible version.
