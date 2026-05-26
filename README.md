# 🚨 Incident Management System (IMS)

**INaAI Competition 2026 · Full-stack Developer Track · Fase 2**

Incident Management System (IMS) adalah platform berbasis web event-driven untuk mengelola seluruh siklus hidup insiden (Incident Lifecycle) secara real-time: **Detection → Auto-Assignment → Optimistic Locking Acknowledgement → Escalation SLA Timer → AI Post-Mortem Report generation**.

Sistem ini didesain dengan arsitektur 4 microservices di backend yang terhubung via **Redis Pub/Sub Event Bus**, visual dashboard Next.js premium bertema dark-glass, penanganan race conditions dengan Redis distributed lock, dan analisis data insiden menggunakan **Gemini 2.0 Flash AI**.

---

## 🏛️ Arsitektur & Microservices

Sistem backend menggunakan FastAPI dengan model 4 Core Services:

1. **Incident Service (CRUD & Locking)**: Mengelola database insiden, status state machine, dan mengamankan klaim acknowledgement menggunakan Redis distributed locking (`SET NX` key-value lock) untuk mencegah duplikasi klaim oleh beberapa on-call engineers.
2. **Notification Service (WebSocket & real-time)**: Mengelola koneksi WebSocket dua arah terautentikasi JWT dan menyiarkan peringatan langsung ke dasbor web ketika insiden baru dibuat atau status berubah.
3. **Escalation Service (SLA Timer)**: Mengatur timer asyncio untuk melacak SLA insiden berdasarkan tingkat keparahan (P1-P4). Jika insiden tidak di-acknowledge dalam SLA waktu tertentu, sistem otomatis menaikkan tingkat tier on-call (Tier 1 → Tier 2 → Tier 3) dan menugaskan ulang insiden ke tim berwenang.
4. **Analytics Service (AI Engine)**: Menghubungi API Gemini 2.0 Flash untuk secara otomatis mengelompokkan insiden (incident clustering), memprediksi pola berulang (recurrence prediction), dan menyusun draf laporan post-mortem (root cause, dampak bisnis, dan action items) secara otomatis.

---

## 🛠️ Tech Stack & Versi

Laporan lengkap versi dapat diakses di [TECH_STACK.md](file:///e:/InaAi%20Competetion/TECH_STACK.md).

* **Runtime**: Python 3.12.0 (Backend), Node.js v20.12.0 (Frontend)
* **Frontend**: Next.js 14.x (App Router, SSR), TypeScript, TailwindCSS 3.4.x
* **Backend**: FastAPI 0.115.x, Uvicorn, SQLAlchemy 2.x, Pydantic v2
* **Storage & Caching**: PostgreSQL 16, Redis 7.4 (Pub/Sub + Locks + Cache)
* **AI Engine**: Gemini 2.0 Flash API (Google AI Studio)

---

## 🚀 Cara Menjalankan Aplikasi (Local Setup)

Seluruh sistem dikontainerisasi menggunakan Docker Compose. Ikuti langkah-langkah berikut untuk memulai:

### 1. Prasyarat
Pastikan Anda sudah menginstal:
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (dengan Docker Compose)

### 2. Setup Environment Variables
Salin file `.env` di direktori root dan isi **GEMINI_API_KEY** Anda:
```env
# Dapatkan Gemini API Key dari https://aistudio.google.com/
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Jalankan Docker Compose
Jalankan perintah berikut di direktori root proyek untuk membangun image dan mengaktifkan service:
```bash
docker compose up -d --build
```
Perintah ini akan menyalakan 4 kontainer utama:
* **postgres** (Database Relasional) di `localhost:5432`
* **redis** (Cache, Pub/Sub & Locks) di `localhost:6379`
* **backend** (FastAPI) di `http://localhost:8000` (Dokumentasi Swagger OpenAPI di `http://localhost:8000/docs`)
* **frontend** (Next.js) di `http://localhost:3001`

### 4. Melakukan Seed Data Awal
Untuk mengisi database dengan user demo on-call dan 100 riwayat insiden realistis:
```bash
docker compose exec backend python -m seed.seed_data
```

---

## 🔑 Akun Demo On-Call
Berikut adalah akun yang sudah disiapkan melalui seed script (Gunakan password: `password123`):
* **Alice Chen** (Engineer - Tier 1): `alice@company.com`
* **Bob Raharjo** (Engineer - Tier 1): `bob@company.com`
* **Diana Putri** (Lead - Tier 2): `diana@company.com`
* **Fiona Hartono** (Manager - Tier 3): `fiona@company.com`

---

## 🧪 Menjalankan Unit Tests (TDD Verification)

Unit tests backend mencakup pengujian kondisi perlombaan klaim (race conditions), alur event Redis Pub/Sub, dan state machine transisi insiden:

```bash
# Menjalankan seluruh test di kontainer backend
docker compose exec backend pytest -v --tb=short
```

---

## 📺 Demo Alur Utama Fitur Premium

### 1. Real-time Incident Dashboard
* Buka browser di `http://localhost:3001` dan login sebagai **Alice** (`alice@company.com`).
* Buka tab browser lain secara rahasia (incognito) dan login sebagai **Diana** (`diana@company.com`).
* Di salah satu dasbor, buat insiden baru klik tombol **+ Create Incident**.
* Amati bahwa dasbor di tab browser satunya langsung menerima alert pop-up notifikasi secara instan via WebSocket tanpa memuat ulang halaman!

### 2. Race Condition Prevention (Acknowledge Lock)
* Di kedua browser, buka detail insiden bertipe `open` yang sama.
* Klik tombol **Acknowledge Incident** di kedua browser secara hampir bersamaan.
* **Hasil**: Salah satu engineer akan berhasil mengklaim kepemilikan dan status berubah menjadi `acknowledged`. Browser kedua akan memunculkan pesan error `409 Conflict: Incident is locked by another responder`, membuktikan Redis distributed lock `SET NX` bekerja sukses.

### 3. SLA Auto-Escalation
* Buat insiden dengan tingkat keparahan **P1** dan biarkan dalam status `open`.
* Melalui timer asyncio, SLA untuk P1 diatur berdurasi pendek untuk demo lokal (5 menit di konfigurasi real, dapat disesuaikan di `.env`).
* Jika tidak di-acknowledge oleh Engineer Tier 1 hingga batas waktu habis, sistem otomatis meluncurkan event `incident.escalated`, menugaskan ulang insiden ke **Tier 2 on-call (Diana)**, dan menyiarkannya di log panel history.

### 4. AI Post-Mortem & Analytics
* Setelah menangani insiden, isi kolom resolution notes dan klik **Resolve Incident**.
* Setelah insiden terselesaikan, masuk ke bagian **AI-Powered Post-Mortem Report**.
* Klik **Generate with Gemini 2.0 Flash**. AI akan menganalisis detail timeline insiden dan menghasilkan draf laporan post-mortem lengkap (Executive Summary, Root Cause, Business Impact, Action Items, & Lessons Learned).
* Buka tab **AI Analytics** di navigasi kiri untuk melihat analisis klaster pola insiden secara visual dan rekomendasi performa on-call dari AI.
