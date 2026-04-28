# AGENTS.md

This file defines specialized agents for working with the LDA Topic Modeling codebase.

## Available Agents

### kdd-pipeline-agent

**Purpose:** Handle KDD (Knowledge Discovery in Databases) pipeline operations including crawling, preprocessing, transformation, and data mining.

**When to use:**
- Modifying or debugging the KDD pipeline flow
- Adding new preprocessing steps
- Working with pipeline state management
- Implementing new data sources for crawling
- Fixing issues with corpus transformation

**Key files:**
- `routers/kdd.py` - KDD pipeline API endpoints
- `services/crawler.py` - Web crawling service
- `services/online_crawler.py` - Online document crawler
- `services/preprocessing.py` - Indonesian text preprocessing
- `repositories/pipeline_repository.py` - Pipeline state data access
- `schemas/pipeline.py` - Pipeline validation schemas

**Example prompts:**
- "Add a new preprocessing step for named entity recognition"
- "Debug why the crawling step is failing for certain URLs"
- "Add support for crawling from a new Indonesian news site"
- "Fix the corpus transformation to handle empty documents"

---

### lda-service-agent

**Purpose:** Manage LDA model training, topic extraction, coherence calculation, and model persistence.

**When to use:**
- Modifying LDA training parameters or logic
- Improving topic coherence calculation
- Working with model persistence and loading
- Implementing new topic visualization features
- Debugging LDA model issues

**Key files:**
- `services/lda_service.py` - Core LDA service
- `services/lda_singleton.py` - Singleton pattern for LDA service
- `services/pyldavis_service.py` - pyLDAvis visualization
- `config.py` - LDA configuration parameters

**Example prompts:**
- "Optimize LDA training for faster convergence"
- "Add automatic topic number selection using coherence score"
- "Fix model loading issues when switching projects"
- "Implement dynamic alpha and beta parameter tuning"

---

### search-service-agent

**Purpose:** Handle document search, similarity calculation, online crawling, and corpus rebuilding.

**When to use:**
- Improving search relevance and accuracy
- Adding new similarity metrics
- Working with online document crawling
- Implementing corpus rebuild functionality
- Debugging search-related issues

**Key files:**
- `routers/search.py` - Search API endpoints
- `services/search_service.py` - Search and similarity logic
- `services/online_crawler.py` - Online document crawler
- `schemas/search.py` - Search validation schemas

**Example prompts:**
- "Add TF-IDF based search as an alternative to cosine similarity"
- "Improve fuzzy matching for typos in Indonesian text"
- "Fix corpus rebuild to respect current project documents"
- "Add search result highlighting for matched terms"

---

### database-agent

**Purpose:** Handle database operations, migrations, repository changes, and data model updates.

**When to use:**
- Creating new database tables or columns
- Writing or running Alembic migrations
- Modifying repository methods
- Optimizing database queries
- Fixing data integrity issues

**Key files:**
- `core/database.py` - Database session management
- `models/db_models.py` - SQLAlchemy database models
- `repositories/` - All repository modules
- `alembic/` - Database migrations (if exists)

**Example prompts:**
- "Create a migration to add document tags"
- "Optimize the project list query for better performance"
- "Add repository methods for batch document operations"
- "Fix foreign key constraints between projects and documents"

---

### api-router-agent

**Purpose:** Create new API endpoints, handle authentication, define request/response schemas, and implement API business logic.

**When to use:**
- Adding new API endpoints
- Modifying authentication or authorization
- Creating new Pydantic schemas
- Implementing API business logic
- Fixing API response issues

**Key files:**
- `app.py` - FastAPI application setup
- `routers/` - All router modules
- `schemas/` - Pydantic validation schemas
- `core/security.py` - JWT authentication
- `core/exceptions.py` - Custom exceptions

**Example prompts:**
- "Add an endpoint to export project results as CSV"
- "Implement role-based access control for projects"
- "Add request validation for project creation"
- "Fix the error response format for validation errors"

---

### nlp-preprocessing-agent

**Purpose:** Improve Indonesian text preprocessing, tokenization, stemming, and stopwords handling.

**When to use:**
- Enhancing Indonesian text preprocessing
- Adding new text cleaning steps
- Improving tokenization for Indonesian
- Working with Sastrawi stemmer
- Implementing custom stopwords

**Key files:**
- `services/preprocessing.py` - Text preprocessing pipeline
- `services/crawler.py` - Content extraction and cleaning
- `config.py` - Preprocessing configuration

**Example prompts:**
- "Add emoji removal to preprocessing pipeline"
- "Improve stemming for Indonesian business terms"
- "Add custom stopwords for news article filtering"
- "Implement sentence segmentation for Indonesian text"

---

## How to Use Agents

When working with this codebase, invoke the appropriate agent based on the task:

```bash
# Example: Work on KDD pipeline
claude "Use kdd-pipeline-agent to add support for PDF crawling"

# Example: Fix search issues
claude "Use search-service-agent to debug search relevance issues"

# Example: Database migration
claude "Use database-agent to create a migration for document tags"
```

**Important:** Always use the most specific agent for your task. The agents have specialized knowledge of their respective domains.

## Agent Best Practices

1. **Always use the singleton LDA service**: When working with LDA operations, use `get_lda_service()` from `services/lda_singleton.py`

2. **Follow the layered architecture**: Changes should flow through Routers → Services → Repositories → Database

3. **Use dependency injection**: FastAPI's `Depends()` for database sessions and authentication

4. **Validate with schemas**: Always define Pydantic schemas for request/response validation

5. **Handle Indonesian text**: Remember the application specializes in Indonesian business news - use Sastrawi and NLTK Indonesian resources

6. **Test with Docker**: Use Docker for testing to ensure consistent environment with production
