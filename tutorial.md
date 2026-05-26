# Tutorial — Incident Management System (IMS)

Panduan praktis untuk menjalankan simulasi, menghapus data, membuat insiden baru, dan memahami angka di Dashboard.

---

## Daftar isi

1. [Menjalankan & mensimulasikan project](#1-menjalankan--mensimulasikan-project)
2. [Menghapus / mereset data](#2-menghapus--mereset-data)
3. [Cara membuat masalah (insiden)](#3-cara-membuat-masalah-insiden)
4. [Skenario demo lanjutan](#4-skenario-demo-lanjutan)
5. [Memahami Dashboard: Active, Open, Ack, Investigating](#5-memahami-dashboard-active-open-ack-investigating)
6. [Kenapa Active + Resolved ≠ Total?](#6-kenapa-angka-active--resolved-tidak-sama-dengan-total)
7. [Kenapa "Open" kosong tapi Dashboard "Active" besar?](#7-kenapa-open-kosong-tapi-dashboard-active-besar)

---

## 1. Menjalankan & mensimulasikan project

### Prasyarat

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) sudah terpasang dan berjalan
- Port bebas: `5432`, `6379`, `8000`, `3001`

### Langkah 1 — Siapkan environment

Di folder root proyek (`e:\InaAi Competetion`), pastikan file `.env` ada. Isi opsional `GEMINI_API_KEY` jika ingin mencoba fitur AI Analytics / Post-Mortem.

### Langkah 2 — Jalankan semua service

```powershell
cd "e:\InaAi Competetion"
docker compose up -d --build
```

Tunggu hingga semua container sehat:

| Service   | URL / Port                          |
|-----------|-------------------------------------|
| Frontend  | http://localhost:3001               |
| Backend   | http://localhost:8000               |
| Swagger   | http://localhost:8000/docs          |
| PostgreSQL| localhost:5432                      |
| Redis     | localhost:6379                      |

Cek status:

```powershell
docker compose ps
```

### Langkah 3 — Seed data (simulasi riwayat insiden)

Script seed mengisi **6 user on-call** dan **100 insiden historis** dengan status bervariasi (open, acknowledged, investigating, resolved, closed).

```powershell
docker compose exec backend python -m seed.seed_data
```

Output yang diharapkan:

```
✅ Seeded 6 users
✅ Seeded 100 historical incidents
✅ Database seeding complete!
```

### Langkah 4 — Login & mulai simulasi di UI

1. Buka http://localhost:3001
2. Login dengan akun demo (password semua: `password123`):

| Nama          | Email               | Peran    |
|---------------|---------------------|----------|
| Alice Chen    | alice@company.com   | Engineer |
| Bob Raharjo   | bob@company.com     | Engineer |
| Diana Putri   | diana@company.com   | Lead     |
| Fiona Hartono | fiona@company.com   | Manager  |

3. Buka **Dashboard** (`/`) — lihat kartu statistik dan daftar insiden terbaru
4. Buka **Incidents** (`/incidents`) — filter, cari, dan buat insiden baru

### Langkah 5 — Simulasi real-time (WebSocket)

Ini mensimulasikan alur **detection → notifikasi ke engineer lain**:

1. Buka browser biasa → login sebagai **Alice**
2. Buka jendela **Incognito** → login sebagai **Diana**
3. Di browser Alice: **Incidents** → **+ Create Incident** (severity P1/P2 lebih dramatis)
4. Di browser Diana: perhatikan **ikon notifikasi** di navbar — alert muncul tanpa refresh halaman

### Langkah 6 — Simulasi via API (Swagger / curl)

Berguna jika ingin mensimulasikan **monitoring alert** tanpa UI.

**Swagger:** http://localhost:8000/docs

1. `POST /api/auth/login` dengan body:
   ```json
   { "email": "alice@company.com", "password": "password123" }
   ```
2. Salin `access_token`
3. Klik **Authorize** → masukkan: `Bearer <token>`
4. `POST /api/incidents/` untuk membuat insiden baru

**PowerShell (contoh):**

```powershell
# Login
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method POST -ContentType "application/json" -Body '{"email":"alice@company.com","password":"password123"}'
$token = $login.access_token

# Buat insiden (simulasi alert monitoring)
$headers = @{ Authorization = "Bearer $token" }
$body = @{
  title = "API latency spike on /checkout"
  description = "p99 latency > 8s, error rate 12%"
  severity = "P1"
  source = "monitoring"
  tags = "api,checkout,latency"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/incidents/" -Method POST -Headers $headers -ContentType "application/json" -Body $body
```

### Langkah 7 — Verifikasi dengan unit test

```powershell
docker compose exec backend pytest -v --tb=short
```

Test mencakup race condition (acknowledge lock), event Redis, dan state machine status insiden.

---

## 2. Menghapus / mereset data

Ada beberapa tingkat penghapusan — pilih sesuai kebutuhan.

### Opsi A — Reset database + seed ulang (paling umum)

Seed script **sudah menghapus** data lama sebelum mengisi ulang (`TRUNCATE` pada `users`, `incidents`, `postmortems`).

```powershell
docker compose exec backend python -m seed.seed_data
```

Setelah ini Anda kembali punya 6 user + 100 insiden sample.

### Opsi B — Hapus satu insiden (soft delete)

Di UI belum ada tombol delete; gunakan API:

```powershell
# Ganti {id} dengan ID insiden
Invoke-RestMethod -Uri "http://localhost:8000/api/incidents/{id}" -Method DELETE -Headers @{ Authorization = "Bearer $token" }
```

Insiden tidak hilang dari DB fisik — kolom `is_deleted = true`, sehingga tidak muncul di list/stats.

### Opsi C — Hapus SEMUA data Docker (database + redis persisten)

**Peringatan:** Semua data PostgreSQL dan Redis di volume Docker akan hilang.

```powershell
docker compose down -v
docker compose up -d --build
docker compose exec backend python -m seed.seed_data
```

### Opsi D — Bersihkan cache Redis saja

Jika angka Dashboard terasa “nyangkut” setelah reset manual DB (jarang, tapi bisa terjadi):

```powershell
docker compose exec redis redis-cli -n 1 FLUSHDB
```

Cache API disimpan di Redis **database 1** (`cache:*`). Pub/Sub dan lock ada di database 0.

Atau restart backend (subscriber + cache direset saat proses baru):

```powershell
docker compose restart backend
```

---

## 3. Cara membuat masalah (insiden)

Dalam sistem ini, “masalah” = **Incident** dengan lifecycle:

```
open → acknowledged → investigating → resolved → closed
```

### Cara 1 — Lewat UI (paling mudah)

1. Login → menu **Incidents**
2. Klik **+ Create Incident**
3. Isi:
   - **Title** — judul singkat (mis. `Redis cluster node down`)
   - **Description** — detail dampak
   - **Severity** — P1 (kritis) sampai P4 (rendah)
   - **Source** — `manual`, `monitoring`, atau `webhook`
   - **Tags** — dipisah koma, mis. `redis,cluster,prod`
4. Submit → status awal selalu **`open`**

### Cara 2 — Lewat Swagger / curl

Lihat [Langkah 6](#langkah-6--simulasi-via-api-swagger--curl) di atas.

### Cara 3 — Setelah insiden dibuat: uji “penanganan masalah”

Buka detail insiden (`/incidents/{id}`):

| Aksi | Efek |
|------|------|
| **Acknowledge** | Klaim insiden (Redis lock — hanya satu engineer yang menang) |
| **Start Investigating** | Status → `investigating` |
| **Resolve** | Isi resolution notes → status `resolved`, SLA timer berhenti |
| **Close** | Status terminal `closed` |

### Severity & SLA (escalation)

| Severity | Timer escalation (dari `.env`) |
|----------|----------------------------------|
| P1 | 300 detik (5 menit) |
| P2 | 900 detik (15 menit) |
| P3 | 1800 detik (30 menit) |
| P4 | 3600 detik (60 menit) |

Untuk demo escalation: buat insiden **P1**, biarkan status **`open`**, jangan acknowledge — setelah timer habis, insiden dinaikkan tier on-call (event `incident.escalated`).

---

## 4. Skenario demo lanjutan

### A. Race condition (dua engineer, satu insiden)

1. Buat insiden baru (status `open`)
2. Buka detail yang sama di **dua browser** (Alice & Bob)
3. Klik **Acknowledge** hampir bersamaan
4. Satu sukses → `acknowledged`; yang lain dapat **409 Conflict** (Redis `SET NX` lock)

### B. Filter insiden di halaman Incidents

- **Filter by Status = open** → hanya insiden `open`
- **Filter by Status = (kosong)** → semua status
- **Search** → cari di judul (tags tidak ikut filter backend saat ini)

### C. AI Post-Mortem & Analytics

1. Resolve sebuah insiden
2. Di halaman detail → **Generate with Gemini** (butuh `GEMINI_API_KEY` di `.env`)
3. Menu **Analytics** — clustering & insight dari Gemini

---

## 5. Memahami Dashboard: Active, Open, Ack, Investigating

Di kartu **Active** pada Dashboard (`/`), Anda akan melihat angka besar (misalnya **25**) dan baris rincian di bawahnya:

```
7 open · 12 ack · 6 investigating
```

Angka-angka itu harus **selalu menjumlah ke total Active**: `7 + 12 + 6 = 25`.

### Apa itu Active?

**Active** = semua insiden yang **belum selesai** (belum `resolved` atau `closed`).

```
Active = open + ack + investigating
```

| Status | Masuk hitungan Active? |
|--------|-------------------------|
| open | Ya |
| acknowledged (ack) | Ya |
| investigating | Ya |
| resolved | Tidak |
| closed | Tidak |

---

### 1. Open

Insiden **baru terdeteksi** dan **belum ada engineer yang meng-claim (acknowledge)**.

| Aspek | Keterangan |
|--------|------------|
| Arti | Masalah sudah tercatat di sistem, belum ada yang bilang “saya yang tangani” |
| Di UI | Tombol **Acknowledge Incident** masih tersedia di halaman detail |
| SLA | Timer escalation (P1–P4) masih berjalan; jika terlalu lama tidak di-acknowledge, insiden bisa dinaikkan ke tier on-call yang lebih tinggi |

**Analogi:** Alarm monitoring berbunyi, belum ada engineer yang mengangkat “tiket” tersebut.

---

### 2. Ack (Acknowledged)

Singkatan dari **Acknowledged** = insiden **sudah diklaim** oleh seorang engineer.

| Aspek | Keterangan |
|--------|------------|
| Arti | Ada penanggung jawab; insiden tidak lagi “mengambang” tanpa owner |
| Di sistem | Status berubah `open` → `acknowledged` (menggunakan Redis lock agar hanya satu engineer yang berhasil claim) |
| Langkah berikutnya | Mulai investigasi atau langsung perbaikan |
| Timer escalation | Biasanya dihentikan setelah acknowledge |

**Analogi:** Engineer sudah menjawab: “Saya yang handle insiden ini.”

---

### 3. Investigating

Insiden **sedang diselidiki** — engineer sudah acknowledge dan sedang mencari akar masalah.

| Aspek | Keterangan |
|--------|------------|
| Arti | Tim sedang menganalisis (log, metrics, deploy terakhir, dll.) |
| Transisi | Dari `acknowledged` → `investigating` |
| Langkah berikutnya | Setelah solusi ditemukan → **Resolve** (wajib isi resolution notes) |

**Analogi:** Engineer sudah masuk ke sistem dan sedang debug; insiden belum dinyatakan selesai.

---

### Alur status lengkap (lifecycle)

```
open  →  acknowledged  →  investigating  →  resolved  →  closed
```

Setiap insiden baru dari tombol **Create Incident** atau API selalu dimulai dengan status **`open`**.

State machine di backend (`backend/app/models/incident.py`) membatasi transisi yang diizinkan — misalnya insiden `resolved` tidak bisa kembali ke `open`.

---

### Kartu statistik lain di Dashboard

| Kartu | Arti |
|-------|------|
| **Total Incidents** | Semua insiden di database (kecuali yang soft-deleted) |
| **Active** | open + ack + investigating |
| **Resolved** | Insiden sudah diperbaiki (`resolved`), belum ditutup formal |
| **Closed** | Insiden sudah ditutup (`closed`) — status akhir / arsip |
| **Avg MTTR** | Rata-rata waktu dari dibuat hingga resolved (format: `X jam Y menit Z detik`) |

**Rumus total:**

```
Total = Active + Resolved + Closed
100   = 34      + 50       + 16
```

---

### Ringkasan cepat

| Istilah di UI | Arti singkat |
|---------------|--------------|
| **Active** | Masih berjalan — belum resolved/closed |
| **open** | Baru, belum di-claim engineer |
| **ack** | Sudah di-claim, sedang ditangani |
| **investigating** | Sedang diselidiki, belum selesai |
| **resolved** | Sudah diperbaiki — tidak masuk Active |
| **closed** | Sudah ditutup (arsip) — tidak masuk Active |

---

## 6. Kenapa angka Active + Resolved tidak sama dengan Total?

Dashboard menampilkan lima kartu. Yang sering membingungkan: **Total ≠ Active + Resolved** karena ada status **`closed`** (kartu **Closed**).

```
Total = Active + Resolved + Closed
```

Contoh: `100 = 34 + 50 + 16` — angka **16** adalah insiden **closed**, bukan data hilang.

---

## 7. Kenapa "Open" kosong tapi Dashboard "Active" besar?

Ini **bukan bug** — filter dan kartu Dashboard memakai definisi **berbeda**. Lihat juga [bagian 5](#5-memahami-dashboard-active-open-ack-investigating).

### Contoh angka

| Metrik | Nilai contoh |
|--------|----------------|
| Dashboard **Active** | **25** |
| Rincian: **open** | **7** |
| Rincian: **ack** | **12** |
| Rincian: **investigating** | **6** |

Jika **open = 0** tetapi **Active = 18**, artinya `0 + 10 ack + 8 investigating = 18` — tidak ada insiden yang menunggu claim pertama, tetapi masih ada 18 insiden yang belum selesai.

### Kenapa filter "Open" di halaman Incidents kosong?

Halaman **Incidents** dengan filter **Status = open** hanya menampilkan insiden `status = 'open'`.

Jika semua insiden aktif sudah di-acknowledge, filter **open** kosong — padahal kartu **Active** di Dashboard tetap menampilkan angka besar (ack + investigating).

**Solusi:** Kosongkan filter status, atau pilih **acknowledged** / **investigating**.

### Distribusi status dari seed (100 insiden)

Script seed (`backend/seed/seed_data.py`) membagikan status secara acak:

| Status | Perkiraan % |
|--------|-------------|
| resolved | ~60% |
| closed | ~15% |
| acknowledged | ~10% |
| investigating | ~8% |
| **open** | **~7%** |

### Cara memastikan angka di Dashboard

1. Baca baris kecil di kartu Active: `X open · Y ack · Z investigating`
2. Di **Incidents**, gunakan filter **All Statuses** untuk melihat insiden acknowledged/investigating
3. Via API (setelah login):

   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/api/incidents/stats" -Headers @{ Authorization = "Bearer $token" }
   ```

   Contoh respons `by_status`:

   ```json
   {
     "by_status": {
       "open": 7,
       "acknowledged": 12,
       "investigating": 6,
       "resolved": 62,
       "closed": 14
     }
   }
   ```

---

## Troubleshooting cepat

| Gejala | Solusi |
|--------|--------|
| Frontend tidak bisa login | Pastikan `docker compose ps` — backend harus `Up` |
| Seed gagal | `docker compose logs backend` — pastikan postgres healthy |
| Angka dashboard aneh setelah reset DB | `docker compose exec redis redis-cli -n 1 FLUSHDB` lalu refresh |
| Gemini error | Isi `GEMINI_API_KEY` di `.env`, restart backend |
| Port bentrok | Ubah port di `docker-compose.yml` atau matikan service yang memakai port yang sama |

---

## Referensi file penting

| File | Fungsi |
|------|--------|
| `docker-compose.yml` | Orkestrasi postgres, redis, backend, frontend |
| `backend/seed/seed_data.py` | Reset + isi data demo |
| `frontend/src/app/page.tsx` | Perhitungan kartu Active di Dashboard |
| `backend/app/services/incident_service.py` | `get_stats()` — agregasi per status |
| `backend/app/models/incident.py` | State machine status insiden |
| `README.md` | Dokumentasi arsitektur & demo resmi |

---

*Tutorial ini untuk INaAI Competition 2026 — Incident Management System.*
