# LDA Topic Modeling — Berita Bisnis Indonesia

Aplikasi web untuk analisis topik otomatis pada berita bisnis berbahasa Indonesia menggunakan **Latent Dirichlet Allocation (LDA)**. Mengimplementasikan pipeline KDD lengkap: crawl URL → preprocessing teks Indonesia → transformasi BoW → training LDA → visualisasi interaktif.

**Stack:** FastAPI · SQLAlchemy (MySQL) · Gensim · Sastrawi · pyLDAvis · Vanilla JS

---

## Prasyarat

- Python 3.12+
- MySQL server (eksternal) dengan schema yang sudah dibuat
- Docker + Docker Compose (opsional)

---

## Setup

### 1. Konfigurasi Database

Buat schema MySQL dan user:

```sql
CREATE DATABASE lda_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lda_user'@'%' IDENTIFIED BY 'password_anda';
GRANT ALL PRIVILEGES ON lda_app.* TO 'lda_user'@'%';
```

### 2. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=lda_user
MYSQL_PASSWORD=password_anda
MYSQL_DATABASE=lda_app

SECRET_KEY=ganti-dengan-secret-key-aman
JWT_SECRET_KEY=ganti-dengan-jwt-secret-aman
```

### 3. Jalankan Aplikasi

**Docker (direkomendasikan):**

```bash
docker-compose up -d
```

**Lokal:**

```bash
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"
uvicorn app:app --host 0.0.0.0 --port 3030 --reload
```

Tabel MySQL dibuat otomatis saat server pertama kali dijalankan.

### 4. Migrasi Data Lama (opsional)

Jika ada data dari versi sebelumnya (JSON/SQLite):

```bash
python scripts/migrate_json_to_mysql.py
```

---

## URL

| URL | Keterangan |
|-----|-----------|
| `http://localhost:3030` | Aplikasi |
| `http://localhost:3030/docs` | Swagger UI (API docs) |
| `http://localhost:3030/api/health` | Health check |

---

## Penggunaan

### Registrasi & Login

1. Buka `http://localhost:3030/register` → buat akun
2. Login di `http://localhost:3030/login`

### Analisis via Upload File TXT (KDD Pipeline)

1. Buka `/admin` → pilih mode **Upload File TXT**
2. Siapkan file `.txt` berisi daftar URL berita (satu URL per baris):
   ```
   https://www.detik.com/berita-1
   https://www.kompas.com/berita-2
   ```
3. Masukkan nama project dan jumlah topik
4. Klik **Upload & Crawling** — sistem crawl semua URL
5. Klik **Train LDA Model** — jalankan preprocessing + training
6. Buka `/visualization` untuk melihat hasil interaktif

### Input Dokumen Manual

1. Buka `/manual-input`
2. Pilih project yang sudah ada atau buat baru
3. Tambah dokumen satu per satu lewat form, atau paste teks langsung
4. Klik **Simpan Semua** untuk menyimpan ke database

### Manajemen Project

- `/projects` — lihat semua project, dokumen per project, hapus project
- `/admin` → section **Project Management** — load model ke memori untuk search & visualisasi

### Visualisasi

1. Buka `/visualization`
2. Pilih project dari dropdown
3. Eksplorasi peta topik interaktif (pyLDAvis):
   - Ukuran lingkaran = frekuensi topik dalam corpus
   - Jarak antar lingkaran = ketidakmiripan semantik
   - Slider λ = keseimbangan antara frekuensi term vs eksklusivitas topik

---

## Konfigurasi LDA

Edit di `config.py` atau set via environment variable:

| Parameter | Default | Keterangan |
|-----------|---------|-----------|
| `NUM_TOPICS` | 5 | Jumlah topik |
| `NUM_WORDS_PER_TOPIC` | 10 | Kata per topik ditampilkan |
| `PASSES` | 15 | Iterasi training |
| `ITERATIONS` | 100 | Gibbs sampling per pass |

---

## Utilitas

```bash
# Re-crawl ulang URL sumber sebuah project (ganti dokumen lama)
python scripts/recrawl_project.py <project_id>
```

---

## Dokumentasi Fitur

Lihat folder [`docs/`](docs/README.md) untuk dokumentasi lengkap per fitur:

- [Authentication](docs/01-authentication.md)
- [KDD Pipeline](docs/02-kdd-pipeline.md)
- [Project Management](docs/03-project-management.md)
- [Document Management](docs/04-document-management.md)
- [Search & Similarity](docs/05-search-similarity.md)
- [Visualization](docs/06-visualization.md)
- [Indonesian NLP](docs/07-indonesian-nlp.md)
