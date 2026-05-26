# Incident Management System
**INaAI Competition 2026 · Full-stack Developer Track · Fase 1 Proposal**

---

## 1. Problem dan Solusi

**Problem.** Ketika terjadi production incident — server down, error rate melonjak, atau payment timeout — tim engineering sering menghadapi kekacauan koordinasi: siapa yang handle, sudah di-acknowledge belum, kapan harus eskalasi, dan bagaimana mencegah kejadian serupa? Tanpa sistem terpusat, informasi tersebar di Slack, email, dan grup WA, memperpanjang Mean Time to Resolution (MTTR) secara signifikan.

**Solusi.** Platform Incident Management System berbasis web yang mengelola siklus hidup penuh sebuah incident: deteksi → assignment → acknowledgement → resolusi → post-mortem. Sistem dirancang event-driven dengan tiga properti utama:

| Pain Point | Solusi yang Dibangun |
|---|---|
| Dua engineer klaim incident bersamaan | Optimistic locking + atomic compare-and-swap via Redis SET NX |
| Tidak ada yang merespons alert | Escalation Service dengan timer otomatis per-incident |
| Koordinasi tersebar di banyak channel | Dashboard real-time terpusat via WebSocket |
| Post-mortem manual dan lambat | AI auto-generate draft dari timeline incident |
| Tidak ada visibilitas pola incident | Analytics AI: clustering + prediksi recurrence |

---

## 2. Tech Stack

| Layer | Teknologi | Alasan |
|---|---|---|
| Frontend | Next.js 14 + TypeScript + TailwindCSS | SSR, type-safe, ecosystem matang |
| Backend | FastAPI (Python) | Async-native, auto OpenAPI docs, performa tinggi |
| Database | PostgreSQL | ACID transactions untuk locking yang proper |
| Cache & Lock | Redis | Atomic ops (SET NX) untuk distributed lock |
| Event Bus | Redis Pub/Sub | Lightweight, cukup untuk skala kompetisi |
| Real-time | WebSocket (FastAPI native) | Push notifikasi ke browser tanpa polling |
| AI | Gemini 2.0 Flash (Google AI Studio) | Free tier, 1500 req/hari, context window 1M token |
| Container | Docker + Docker Compose | Semua service reproducible dari clean state |
| CI/CD | GitHub Actions | Auto lint → test → build → deploy |
| Deploy | Railway / Render | Free tier cukup, Docker-native |

---

## 3. Architecture Diagram

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Engineer Browser│  │ Alert Simulator │  │ External Monitor│
│ React/Next.js   │  │ REST Trigger    │  │ Webhook         │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
              ┌───────────────────────────────┐
              │     API Gateway + Auth        │
              │  FastAPI · JWT · Rate Limit   │
              └───────┬───────────────────────┘
                      │
        ┌─────────────┼──────────────┬──────────────┐
        ▼             ▼              ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│  Incident    │ │ Notification │ │  Escalation │ │  Analytics   │
│  Service     │ │  Service     │ │  Service    │ │  Service     │
│ CRUD·Locking │ │ WebSocket    │ │ Timer·Assign│ │ AI·Postmortem│
└──────┬───────┘ └──────┬───────┘ └──────┬──────┘ └──────┬───────┘
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                                 │
              ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                    Redis Pub/Sub — Event Bus
              ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  PostgreSQL  │        │    Redis     │        │ Gemini 2.0   │
│  Primary DB  │        │ Cache + Lock │        │  AI/LLM API  │
└──────────────┘        └──────────────┘        └──────────────┘
```

**Event Flow:**
- `incident.created` → Notification Service push alert ke semua engineer
- `incident.acknowledged` → Escalation Service cancel timer
- `incident.resolved` → Analytics Service generate post-mortem via Gemini
- `incident.escalated` → Notification Service push alert ke tier lebih tinggi

**Race Condition Handling:**
Saat dua engineer acknowledge bersamaan, sistem pakai Redis SET NX (atomic). Hanya satu yang berhasil acquire lock. Engineer kedua mendapat respons `409 Conflict: already acknowledged by engineer@email.com`.

---

## 4. Roadmap Fase 2 (21,5 Jam)

| # | Deliverable | Durasi | Kriteria |
|---|---|---|---|
| 1 | Docker Compose + skeleton 4 service + PostgreSQL schema | 2 jam | Must Have |
| 2 | Incident CRUD, status machine, optimistic locking (Redis SET NX) | 2.5 jam | Must Have + Extraordinary |
| 3 | Redis Pub/Sub event bus + event contracts antar service | 1.5 jam | Must Have |
| 4 | Notification Service + WebSocket real-time ke frontend | 1.5 jam | Must Have |
| 5 | Escalation Service dengan configurable timer + auto-assign | 2 jam | Must Have |
| 6 | Frontend dashboard: incident list, detail, acknowledge, resolve | 2.5 jam | Extraordinary |
| 7 | AI Analytics: post-mortem generator + incident clustering via Gemini 2.0 Flash | 2 jam | Extraordinary |
| 8 | GitHub Actions CI/CD + OpenAPI docs + structured logging (structlog) | 1.5 jam | Nice to Have |
| 9 | Redis caching untuk read-heavy endpoint + cache invalidation on event | 1 jam | Nice to Have |
| 10 | TDD: unit test locking logic + event flow ditulis SEBELUM implementasi | 1 jam | Nice to Have |
| – | Buffer: polish UI, seed 100 incident historis, README, demo prep | 4 jam | – |

**Total: 21,5 jam**

---

## Coverage Kriteria Penilaian

### Must Have (semua wajib Pass)
- ✅ Docker — 4 service + PostgreSQL + Redis via Docker Compose
- ✅ Clean Code — boundary service jelas, SOLID principles natural per domain
- ✅ Event-driven architecture — Redis Pub/Sub dengan 4 event type yang terdefinisi
- ✅ Race condition handling — Redis SET NX atomic untuk acknowledge conflict
- ⚠️ AI coding tools — wajib catat AI Usage Log sejak menit pertama coding

### Nice to Have (target semua 5)
- ✅ TDD — locking logic ditulis test-first, dibuktikan via commit history
- ✅ CI/CD — GitHub Actions: lint → test → build → deploy
- ✅ Caching — Redis cache untuk incident list + invalidasi on event
- ✅ API Docs — FastAPI auto-generate OpenAPI di `/docs`
- ✅ Structured logging — structlog dengan field: timestamp, service, level, incident_id

### Extraordinary (target semua 4)
- ✅ Multi-service 3+ — 4 service terpisah secara natural
- ✅ Concurrent locking — demo dua browser acknowledge bersamaan
- ✅ AI analytics — Gemini 2.0 Flash: post-mortem + clustering + insight pola
- ✅ End-to-end smooth flow — simulate → dashboard → acknowledge → resolve → analytics
