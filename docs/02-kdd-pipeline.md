# KDD Pipeline

Implements a 4-stage Knowledge Discovery in Databases workflow: **Crawl → Preprocess → Transform → Mine (LDA)**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/kdd/crawl` | Full pipeline in one shot |
| POST | `/api/kdd/upload-and-crawl` | Stage 1 only: crawl URLs from file |
| POST | `/api/kdd/preprocessing` | Stage 2: preprocess crawled text |
| POST | `/api/kdd/transforming` | Stage 3: build BoW dictionary + corpus |
| POST | `/api/kdd/datamining` | Stage 4: train LDA model |
| GET | `/api/kdd/status` | Current pipeline state and data counts |
| GET | `/api/kdd/results` | Latest LDA results |
| GET | `/api/kdd/pyldavis` | pyLDAvis visualization for current session |
| POST | `/api/kdd/reset` | Reset entire pipeline state |

All write endpoints require authentication.

---

## Full Pipeline (One Shot)

**POST /api/kdd/crawl** runs all 4 stages in sequence and saves results to MySQL.

**Form data** (multipart):

| Field | Type | Required | Notes |
|-------|------|:--------:|-------|
| `project_name` | string | Yes | 1–100 chars |
| `file` | `.txt` file | Yes | UTF-8, one URL per line |
| `num_topics` | int | No | Default: project config → `Config.NUM_TOPICS` |
| `num_words_per_topic` | int | No | Default: project config → `Config.NUM_WORDS_PER_TOPIC` |
| `passes` | int | No | Default: project config → `Config.PASSES` |
| `iterations` | int | No | Default: project config → `Config.ITERATIONS` |
| `eta` | float | No | Default: project config → `Config.ETA` (None = Gensim symmetric prior) |

If a project with `project_name` already exists, its stored LDA config takes precedence over the global defaults (but explicit form values always win).

**Success response:**
```json
{
  "success": true,
  "message": "Proses KDD selesai! 25 berita berhasil dianalisis.",
  "data": {
    "project_name": "my_project",
    "project_id": 3,
    "crawl_stats": { "total_urls": 30, "success_count": 25, "failed_count": 5 },
    "num_topics": 5,
    "topics": [
      { "id": 0, "words": [["bisnis", 0.08], ["pasar", 0.06], ...] },
      ...
    ]
  }
}
```

**Side effects:**
- Gensim model files written to `data/results/{project_name}/`
- MySQL: project row created/updated, documents bulk-inserted, pipeline run recorded.
- If the project name already exists, its documents are replaced (re-crawl overwrites).

---

## Stage-by-Stage Usage

These endpoints exist for reviewing results at each stage independently, but the current `/admin` UI does **not** call them — it always trains via `POST /api/search/train` (see "Training via /api/search/train" below), which runs the same 4 stages internally in one request.

### Stage 1 — Crawl

**POST /api/kdd/upload-and-crawl** (form: `file`)

Returns crawled documents in memory. Delay between requests: 0.5 s.

```json
{
  "success": true,
  "data": {
    "total": 30,
    "success_count": 25,
    "failed_count": 5,
    "source_urls": ["https://..."],
    "documents": [
      { "title": "...", "content": "...", "url": "..." }
    ]
  }
}
```

Pipeline cannot proceed if `success_count == 0`.

### Stage 2 — Preprocessing

**POST /api/kdd/preprocessing** (no body; reads in-memory state from Stage 1)

Indonesian text pipeline applied to each document's `content`:

1. Lowercase
2. Remove URLs, emails, numbers, punctuation
3. NLTK tokenization
4. Indonesian stopword removal (NLTK set + ~45 custom stopwords: pronouns, particles, prepositions, conjunctions)
5. Sastrawi stemming (Indonesian morphological analysis)
6. Filter: keep tokens with length > 2

Returns a sample of token counts per document.

### Stage 3 — Transform

**POST /api/kdd/transforming** (no body)

Builds a Gensim **Dictionary** and **Bag-of-Words corpus**.

- Dictionary filtered: keep words in ≥1 doc, remove words in >95% of docs (applied when dict size > 10)
- Returns `dictionary_size` and `corpus_size`

### Stage 4 — Data Mining (LDA)

**POST /api/kdd/datamining**

```json
{
  "num_topics": 5,
  "num_words_per_topic": 10,
  "passes": 15,
  "iterations": 100,
  "eta": 0.1
}
```

All fields are optional. Global `config.py` values are used as fallback.

**LDA hyperparameters:**

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `num_topics` | `Config.NUM_TOPICS` (5) | Number of latent topics |
| `num_words_per_topic` | `Config.NUM_WORDS_PER_TOPIC` (10) | Top words shown per topic |
| `passes` | `Config.PASSES` (15) | Iterations over corpus |
| `iterations` | `Config.ITERATIONS` (100) | Gibbs sampling steps per pass |
| `eta` | `Config.ETA` (None) | Dirichlet prior pada distribusi word-per-topic; `None` = symmetric (1/num_topics), nilai kecil (e.g. 0.01) → topik lebih sparse, nilai besar (e.g. 0.9) → kata lebih merata antar topik |
| `chunksize` | 100 | Docs per training chunk (fixed) |
| `alpha` | `'auto'` | Document-topic concentration (learned, fixed) |
| `random_state` | 42 | Reproducible training (fixed) |

Returns topics with word distributions and coherence score (C_V method; returns 0.0 on failure).

---

## Pipeline State

`GET /api/kdd/status` returns:

```json
{
  "success": true,
  "project_name": "my_project",
  "status": {
    "crawling": "completed",
    "selection": "completed",
    "preprocessing": "completed",
    "transforming": "completed",
    "datamining": "running"
  },
  "data_count": { "raw": 25, "selected": 25, "preprocessed": 25 },
  "crawl_results": { "success_count": 25, "failed_count": 5 }
}
```

Status values: `pending` | `running` | `completed` | `error`

**Note:** Pipeline state is in-memory (`core/state.py` → `kdd_state_manager`). It resets on server restart. Persistent run history is in the `pipeline_runs` MySQL table.

---

## Training via `/api/search/train`

`POST /api/search/train` (in `routers/search.py`, see [05-search-similarity.md](05-search-similarity.md)) is the entry point actually used by the `/admin` UI for both "Auto" and "Manual upload" modes. It runs the same 4 stages as the one-shot pipeline (preprocess → build dictionary/corpus → train LDA → coherence), but as direct calls into `services/lda_service.py` rather than via the `/api/kdd/*` endpoints above.

While it runs, it reports progress into the same `kdd_state_manager` used by `GET /api/kdd/status`:

1. Resets pipeline state, then immediately marks `crawling` and `selection` as `completed` (documents are already provided/loaded).
2. `preprocessing` → `running` → `completed`
3. `transforming` → `running` → `completed`
4. `datamining` → `running` → `completed` (or `error` if training raises)

This lets the `/admin` page poll `GET /api/kdd/status` during training to drive the 5-step progress indicator, even though training itself happens in a single request.

---

## Error Responses

| Message | Cause |
|---------|-------|
| `"Nama project harus diisi"` | Empty project name in form |
| `"File harus berformat .txt"` | Wrong file extension |
| `"Tidak ada URL valid ditemukan dalam file"` | No parseable URLs in TXT |
| `"Tidak ada konten berhasil di-crawl"` | All crawl attempts failed |
| `"Tahap selection harus diselesaikan terlebih dahulu"` | Stage order violated |
| `"Error: {detail}"` | Unexpected exception in any stage |

---

## Model Persistence (Disk)

After a successful full pipeline, the following files are written under `data/results/{project_name}/`:

```
lda_model_model   – Gensim LDA model weights
lda_model_dict    – Gensim Dictionary
lda_model_mm      – MmCorpus (bag-of-words)
results.json      – Topic words + metadata
documents.json    – Document references
source_urls.txt   – Original input URLs
```

The `data/` directory must be persisted across deployments (Docker volume).

---

## Frontend

The admin page at `/admin` provides two modes:

- **Auto mode** (`🤖 Pencarian Otomatis`): search documents + train via `/api/search/train`
- **Manual mode** (`📄 Upload File TXT`): upload a `.txt` file, crawl via `/api/kdd/upload-and-crawl`, then train via `/api/search/train`

Progress is shown as a 5-step indicator: Crawling → Preprocessing → Transforming → Data Mining → Selesai. When training starts, `startProgressPolling()` (in `admin.html`'s inline script) unhides `#progress-container` and polls `GET /api/kdd/status` every 600ms, toggling `active`/`completed` classes on `#step-*` and appending lines to `#log-output`. `stopProgressPolling()` is called once `/api/search/train` resolves. For small document sets, training can finish faster than the poll interval, so the indicator may jump straight to "completed" without showing intermediate "active" states.
