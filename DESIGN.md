# DESIGN.md

This file documents the design decisions, architectural patterns, and system design for the LDA Topic Modeling application.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login   │  │   Admin  │  │    Viz   │  │ Projects │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   Auth   │  │    KDD   │  │  Search  │  │ Projects │       │
│  │  Router  │  │  Router  │  │  Router  │  │  Router  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │    LDA   │  │  Search  │  │ Crawler  │  │Preprocess│       │
│  │ Service  │  │ Service  │  │ Service  │  │ Service  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Repository Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  User    │  │ Project  │  │ Document │  │ Pipeline │       │
│  │    Repo  │  │    Repo  │  │    Repo  │  │    Repo  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Data Storage Layer                        │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │  SQLite Database │  │  File System     │                    │
│  │  (SQLAlchemy)    │  │  (Models, Corpus)│                   │
│  └──────────────────┘  └──────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### KDD Pipeline Architecture

```
Input URLs → Crawling → Preprocessing → Transformation → Data Mining → Results
              ↓           ↓               ↓               ↓
         Extract     Indonesian     Bag-of-Words     LDA Training
         Content     Text Cleaning    & Dictionary    & Topics
                     & Stemming
```

## Design Decisions

### 1. Framework Migration: Flask → FastAPI

**Decision:** Migrate from Flask to FastAPI

**Rationale:**
- **Async Support:** Native async/await for better I/O performance
- **Type Safety:** Built-in Pydantic validation reduces runtime errors
- **Auto Documentation:** Automatic OpenAPI/Swagger generation
- **Better Dependency Injection:** Cleaner dependency management
- **Modern Python:** Takes advantage of Python 3.12+ features

**Trade-offs:**
- Steeper learning curve for developers unfamiliar with async
- More boilerplate for simple endpoints
- Debugging async code can be more complex

---

### 2. Repository Pattern

**Decision:** Implement repository pattern for data access

**Rationale:**
- **Separation of Concerns:** Business logic separated from data access
- **Testability:** Easy to mock repositories for testing
- **Maintainability:** Single place for database queries per entity
- **Flexibility:** Can swap database implementations without affecting services

**Implementation:**
```python
# Repository interface
class ProjectRepository:
    @staticmethod
    async def create(session, name, description, ...) -> Project
    async def get_by_id(session, project_id) -> Optional[Project]
    async def list(session, user_id) -> List[Project]
    async def update(session, project_id, **kwargs) -> Project
    async def delete(session, project_id) -> bool
```

---

### 3. Singleton Pattern for LDA Service

**Decision:** Use singleton pattern for LDA service instance

**Rationale:**
- **State Consistency:** All routers work with same project state
- **Resource Efficiency:** Single Gensim model in memory
- **Project Switching:** Centralized project loading logic
- **Cache Management:** Single cache for dictionary and corpus

**Implementation:**
```python
# services/lda_singleton.py
_lda_service_instance = None

def get_lda_service() -> LDAService:
    global _lda_service_instance
    if _lda_service_instance is None:
        _lda_service_instance = LDAService()
    return _lda_service_instance
```

**Critical Rule:** Always use `get_lda_service()` never `LDAService()` in routers

---

### 4. Hybrid Storage Strategy

**Decision:** Use SQLite for metadata + File system for models

**Rationale:**
- **SQLite:** Fast, embedded, perfect for metadata (users, projects, documents)
- **File System:** Gensim models are binary files, not suitable for database BLOB
- **Simplicity:** No external database service needed for deployment
- **Performance:** Models loaded directly from disk by Gensim

**Storage Layout:**
```
data/
├── lda_app.db              # SQLite database
├── results/
│   ├── project1.model      # Gensim LDA model
│   ├── project1.dict       # Gensim dictionary
│   ├── project1.mm         # Gensim corpus
│   └── project1_data.json  # Additional metadata
```

---

### 5. Layered Architecture

**Decision:** Implement strict layered architecture

**Rationale:**
- **Clear Boundaries:** Each layer has specific responsibility
- **Dependency Flow:** One-way dependency (Router → Service → Repository)
- **Testability:** Each layer can be tested independently
- **Scalability:** Easy to replace or modify individual layers

**Rules:**
1. Routers never access database directly
2. Services never access database directly (use repositories)
3. Repositories never contain business logic
4. Models never depend on services or repositories

---

## Technology Choices

### Backend Framework: FastAPI 0.115.0

**Why:**
- Modern async framework
- Automatic API documentation
- Built-in request validation
- Excellent performance (on par with NodeJS)
- Native WebSocket support (future real-time features)

### Database: SQLite + SQLAlchemy 2.0

**Why SQLite:**
- Zero configuration
- Single file storage
- Sufficient for current load
- Easy backup and migration

**Why SQLAlchemy:**
- Industry standard ORM
- Async support in 2.0
- Database agnostic (can migrate to PostgreSQL later)
- Powerful query builder

### NLP Stack: Gensim + NLTK + Sastrawi

**Why Gensim:**
- Best-in-class LDA implementation
- Efficient corpus handling
- Built-in coherence calculation
- Excellent Indonesian language support

**Why Sastrawi:**
- Native Indonesian stemmer
- Better accuracy than generic stemmers
- Active maintenance

**Why NLTK:**
- Comprehensive Indonesian stopwords
- Flexible tokenization
- Industry standard

### Task Queue: None (Currently)

**Current State:** Synchronous execution

**Future Consideration:** Celery + Redis for:
- Long-running LDA training
- Background crawling
- Periodic retraining

---

## Data Models

### Entity Relationships

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│    User     │────1:N──│   Project    │────1:N──│  Document   │
└─────────────┘         └──────────────┘         └─────────────┘
                                                      │
                                                      │
                                                      ▼
                                            ┌──────────────────┐
                                            │ PipelineState    │
                                            └──────────────────┘
```

### Core Entities

**User:**
```python
- id: int (PK)
- email: str (unique)
- password_hash: str
- created_at: datetime
```

**Project:**
```python
- id: int (PK)
- name: str (unique)
- description: str (optional)
- num_topics: int
- document_count: int
- coherence_score: float
- model_path: str (optional)
- created_by: int (FK → User)
- status: str
- created_at: datetime
- updated_at: datetime
```

**Document:**
```python
- id: int (PK)
- project_id: int (FK → Project)
- url: str
- title: str
- content: str
- content_preview: str (optional)
- crawled_at: datetime
```

**PipelineState:**
```python
- id: int (PK)
- project_id: int (FK → Project)
- stage: str (crawl/preprocess/transform/mine)
- status: str (pending/processing/completed/error)
- progress: int (0-100)
- error_message: str (optional)
```

---

## API Design Patterns

### RESTful Conventions

**Resource Naming:**
- Plural nouns: `/api/projects`, `/api/documents`
- Nested resources: `/api/projects/{id}/documents`
- Actions: `/api/projects/{id}/train` (for non-CRUD operations)

**HTTP Methods:**
- `GET` - Retrieve resources
- `POST` - Create resources or trigger actions
- `PUT/PATCH` - Update resources
- `DELETE` - Remove resources

### Response Format

**Success Response:**
```python
{
    "success": True,
    "data": {...},
    "message": "Optional success message"
}
```

**Error Response:**
```python
{
    "success": False,
    "error": "Error type",
    "message": "Human-readable error message",
    "details": {...}  # Optional validation errors
}
```

### Authentication Pattern

**JWT Token Storage:**
- Server-side: HTTP-only cookie
- Client-side: localStorage (for API calls)

**Protected Endpoint Pattern:**
```python
@router.get("/api/protected")
async def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    # current_user is guaranteed to be authenticated
    pass
```

---

## Security Considerations

### Current Implementation

1. **Password Hashing:** bcrypt with salt
2. **JWT Tokens:** Short-lived access tokens
3. **SQL Injection:** Protected by SQLAlchemy parameterized queries
4. **XSS Protection:** Input validation via Pydantic schemas
5. **CORS:** Configured for specific origins (currently wildcard)

### Future Improvements

1. **Rate Limiting:** Prevent abuse of API endpoints
2. **CSRF Protection:** Additional layer for form submissions
3. **Input Sanitization:** Additional cleaning for user content
4. **HTTPS Enforcement:** Redirect HTTP to HTTPS
5. **Token Refresh:** Implement refresh token rotation

---

## Performance Considerations

### Current Optimizations

1. **Async I/O:** Non-blocking database and file operations
2. **Connection Pooling:** SQLAlchemy connection pool
3. **Lazy Loading:** Documents loaded on-demand
4. **Model Caching:** LDA model kept in memory

### Bottlenecks

1. **LDA Training:** CPU-intensive, blocks during training
2. **Large Corpora:** Memory-intensive for large document sets
3. **Visualization:** pyLDAvis generation can be slow

### Optimization Strategies

1. **Background Tasks:** Move LDA training to background queue
2. **Incremental Training:** Use Gensim's online LDA
3. **Caching:** Cache frequently accessed data
4. **Pagination:** Limit result sets for list endpoints

---

## Scalability Considerations

### Current Limitations

1. **Single Server:** No horizontal scaling
2. **SQLite:** Not suitable for high concurrency
3. **File Storage:** Local filesystem doesn't scale
4. **Memory:** Models loaded per instance

### Scaling Path

**Phase 1: Database Migration**
- Migrate from SQLite to PostgreSQL
- Use connection pooling
- Implement read replicas

**Phase 2: Distributed Task Queue**
- Implement Celery + Redis
- Background LDA training
- Async crawling

**Phase 3: Microservices**
- Separate LDA training service
- Dedicated crawling service
- API gateway

**Phase 4: Cloud Storage**
- Migrate models to S3-compatible storage
- Use CDN for static assets
- Distributed caching (Redis)

---

## Future Improvements

### Short Term (1-3 months)

1. **Enhanced Search:** Add TF-IDF and BM25 ranking
2. **Better Visualization:** Interactive topic exploration
3. **Export Features:** CSV, JSON, PDF exports
4. **Batch Operations:** Bulk document upload
5. **API Rate Limiting:** Prevent abuse

### Medium Term (3-6 months)

1. **Background Tasks:** Celery for async operations
2. **Real-time Updates:** WebSocket for pipeline progress
3. **Advanced Preprocessing:** Named entity recognition
4. **Topic Labeling:** Automatic topic naming
5. **Trend Analysis:** Temporal topic evolution

### Long Term (6+ months)

1. **Multi-language Support:** English, Malay support
2. **Advanced Models:** BERTopic, NMF alternatives
3. **Distributed Training:** Spark-based LDA
4. **API Gateway:** Rate limiting, authentication
5. **Microservices Architecture:** Service decomposition

---

## Development Guidelines

### Code Style

1. **Async Functions:** Use `async/await` for I/O operations
2. **Type Hints:** All functions should have type hints
3. **Docstrings:** Google-style docstrings for public functions
4. **Error Handling:** Specific exceptions, never bare `except`

### Testing Strategy

1. **Unit Tests:** Repository and service layer tests
2. **Integration Tests:** API endpoint tests
3. **E2E Tests:** Critical user flows
4. **Performance Tests:** LDA training benchmarks

### Deployment Strategy

1. **Docker:** Containerized application
2. **Docker Compose:** Local development setup
3. **Environment Variables:** Configuration via environment
4. **Health Checks:** `/api/health` endpoint for monitoring

---

## Design Principles

1. **Simplicity:** Simple solutions preferred over clever ones
2. **Explicit over Implicit:** Clear is better than cute
3. **Progressive Enhancement:** Start simple, add complexity as needed
4. **User Focus:** Indonesian business news users first
5. **Data Quality:** Better preprocessing over complex models

## Anti-Patterns to Avoid

1. **Direct Database Access in Routers:** Always use repositories
2. **Multiple LDA Instances:** Always use singleton
3. **Synchronous I/O:** Use async for database and file operations
4. **Hardcoded Configuration:** Use config.py and environment variables
5. **Silent Failures:** Always log and surface errors appropriately
