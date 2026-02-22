# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

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
- Health Check: `http://localhost:3030/api/health`

**Backend API Endpoints:**
- Authentication: `/api/auth/*` (register, login, verify, logout)
- KDD Pipeline: `/api/kdd/*` (crawl, preprocess, transform, datamining)
- Search: `/api/search/*` (document search and similarity)
- Projects: `/api/projects/*` (project management)
- Health: `/api/health`

**API Documentation:**
The application includes Swagger/OpenAPI documentation available at `/docs`. All endpoints are documented with:
- Request/response schemas
- Authentication requirements (JWT Bearer token)
- Parameter descriptions
- Example values
- Response status codes

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask application
python app.py
```
The application runs on `http://localhost:3030`

### Virtual Environment
The project uses a Python virtual environment located in `venv/`. Always activate it before running the application.

## Architecture Overview

This is a Flask-based web application for **LDA (Latent Dirichlet Allocation) Topic Modeling** focused on Indonesian business news analysis. The application implements a complete KDD (Knowledge Discovery in Databases) pipeline.

### Core Components

**Flask Application Structure:**
- `app.py` - Main Flask application with route registration
- `config.py` - Configuration management including LDA parameters
- `routes/` - API blueprints for modular route handling
- `services/` - Business logic for text processing and LDA
- `models/` - Data models (user, project, document management)
- `templates/` - HTML templates for web interface
- `data/` - Data storage (users, news, results)

### KDD Pipeline Implementation

The application implements a 4-step KDD process:

1. **Crawling** (`services/crawler.py`):
   - Extracts content from news URLs
   - Supports Indonesian news websites
   - Handles file upload with multiple URLs

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

**TextPreprocessor** (`services/preprocessing.py`):
- Indonesian text processing pipeline
- Combines NLTK and Sastrawi for comprehensive preprocessing
- Specialized handling for Indonesian language patterns

**CrawlerService** (`services/crawler.py`):
- Web scraping with BeautifulSoup and requests
- Intelligent content extraction for news articles
- Error handling and rate limiting

**SearchService** (`services/search_service.py`):
- Document search with hybrid text matching (title + content)
- Topic-based document similarity using cosine similarity
- Fuzzy matching with configurable thresholds
- Online document crawling integration

**Authentication** (`routes/auth.py`):
- JWT-based authentication system
- User registration and login management
- Token validation middleware using `@token_required` decorator

**Project Management** (`routes/project.py`, `models/project.py`):
- Multi-project LDA model management
- Project metadata storage and retrieval
- Model persistence per project

### API Structure

- `/api/auth/*` - User authentication endpoints
- `/api/kdd/*` - KDD pipeline management endpoints
- `/api/search/*` - Document search and similarity endpoints
- `/api/projects/*` - Project CRUD and management endpoints
- `/api/health` - Health check endpoint
- Page routes for web interface (`/`, `/login`, `/register`, `/admin`, `/visualization`)

### KDD Pipeline State Management

The pipeline uses in-memory state tracking (`routes/kdd.py`):
- `kdd_state` dictionary tracks progress through all KDD stages
- Each stage has a status: `pending`, `processing`, `completed`, `error`
- Pipeline can run end-to-end or step-by-step through individual endpoints
- Results are persisted to `data/results/` for later retrieval

Key KDD endpoints:
- `POST /api/kdd/crawl` - Full pipeline execution (crawl → preprocess → transform → mine)
- `POST /api/kdd/upload-and-crawl` - Crawling only with file upload
- `POST /api/kdd/preprocessing` - Preprocessing step only
- `POST /api/kdd/transforming` - Bag-of-words transformation step only
- `POST /api/kdd/datamining` - LDA training step only
- `GET /api/kdd/results` - Retrieve pipeline results
- `GET /api/kdd/status` - Check pipeline status and progress

### Configuration

LDA parameters are configurable in `config.py`:
- `NUM_TOPICS` - Default number of topics (5)
- `NUM_WORDS_PER_TOPIC` - Words displayed per topic (10)
- `PASSES` - LDA training passes (15)
- `ITERATIONS` - LDA training iterations (100)
- `SECRET_KEY` - Flask secret key for sessions
- `JWT_SECRET_KEY` - JWT token signing key

### Data Storage

The application uses JSON file-based storage:
- `data/users.json` - User accounts with hashed passwords
- `data/news.json` - Sample news data
- `data/projects.json` - Project metadata and model references
- `data/results/lda_results.json` - Current analysis results
- `data/results/{project_name}_data.json` - Project-specific LDA data

Model persistence:
- Gensim LDA models saved as `.model` files
- Dictionary and corpus saved separately as `.dict` and `.mm` files
- Models are organized by project in `data/results/`

### Frontend

Single-page application with HTML templates and JavaScript for:
- User authentication interface
- File upload for URL crawling
- Real-time KDD pipeline progress tracking
- Topic visualization and analysis results

### Indonesian NLP Stack

The application uses specialized Indonesian language processing:
- **Sastrawi** - Indonesian stemmer for word root extraction
- **NLTK Indonesian stopwords** - Common Indonesian stopword removal
- Custom preprocessing patterns for Indonesian text patterns