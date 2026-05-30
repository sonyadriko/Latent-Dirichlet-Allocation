# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Python Version:** 3.12+

### Docker (Recommended)
```bash
docker-compose up -d            # Start
docker-compose up -d --build    # Rebuild after code changes
docker-compose logs -f          # View logs
docker-compose down             # Stop
```

### Local Development
```bash
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"
uvicorn app:app --host 0.0.0.0 --port 3030 --reload
```

**URLs:** Frontend `http://localhost:3030` · API docs `http://localhost:3030/docs` · Health `http://localhost:3030/api/health`

### Utility Scripts
```bash
python scripts/recrawl_project.py <project_id>     # Re-crawl a project (overwrites data)
python scripts/migrate_json_to_mysql.py            # One-time: legacy JSON/SQLite -> MySQL
```

**Database setup:** the app uses an **external MySQL** server. Copy `.env.example` to `.env` and fill in `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` (or a full `DATABASE_URL`). The target schema must exist and the user needs CREATE privileges (tables are auto-created at startup). `charset=utf8mb4` is required.

## Architecture

FastAPI app for LDA topic modeling on Indonesian business news, implementing a KDD (Knowledge Discovery in Databases) pipeline.

**No test suite exists.** Verify changes by running the app.

### Layer structure
```
app.py          → FastAPI entry point, lifespan init, router registration
routers/        → HTTP handlers (thin: validate input, call services, return response)
services/       → Business logic (LDA, crawling, preprocessing, search, pyLDAvis)
repositories/   → Async SQLAlchemy queries (project, document, user, pipeline)
schemas/        → Pydantic request/response models
models/         → db_models.py (SQLAlchemy ORM). user.py/project.py/document.py are LEGACY JSON models, no longer wired in
core/           → database.py, security.py, state.py, exceptions.py, error_handlers.py
```

`routes/` — legacy Flask code, **not used**, ignore it.

### Single source of truth: MySQL

All persistent data (users, projects, documents, pipeline runs) lives in **MySQL** via SQLAlchemy ORM (`models/db_models.py`) and the repositories. The old JSON files (`data/users.json`, `data/projects.json`) and SQLite (`data/lda_app.db`) are **deprecated backups** — the JSON model classes (`models/user.py`, `models/project.py`, `models/document.py`) are no longer imported by routers or services. Do all data access through the repositories.

### Critical architectural quirks

**Sync/async boundary with the LDA service:** `services/lda_service.py` is **synchronous** and does **pure filesystem/Gensim work only** (no DB access). All DB writes happen in the async route handlers. When a router needs to load/train a model, it fetches the project + documents from MySQL and passes them into `lda_service.load_project_model(project_name, project_id, document_count, documents)` / `save_project_model(...)`. **Never call a repository from inside `lda_service`.**

**Pipeline in-memory state:** `core/state.py` exports a global `kdd_state_manager` (async lock-protected dict) holding transient live-progress state. Persistent run history is in the `PipelineRun` table. `kdd_state_manager` resets on restart.

**LDA singleton:** `services/lda_singleton.py` provides `get_lda_service()` for a shared `LDAService` instance. All routers (`kdd`, `project`, `search`) use this singleton, so the currently-loaded project/model is shared across them.

**Gensim model files stay on disk:** trained models are saved under `data/results/{project_name_slug}/` (`lda_model_model`, `lda_model_dict`, `lda_model_mm`, plus `documents.json`). The DB stores only the `model_path`. The LDA service loads them by project **name** (slugified), so the `./data` volume must persist.

### KDD Pipeline (4 stages)

1. **Crawl** — `services/crawler.py` scrapes URLs from an uploaded `.txt` file via BeautifulSoup
2. **Preprocess** — `services/preprocessing.py` runs Sastrawi stemming + NLTK Indonesian stopwords
3. **Transform** — `services/lda_service.py` builds Gensim BoW dictionary and corpus
4. **Mine** — `services/lda_service.py` trains `LdaModel`; results saved to DB + disk

Online document addition (existing project) uses `services/online_crawler.py`.

### Database

Async SQLAlchemy 2.0 + aiomysql (external MySQL). Session dependency: `get_session` (from `core/database.py`) — use with `Depends(get_session)`. Tables auto-created at startup via `init_database()`. Alembic is installed but no migrations exist; schema changes require `alembic revision --autogenerate`.

DB models: `User`, `Project`, `Document`, `PipelineRun` (all in `models/db_models.py`).

### Authentication

JWT (python-jose, HS256, 24h expiry). Protected endpoints use `Depends(get_current_user)`. Token sent as `Authorization: Bearer <token>` from the frontend (stored in localStorage). `get_current_user_optional` returns `None` instead of 401 when no token present.

### Configuration (`config.py`)

All values overridable via environment variables:
- `SECRET_KEY`, `JWT_SECRET_KEY`
- `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE` — composed into a `mysql+aiomysql://...?charset=utf8mb4` URL. An explicit `DATABASE_URL` overrides them.
- LDA defaults: `NUM_TOPICS=5`, `NUM_WORDS_PER_TOPIC=10`, `PASSES=15`, `ITERATIONS=100`

### Adding new endpoints

1. Schema in `schemas/` (or inline on the router if simple)
2. Repository method in `repositories/` for DB access
3. Route in `routers/` using `Depends(get_session)` and `Depends(get_current_user)`
4. Raise typed exceptions from `core/exceptions.py` (`NotFoundException`, `ValidationException`, etc.)

### Frontend

Vanilla JS + Jinja2 templates. Each page (`admin.html`, `projects.html`, `manual-input.html`, `visualization.html`) has a corresponding JS file in `static/js/`. Auth state lives in `localStorage`; the frontend sends Bearer tokens on API calls. `sidebar.js` is shared across pages.
