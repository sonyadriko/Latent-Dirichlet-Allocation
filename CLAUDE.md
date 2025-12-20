# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask application
python app.py
```
The application runs on `http://localhost:5001`

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
- `models/` - Data models (user management)
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

**TextPreprocessor** (`services/preprocessing.py`):
- Indonesian text processing pipeline
- Combines NLTK and Sastrawi for comprehensive preprocessing

**CrawlerService** (`services/crawler.py`):
- Web scraping with BeautifulSoup and requests
- Intelligent content extraction for news articles
- Error handling and rate limiting

**Authentication** (`routes/auth.py`):
- JWT-based authentication system
- User registration and login management
- Token validation middleware

### API Structure

- `/api/auth/*` - User authentication endpoints
- `/api/kdd/*` - KDD pipeline management endpoints
- `/api/health` - Health check endpoint
- Page routes for web interface (`/`, `/login`, `/register`, `/admin`, `/visualization`)

### Configuration

LDA parameters are configurable in `config.py`:
- `NUM_TOPICS` - Default number of topics (5)
- `NUM_WORDS_PER_TOPIC` - Words displayed per topic (10)
- `PASSES` - LDA training passes (15)
- `ITERATIONS` - LDA training iterations (100)

### Data Storage

The application uses JSON file-based storage:
- `data/users.json` - User accounts
- `data/news.json` - Sample news data
- `data/results/` - LDA analysis results and project data

### Frontend

Single-page application with HTML templates and JavaScript for:
- User authentication interface
- File upload for URL crawling
- Real-time KDD pipeline progress tracking
- Topic visualization and analysis results