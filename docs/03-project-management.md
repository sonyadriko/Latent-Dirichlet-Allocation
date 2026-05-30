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
  "num_topics": 7
}
```

| Field | Constraint |
|-------|-----------|
| `name` | 2–100 chars, required, globally unique |
| `description` | Optional |
| `num_topics` | Integer 1–50, default 5 |

**Success:**
```json
{ "success": true, "data": { "id": 4, "name": "Analisis Berita Ekonomi", "num_topics": 7, ... } }
```

**Error:**
```json
{ "success": false, "message": "Project name already exists" }
```

---

## List Projects

**GET /api/projects/**

Returns only active projects (`status = "active"`) ordered by `created_at` descending.

```json
{
  "success": true,
  "data": [
    { "id": 4, "name": "...", "num_topics": 7, "document_count": 39, "coherence_score": 0.412, "status": "active", ... }
  ]
}
```

---

## Load Project Model

**POST /api/projects/{id}/load**

Loads the project's Gensim LDA model from disk into memory so that search, similarity, and visualization features can use it.

```json
{
  "success": true,
  "data": { "project": { ... }, "model_loaded": true, "message": "Successfully loaded project: ..." }
}
```

**What happens:**
1. Project row fetched from MySQL.
2. Documents fetched (up to 10,000) to rebuild corpus if not on disk.
3. `lda_service.load_project_model(name, id, doc_count, documents)` called.
4. Model files loaded from `data/results/{project_name}/`.

**Errors:**
- `"Project not found"` — ID doesn't exist
- `"Model files not found for this project"` — project was created but never trained, or model folder was deleted

**Note:** Only one project model lives in memory at a time (singleton LDA service). Loading a new project replaces the previous one.

---

## Delete Project

**DELETE /api/projects/{id}/delete**

Permanently removes:
- MySQL rows: project + all documents + pipeline runs (cascade)
- Disk: model folder at `data/results/{project_name}/`

```json
{ "success": true, "message": "Project \"Analisis Berita Ekonomi\" deleted successfully" }
```

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

Copies metadata only — documents are **not** copied, `document_count` starts at 0. The clone must be trained with new documents to produce a functional model.

Default new name: `"{original} (Copy)"` if `name` is not provided.

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

## Get Project Documents

**GET /api/projects/{id}/documents**

Returns up to 10,000 documents for the project. Response includes `content` truncated to 500 chars (use `to_dict_full()` via the document detail endpoint for full content).

```json
{
  "success": true,
  "data": {
    "project": { ... },
    "documents": [ { "id": 1, "title": "...", "content": "...", "url": "...", "tokens_count": 87 } ],
    "total": 39
  }
}
```

---

## Data Model

```
Project
├── id                INT PK
├── name              VARCHAR(100) UNIQUE
├── description       TEXT
├── num_topics        INT (default 5)
├── document_count    INT (denormalized counter, kept in sync)
├── coherence_score   FLOAT
├── model_path        VARCHAR(255)  ← path to disk model folder
├── status            VARCHAR(20)   ← "active" | "archived" | "deleted"
├── created_by        INT FK → users.id (SET NULL on delete)
├── created_at        DATETIME
└── updated_at        DATETIME
```

---

## Frontend Pages

| URL | Template | Purpose |
|-----|----------|---------|
| `/projects` | `templates/projects.html` | List, view documents, delete |
| `/admin` | `templates/admin.html` | Create, load, clone, KDD pipeline |
