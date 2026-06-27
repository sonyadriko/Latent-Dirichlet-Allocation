# Project Management

A **project** is the top-level unit that groups a trained LDA model with its source documents. Every LDA analysis belongs to a project.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/projects/` | No | List all active projects |
| POST | `/api/projects/` | Yes | Create a new project |
| GET | `/api/projects/list` | Yes | Same as `/` — used by admin UI |
| GET | `/api/projects/{id}` | No | Get project by ID |
| GET | `/api/projects/stats/overview` | No | Aggregate statistics |
| POST | `/api/projects/{id}/load` | Yes | Load model into memory |
| PUT | `/api/projects/{id}/lda-config` | Yes | Update per-project LDA parameters |
| POST | `/api/projects/{id}/clone` | Yes | Clone project metadata |
| DELETE | `/api/projects/{id}/delete` | Yes | Delete project + documents + model files |
| DELETE | `/api/projects/{id}/delete-db` | Yes | Alias for `/delete` |
| GET | `/api/projects/{id}/documents` | Yes | List project documents |
| GET | `/api/projects/{id}/pyldavis` | No | pyLDAvis visualization data |

---

## Create Project

**POST /api/projects/**

```json
{
  "name": "Analisis Berita Ekonomi",
  "description": "Berita ekonomi Q2 2024",
  "num_topics": 7,
  "num_words_per_topic": 10,
  "passes": 20,
  "iterations": 200,
  "eta": 0.1
}
```

| Field | Constraint | Default |
|-------|-----------|---------|
| `name` | 2–100 chars, required, globally unique | — |
| `description` | Optional | `""` |
| `num_topics` | Integer 1–50 | 5 |
| `num_words_per_topic` | Integer 1–100 | 10 |
| `passes` | Integer 1–500 | 15 |
| `iterations` | Integer 1–5000 | 100 |
| `eta` | Float 0–1, optional | `null` (Gensim symmetric prior) |

**Success:**
```json
{ "success": true, "data": { "id": 4, "name": "Analisis Berita Ekonomi", "num_topics": 7, "passes": 20, ... } }
```

---

## Update LDA Config

**PUT /api/projects/{id}/lda-config**

Updates only the LDA training parameters for an existing project. Does **not** retrain — the new config takes effect on the next training run.

```json
{
  "num_topics": 8,
  "num_words_per_topic": 15,
  "passes": 30,
  "iterations": 300,
  "eta": 0.05
}
```

`num_topics`, `num_words_per_topic`, `passes`, `iterations` are required. `eta` is optional (omit or `null` to use Gensim default). Constraints same as Create.

**Success:**
```json
{ "success": true, "data": { "id": 4, "num_topics": 8, "passes": 30, ... }, "message": "LDA config updated" }
```

**Error:** `"Project not found"` — ID doesn't exist.

---

## List Projects

**GET /api/projects/**

Returns only active projects (`status = "active"`) ordered by `created_at` descending.

```json
{
  "success": true,
  "data": [
    { "id": 4, "name": "...", "num_topics": 7, "passes": 20, "iterations": 200, "document_count": 39, "coherence_score": 0.412, "status": "active", ... }
  ]
}
```

---

## Load Project Model

**POST /api/projects/{id}/load**

Loads the project's Gensim LDA model from disk into memory so that search, similarity, and visualization features can use it.

**What happens:**
1. Project row fetched from MySQL.
2. Documents fetched (up to 10,000) to rebuild corpus if not on disk.
3. `lda_service.load_project_model(name, id, doc_count, documents)` called.
4. Model files loaded from `data/results/{project_name}/`.

**Note:** Only one project model lives in memory at a time (singleton LDA service). Loading a new project replaces the previous one.

---

## Delete Project

**DELETE /api/projects/{id}/delete**

Permanently removes:
- MySQL rows: project + all documents + pipeline runs (cascade)
- Disk: model folder at `data/results/{project_name}/`

Returns 404 if project not found.

---

## Clone Project

**POST /api/projects/{id}/clone**

```json
{
  "name": "Analisis Berita Ekonomi v2",
  "description": "Optional",
  "num_topics": 7
}
```

Copies metadata only — documents are **not** copied, `document_count` starts at 0. LDA config (`passes`, `iterations`, `num_words_per_topic`) is **not** cloned; new project uses global defaults. The clone must be trained with new documents to produce a functional model.

---

## Project Statistics

**GET /api/projects/stats/overview**

```json
{
  "success": true,
  "data": {
    "total_projects": 4,
    "total_documents": 120,
    "average_coherence": 0.384,
    "total_topics": 23,
    "topic_distribution": { "5": 3, "8": 1 },
    "recent_projects": [ ... ]
  }
}
```

---

## Data Model

```
Project
├── id                  INT PK
├── name                VARCHAR(100) UNIQUE
├── description         TEXT
├── num_topics          INT (default 5)
├── num_words_per_topic INT (default 10)   ← top words shown per topic
├── passes              INT (default 15)   ← LDA training passes
├── iterations          INT (default 100)  ← Gibbs sampling steps per pass
├── eta                 FLOAT NULL         ← Dirichlet prior word-per-topic; NULL = symmetric
├── document_count      INT (denormalized counter, kept in sync)
├── coherence_score     FLOAT
├── model_path          VARCHAR(255)  ← path to disk model folder
├── status              VARCHAR(20)   ← "active" | "archived" | "deleted"
├── created_by          INT FK → users.id (SET NULL on delete)
├── created_at          DATETIME
└── updated_at          DATETIME
```

**Schema migration:** New LDA config columns are added automatically via `ALTER TABLE` in `init_database()` if they don't exist — including `eta FLOAT NULL DEFAULT NULL` — so existing databases upgrade safely without manual migration.

---

## Frontend Pages

| URL | Template | Purpose |
|-----|----------|---------|
| `/projects` | `templates/projects.html` | List, view documents, edit LDA config (⚙️ LDA button), delete |
| `/admin` | `templates/admin.html` | Load project into memory, run KDD pipeline |
