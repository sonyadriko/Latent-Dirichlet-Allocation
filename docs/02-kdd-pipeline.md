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
| `num_topics` | int | No | Default: 5 |

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

Use this flow when you want to review results at each stage before proceeding (visible in the admin UI step-by-step mode).

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
{ "num_topics": 5 }
```

**LDA hyperparameters (from `config.py`):**

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `NUM_TOPICS` | 5 | Number of latent topics |
| `NUM_WORDS_PER_TOPIC` | 10 | Top words shown per topic |
| `PASSES` | 15 | Iterations over corpus |
| `ITERATIONS` | 100 | Gibbs sampling steps per pass |
| `chunksize` | 100 | Docs per training chunk |
| `alpha` | `'auto'` | Document-topic concentration (learned) |
| `random_state` | 42 | Reproducible training |

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
- **Manual mode** (`📄 Upload File TXT`): upload a `.txt` file, crawl, then train

Progress is shown as a 5-step indicator: Crawling → Preprocessing → Transforming → Data Mining → Selesai.
