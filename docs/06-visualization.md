# Visualization

Interactive topic visualization powered by **pyLDAvis** and **D3.js**. Shows topic clusters in 2D space and term-frequency relationships.

## Endpoints

| Method | Path | Auth | Description |
|--------|------|:----:|-------------|
| GET | `/api/projects/{id}/pyldavis` | No | pyLDAvis data for a saved project |
| GET | `/api/kdd/pyldavis` | No | pyLDAvis data for the current KDD pipeline session |

---

## Project Visualization

**GET /api/projects/{id}/pyldavis**

1. Fetches project + documents from MySQL
2. Loads Gensim model from disk (`data/results/{project_name}/lda_model*`)
3. Generates pyLDAvis data structure (topic distances, term frequencies, term-topic weights)
4. Returns JSON-serializable dict compatible with `ldavis.v3.0.0.js`

```json
{
  "success": true,
  "project": { "id": 4, "name": "gramededd22", ... },
  "data": {
    "mdsDat": { "x": [...], "y": [...], "topics": [...], "Freq": [...] },
    "tinfo": { "Term": [...], "Freq": [...], "Total": [...], "Category": [...], ... },
    "token.table": { ... },
    "R": 30,
    "lambda.step": 0.01,
    "plot.opts": { "xlab": "PC1", "ylab": "PC2" }
  },
  "message": "pyLDAvis data prepared for project: gramededd22"
}
```

**Error responses:**
```json
{ "success": false, "message": "Project with ID {id} not found" }
{ "success": false, "message": "Failed to load project model: Model files not found for this project" }
{ "success": false, "message": "Failed to prepare pyLDAvis visualization data. The model may not have been trained properly." }
```

---

## KDD Session Visualization

**GET /api/kdd/pyldavis**

Returns pyLDAvis data for the model trained in the **current server session** (in-memory state from KDD pipeline steps). No project ID required — uses the model currently held in `lda_service`.

**Requires:**
- Stage 3 (Transform) completed: corpus must exist
- Stage 4 (Data Mining) completed: model must be trained

```json
{ "success": false, "message": "LDA model not trained yet. Please complete the data mining step first." }
{ "success": false, "message": "Transformed data not available. Please complete the transforming step first." }
```

---

## Visualization Behavior

**2D topic map:** Topics plotted as circles. Circle size proportional to topic frequency in the corpus. Distance between circles indicates semantic dissimilarity (computed via PCA on topic-term distributions).

**Term relevance slider (λ):** Controls the balance between term frequency and topic exclusivity. Step: 0.01.
- λ = 1: ranks terms purely by probability within topic
- λ = 0: ranks terms by how exclusively they belong to this topic

**Top terms:** `NUM_WORDS_PER_TOPIC` (default 10) from `config.py`.

**Sort topics:** Topics sorted by relevance/frequency (default: `sort_topics=True`).

---

## Frontend

**`/visualization`** → `templates/visualization.html`

**Static JS files loaded:**
- `static/js/d3.v5.min.js` — D3 v5 (dependency of pyLDAvis)
- `static/js/ldavis.v3.0.0.js` — Official pyLDAvis JS renderer
- `static/js/pyldavis.js` — App wrapper (loads data, initializes vis, handles project selection)
- `static/js/visualization.js` — Additional topic/document display logic

**UI sections:**
1. **Project selector** — loads available projects, triggers `GET /api/projects/{id}/pyldavis`
2. **Interactive pyLDAvis panel** — rendered in `#ldavis-container`
3. **Topic word list** — shows top words per topic alongside the chart
4. **Search & similar docs** — integrates with `GET /api/search/documents` for topic-filtered search results

**Loading flow:**
1. Page load: fetch `/api/projects/` → populate dropdown
2. User selects project: call `GET /api/projects/{id}/pyldavis`
3. Data injected into `LDAvis(data, "#ldavis-container", {...})`
4. If visualization data unavailable, fallback message shown

---

## Requirements

Visualization requires **both** a trained Gensim model and a corpus. If the corpus was not saved to disk at training time (old projects), it is rebuilt from the project's documents stored in MySQL when the project is loaded.

Corpus rebuild path: MySQL documents → preprocess → `Dictionary.doc2bow()` → serialize to `lda_model_mm`.
