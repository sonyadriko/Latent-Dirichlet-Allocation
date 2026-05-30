# Document Management

Manual document input for building an LDA corpus without crawling URLs. Documents can be entered individually or in bulk, associated with a project, and edited or deleted after creation.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| POST | `/api/documents/manual` | Yes | Create single document |
| POST | `/api/documents/manual/bulk` | Yes | Create 1–100 documents at once |
| GET | `/api/documents/manual` | Yes | List documents (filterable by project) |
| PUT | `/api/documents/manual/{id}` | Yes | Update title and/or content |
| DELETE | `/api/documents/manual/{id}` | Yes | Delete document |

---

## Create Single Document

**POST /api/documents/manual**

```json
{
  "title": "Eternal Love",
  "content": "Waktu tidak menyembuhkan apa pun...",
  "project_id": 4
}
```

| Field | Constraint |
|-------|-----------|
| `title` | 1–500 chars, required |
| `content` | ≥1 char, required |
| `project_id` | Optional; project must exist if provided |

**Success:**
```json
{
  "id": 42,
  "title": "Eternal Love",
  "content": "Waktu tidak menyembuhkan apa pun...",
  "url": null,
  "tokens_count": 0,
  "dominant_topic": null,
  "dominant_prob": null,
  "project_id": 4,
  "created_at": "2024-06-01T12:00:00"
}
```

Creating a document also increments `project.document_count` in MySQL.

---

## Bulk Create

**POST /api/documents/manual/bulk**

```json
{
  "documents": [
    { "title": "Doc 1", "content": "..." },
    { "title": "Doc 2", "content": "..." }
  ],
  "project_id": 4
}
```

| Constraint | Value |
|-----------|-------|
| `documents` length | 1–100 |
| Each `title` | Required, non-empty |
| Each `content` | Required, non-empty |

**Deduplication:** Documents whose `title` already exists in the project are silently skipped. If all documents are duplicates, the response returns the existing documents with `created_count: 0`.

**Success:**
```json
{
  "created_count": 38,
  "documents": [ ... ],
  "message": "Successfully created 38 documents"
}
```

**All-duplicate response:**
```json
{
  "created_count": 0,
  "documents": [ ... existing docs ... ],
  "message": "All documents already exist in database (39 found)"
}
```

---

## List Documents

**GET /api/documents/manual?project_id=4&limit=50&offset=0**

| Query param | Default | Range |
|------------|---------|-------|
| `project_id` | — | optional |
| `limit` | 100 | 1–1000 |
| `offset` | 0 | ≥0 |

**Note:** `content` in list responses is truncated to 500 chars. The full content is returned only in individual responses (create/update).

---

## Update Document

**PUT /api/documents/manual/{id}**

```json
{
  "title": "New Title",
  "content": "Updated content..."
}
```

Either or both fields can be included. Fields not provided are left unchanged.

Returns the updated document. Returns 404 if not found.

---

## Delete Document

**DELETE /api/documents/manual/{id}**

```json
{ "success": true, "message": "Document 'Eternal Love' deleted successfully" }
```

Returns 404 if not found.

---

## Data Model

```
Document
├── id              INT PK
├── title           TEXT
├── content         TEXT
├── url             TEXT (NULL for manual docs)
├── tokens_count    INT (0 until preprocessing runs)
├── dominant_topic  INT (NULL until LDA inference)
├── dominant_prob   FLOAT (NULL until LDA inference)
├── project_id      INT FK → projects.id (CASCADE DELETE)
├── created_at      DATETIME
└── updated_at      DATETIME
```

`tokens_count`, `dominant_topic`, and `dominant_prob` are populated when the LDA pipeline processes the document. Manually entered documents start with `url = NULL`.

---

## Frontend Page

**`/manual-input`** → `templates/manual-input.html`

**Workflow:**
1. Select an existing project from the dropdown (or create new)
2. Fill title + content, click **➕ Tambah ke List** (adds to local buffer — not saved yet)
3. Click **💾 Simpan Semua** to bulk-save the buffered documents to MySQL
4. Existing saved documents show a **✓ Tersimpan** badge; new unsaved ones show **⏳ Belum disimpan**
5. Click **✏️** to edit an existing document (calls `PUT` immediately on save)
6. Click **🗑️** to delete (calls `DELETE` immediately)

**Character counter:** Updates live as you type. Visible word count per document.

**Bulk save:** Calls `POST /api/documents/manual/bulk`. Duplicate titles within the same project are automatically skipped.

---

## Error Responses

| Message | Cause |
|---------|-------|
| `"Document at index {i} is missing 'title' field"` | Blank title in bulk array |
| `"Document at index {i} is missing 'content' field"` | Blank content in bulk array |
| `"Project with ID {id} not found"` | Invalid `project_id` |
| `"Document with ID {id} not found"` | Invalid doc ID in update/delete |
| `"Error creating document: {detail}"` | Unexpected DB error |
