# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Python Version:** 3.12+ (Dockerfile uses python:3.12-slim)

### Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Check container status
docker-compose ps
```

**Application URLs:**
- Frontend: `http://localhost:3030`
- Backend API: `http://localhost:3030/api/*`
- **Swagger UI (API Documentation): `http://localhost:3030/docs`**
- **ReDoc: `http://localhost:3030/redoc`**
- Health Check: `http://localhost:3030/api/health`

**Backend API Endpoints:**
- Authentication: `/api/auth/*` (register, login, verify, logout)
- KDD Pipeline: `/api/kdd/*` (crawl, preprocess, transform, datamining)
- Search: `/api/search/*` (document search, similarity, train)
- Projects: `/api/projects/*` (project CRUD, list, delete, set current)
- Health: `/api/health`

**API Documentation:**
The application includes auto-generated OpenAPI documentation via FastAPI:
- Swagger UI at `/docs` - interactive API explorer
- ReDoc at `/redoc` - alternative documentation format
- All endpoints are documented with request/response schemas, auth requirements, and examples

### Local Development
```bash
# Create and activate virtual environment (if not exists)
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data (first time setup)
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('punkt_tab')"

# Run the FastAPI application with uvicorn
uvicorn app:app --host 0.0.0.0 --port 3030 --reload
```
The application runs on `http://localhost:3030`

### Virtual Environment
The project uses a Python virtual environment located in `venv/`. Always activate it before running the application.

## Architecture Overview

This is a **FastAPI-based web application** for **LDA (Latent Dirichlet Allocation) Topic Modeling** focused on Indonesian business news analysis. The application implements a complete KDD (Knowledge Discovery in Databases) pipeline with a modern layered architecture.

**Migration Note:** The application was migrated from Flask to FastAPI for better async support, type safety, and automatic API documentation. The legacy `routes/` directory contains old Flask code and is no longer used.

### Layered Architecture

The codebase follows a clean, layered architecture pattern:

```
app.py                    # FastAPI application entry point
├── routers/             # API route handlers (FastAPI)
├── services/            # Business logic layer
├── repositories/        # Data access layer (SQLAlchemy)
├── schemas/             # Pydantic validation schemas
├── models/              # Database models and domain models
├── core/                # Core utilities (database, security, exceptions)
├── templates/           # Jinja2 HTML templates
└── data/                # Data storage (SQLite + JSON files)
```

**Key Architectural Patterns:**
- **Repository Pattern**: `repositories/` abstracts database operations
- **Service Layer**: `services/` contains business logic (LDA, crawling, search)
- **Singleton Pattern**: `lda_singleton.py` ensures one LDA service instance across routers
- **Dependency Injection**: FastAPI's `Depends()` for auth and database sessions

### Core Components

**FastAPI Application** (`app.py`):
- Lifespan context manager for startup/shutdown events
- CORS middleware configuration
- Router registration (`/api/auth`, `/api/kdd`, `/api/search`, `/api/projects`)
- Static files and Jinja2 templates setup
- Page routes (`/`, `/login`, `/register`, `/admin`, `/visualization`, `/projects`)

### KDD Pipeline Implementation

The application implements a 4-step KDD process:

1. **Crawling** (`services/crawler.py`, `services/online_crawler.py`):
   - Extracts content from news URLs
   - Supports Indonesian news websites
   - Handles file upload with multiple URLs
   - Online document crawling for adding documents to existing projects

2. **Preprocessing** (`services/preprocessing.py`):
   - Indonesian text preprocessing using Sastrawi stemmer
   - NLTK tokenization and stopwords removal
   - Case folding, punctuation removal, and cleaning

3. **Transformation** (`services/lda_service.py`):
   - Bag-of-words conversion using Gensim
   - Dictionary and corpus creation
   - Document-term matrix generation

4. **Data Mining** (`services/lda_service.py`):
   - LDA model training with Gensim
   - Topic extraction and coherence calculation
   - Document-topic distribution analysis

### Key Services

**LDAService** (`services/lda_service.py`):
- Core topic modeling functionality
- Gensim-based LDA implementation
- Model persistence and results serialization
- Dictionary and corpus management for projects
- **Singleton Pattern**: Use `get_lda_service()` from `lda_singleton.py` to ensure all routers use the same instance

**SearchService** (`services/search_service.py`):
- Document search with hybrid text matching (title + content)
- Topic-based document similarity using cosine similarity
- Fuzzy matching with configurable thresholds
- Online document crawling integration
- Training mode to rebuild corpus from project documents

**PyLDAvisService** (`services/pyldavis_service.py`):
- Generates interactive LDA visualization with pyLDAvis
- HTML-based visualization export
- Per-project visualization data

**TextPreprocessor** (`services/preprocessing.py`):
- Indonesian text processing pipeline
- Combines NLTK and Sastrawi for comprehensive preprocessing
- Specialized handling for Indonesian language patterns

**CrawlerService** (`services/crawler.py`):
- Web scraping with BeautifulSoup and requests
- Intelligent content extraction for news articles
- Error handling and rate limiting

**OnlineDocumentCrawler** (`services/online_crawler.py`):
- Crawls individual URLs to add documents to existing projects
- Preprocesses and integrates with project corpus

### Database Layer

**Async SQLAlchemy** (`core/database.py`):
- SQLAlchemy 2.0 with async support
- SQLite database with aiosqlite
- Declarative base for model definitions
- Session management with `get_db_session()` dependency

**Repository Pattern** (`repositories/`):
- `project_repository.py` - Project CRUD and queries
- `document_repository.py` - Document management
- `user_repository.py` - User authentication data
- `pipeline_repository.py` - KDD pipeline state management

**Database Models** (`models/db_models.py`):
- `Project` - LDA project metadata
- `Document` - News articles and content
- `User` - User accounts with hashed passwords
- `PipelineState` - KDD pipeline progress tracking

### API Structure

FastAPI routers with automatic OpenAPI documentation:

- `/api/auth/*` - JWT-based user authentication endpoints
- `/api/kdd/*` - KDD pipeline management endpoints
- `/api/search/*` - Document search and similarity endpoints
- `/api/projects/*` - Project CRUD and management endpoints
- `/api/health` - Health check endpoint

**Authentication:**
- JWT-based authentication using `python-jose`
- Bearer token required for protected endpoints
- `get_current_user()` dependency for token validation
- Token stored in HTTP-only cookies and localStorage

**Page Routes:**
- `/` - Main landing page
- `/login`, `/register` - Authentication pages
- `/admin` - Admin dashboard with KDD pipeline controls
- `/visualization` - Topic visualization with pyLDAvis
- `/projects` - Project management page (list, delete, switch)

### Configuration

LDA parameters are configurable in `config.py`:
- `NUM_TOPICS` - Default number of topics (5)
- `NUM_WORDS_PER_TOPIC` - Words displayed per topic (10)
- `PASSES` - LDA training passes (15)
- `ITERATIONS` - LDA training iterations (100)
- `DATABASE_URL` - SQLite database connection string
- `SECRET_KEY` - JWT token signing key

### Data Storage

The application uses a hybrid storage approach:

**SQLite Database** (via SQLAlchemy):
- `data/lda_app.db` - User accounts, projects, documents, pipeline state
- Async operations with aiosqlite
- Declarative models for type-safe queries

**JSON Files** (legacy, being phased out):
- `data/users.json` - User accounts (deprecated)
- `data/news.json` - Sample news data
- `data/results/lda_results.json` - Current analysis results (deprecated)

**Model Persistence:**
- Gensim LDA models saved as `.model` files in `data/results/`
- Dictionary and corpus saved separately as `.dict` and `.mm` files
- Models organized by project: `data/results/{project_name}_*`

### Frontend

Single-page application with Jinja2 templates and vanilla JavaScript:
- User authentication interface
- File upload for URL crawling
- Real-time KDD pipeline progress tracking
- Topic visualization and analysis results
- Project management (list, delete, switch projects)

### Indonesian NLP Stack

The application uses specialized Indonesian language processing:
- **Sastrawi** - Indonesian stemmer for word root extraction
- **NLTK Indonesian stopwords** - Common Indonesian stopword removal
- Custom preprocessing patterns for Indonesian text patterns

### Development Patterns

**Adding New Endpoints:**
1. Create Pydantic schemas in `schemas/` for request/response validation
2. Add repository methods in `repositories/` for database operations
3. Create route handlers in `routers/` with FastAPI decorators
4. Use `Depends(get_db_session)` for database access
5. Use `Depends(get_current_user)` for authenticated endpoints

**Working with LDA Service:**
- Always use `get_lda_service()` from `services/lda_singleton.py`
- This ensures project state consistency across all routers
- The singleton loads the current project's model and corpus automatically

**Error Handling:**
- Custom exceptions in `core/exceptions.py`
- Global error handlers registered in `core/error_handlers.py`
- FastAPI automatically generates error responses

**Database Migrations:**
- Alembic is installed for database migrations
- Migration scripts would go in `alembic/` directory
- Use `alembic revision --autogenerate -m "description"` for schema changes
