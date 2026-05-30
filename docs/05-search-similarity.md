# Search & Similarity

Document search (local + online), LDA-based topic similarity, and standalone model training.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/search/documents` | No | Hybrid search: local corpus + optional online |
| GET | `/api/search/online` | No | Online-only search |
| POST | `/api/search/crawl-url` | Yes | Extract content from a single URL |
| POST | `/api/search/add-online` | Yes | Search online and add results to collection |
| POST | `/api/search/train` | Yes | Train LDA on provided or loaded documents |
| GET | `/api/search/similar/{doc_id}` | No | Find documents similar to a given doc |
| GET | `/api/search/topics` | No | Document-topic distribution for current model |
| GET | `/api/search/model-status` | No | LDA model readiness check |

---

## Document Search

**GET /api/search/documents**

| Query param | Default | Description |
|------------|---------|-------------|
| `query` | required | Search string |
| `online` | `true` | Include online results (Google Books, Wikipedia) |
| `top_k` | `10` | Max results |
| `threshold` | `0.3` | Minimum similarity score (0–1) |

**Response:**
```json
{
  "success": true,
  "data": {
    "best_match": { "title": "...", "content": "...", "category": "...", "author": "..." },
    "similar_documents": [
      { "document": { ... }, "similarity_score": 0.72, "dominant_topic": { "topic_id": 2, ... } }
    ],
    "online_documents": [ { "title": "...", "source": "google_books", "url": "..." } ],
    "online_count": 5,
    "online_local_matches": [ ... ]
  }
}
```

`online_local_matches` lists online results whose title matches a document already loaded in the current project.

**Search requires a model to be loaded.** If none is loaded, the service auto-loads the most recently created project.

---

## Online-Only Search

**GET /api/search/online?query=bisnis+digital&max_results=10**

Returns results from external sources only (no local corpus lookup). No model required.

---

## Crawl a Specific URL

**POST /api/search/crawl-url**

```json
{ "url": "https://www.detik.com/artikel-contoh" }
```

**Success:**
```json
{ "success": true, "data": { "title": "...", "content": "...", "author": "...", "url": "..." } }
```

**Error:** `"Failed to crawl URL or extract content"` — timeout, HTTP error, or no extractable content.

---

## Train LDA (from Admin / Search Mode)

**POST /api/search/train**

Used by the admin page's "Auto mode" — trains LDA on documents from the loaded project or a provided array.

```json
{
  "num_topics": 5,
  "project_name": "my_project",
  "project_description": "Optional description",
  "source_urls": ["https://..."],
  "documents": [
    { "title": "...", "content": "...", "url": "..." }
  ]
}
```

| Source | Priority | Used when |
|--------|----------|-----------|
| `documents` array in body | 1st | Crawl results passed directly |
| `lda_service.current_project_documents` | 2nd | Project model loaded (re-train) |
| Nothing | — | Returns error: not enough docs |

**Constraint:** `len(documents) >= num_topics`

**Success:**
```json
{
  "success": true,
  "data": {
    "num_documents": 25,
    "dictionary_size": 430,
    "num_topics": 5,
    "coherence_score": 0.412,
    "topics": [ ... ],
    "model_path": "data/results/my_project/lda_model",
    "project_id": 3
  }
}
```

If `project_name` is given, the project and its documents are persisted to MySQL (upsert by name).

---

## Find Similar Documents

**GET /api/search/similar/{doc_id}?top_k=10&threshold=0.3**

Compares the topic distribution of document `doc_id` against all documents in the currently loaded project's corpus using cosine similarity.

```json
{
  "success": true,
  "data": {
    "doc_id": 5,
    "similar_documents": [
      { "doc_id": 12, "title": "...", "similarity_score": 0.85, "dominant_topic": 2 }
    ],
    "count": 3
  }
}
```

Requires model + corpus loaded. Returns empty list if no documents exceed `threshold`.

---

## Document-Topic Distribution

**GET /api/search/topics**

Returns the topic assignment for every document in the current corpus.

```json
{
  "success": true,
  "data": {
    "document_topics": [
      { "doc_id": 0, "dominant_topic": 2, "dominant_prob": 0.62, "all_topics": [[0, 0.12], [2, 0.62], ...] }
    ],
    "topics": [ { "id": 0, "words": [["bisnis", 0.08], ...] } ],
    "num_documents": 25,
    "coherence": 0.412
  }
}
```

**Auto-load behavior:** If no model is loaded, the most recently created project is loaded automatically.

**Corpus rebuild:** If the corpus is not on disk but the project's documents are available, the corpus is rebuilt in-memory on demand.

**Error responses:**
```json
{ "success": false, "message": "LDA model not trained yet. No projects available" }
{ "success": false, "message": "Cannot rebuild corpus: no documents or dictionary available" }
{ "success": false, "message": "Model corpus not available and no project documents to rebuild from. Please retrain the project." }
```

---

## Model Status

**GET /api/search/model-status**

```json
{
  "success": true,
  "data": {
    "model_trained": true,
    "document_count": 39,
    "num_topics": 5,
    "dictionary_size": 430,
    "current_project_id": 4
  }
}
```

If not trained, auto-loads the most recent project. Returns `model_trained: false` with zeroed stats if no project exists.

---

## Numpy Serialization

LDA inference returns `numpy` types by default. All search endpoints pass data through `convert_numpy_types()` before returning, converting `np.integer` → `int`, `np.floating` → `float`, `np.ndarray` → `list`.

---

## Frontend

The `/admin` page drives most of these features:

- **Search box** → `GET /api/search/documents`
- **🌐 Add Online Results** → `POST /api/search/add-online`
- **🧠 Train LDA Model** (Auto mode) → `POST /api/search/train`
- **🧠 Train LDA Model** (Manual mode) → same endpoint with `documents` from crawl results stored in `sessionStorage`

The `/visualization` page uses `GET /api/search/topics` to display document-topic assignments alongside the pyLDAvis chart.
