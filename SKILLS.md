# SKILLS.md

This file defines reusable skills for working with the LDA Topic Modeling codebase.

## Available Skills

### add-api-endpoint

**Description:** Add a new API endpoint following FastAPI patterns with proper authentication, validation, and error handling.

**When to use:**
- Creating new API routes
- Adding CRUD operations for resources
- Implementing new feature endpoints

**Steps:**
1. Create Pydantic schemas in `schemas/` for request/response
2. Add repository methods in `repositories/` for database operations
3. Create route handler in appropriate `routers/` file
4. Use `Depends(get_db_session)` for database access
5. Use `Depends(get_current_user)` for authenticated endpoints
6. Add proper error handling with custom exceptions
7. Test endpoint at `/docs` (Swagger UI)

**Example:**
```python
# schemas/new_feature.py
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    name: str
    description: Optional[str] = None

class NewFeatureResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]

# routers/new_feature.py
from fastapi import APIRouter, Depends
from core.database import get_db_session
from core.security import get_current_user
from models.user import User

router = APIRouter()

@router.post("/api/new-feature", response_model=NewFeatureResponse)
async def create_new_feature(
    request: NewFeatureRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    # Implementation here
    pass
```

---

### create-database-migration

**Description:** Create and apply Alembic database migration for schema changes.

**When to use:**
- Adding new tables or columns
- Modifying existing database schema
- Changing relationships between models

**Steps:**
1. Modify `models/db_models.py` with your changes
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Verify changes in database

**Example:**
```bash
# After adding new column to Project model
alembic revision --autogenerate -m "add project status"
alembic upgrade head
```

---

### add-preprocessing-step

**Description:** Add a new preprocessing step to the Indonesian text processing pipeline.

**When to use:**
- Implementing new text cleaning operations
- Adding custom Indonesian language processing
- Enhancing tokenization or stemming

**Steps:**
1. Add new method to `services/preprocessing.py`
2. Update `TextPreprocessor.preprocess()` method to include new step
3. Test with sample Indonesian text
4. Verify impact on LDA results

**Example:**
```python
# In services/preprocessing.py
class TextPreprocessor:
    def preprocess(self, text: str) -> str:
        # Existing steps...
        text = self._new_preprocessing_step(text)
        # Continue with pipeline...
        return text

    def _new_preprocessing_step(self, text: str) -> str:
        # Your new preprocessing logic
        return processed_text
```

---

### implement-search-feature

**Description:** Implement a new search or similarity feature using the search service.

**When to use:**
- Adding new search methods
- Implementing different similarity metrics
- Creating document comparison features

**Steps:**
1. Add method to `services/search_service.py`
2. Create validation schemas in `schemas/search.py`
3. Add endpoint in `routers/search.py`
4. Use singleton LDA service: `get_lda_service()`
5. Test with various query patterns

**Example:**
```python
# In services/search_service.py
class SearchService:
    def new_search_method(self, query: str, project_id: int):
        # Implementation using LDA service
        lda_service = get_lda_service()
        # Your search logic
        return results
```

---

### add-project-feature

**Description:** Add a new feature to project management (create, update, delete, switch projects).

**When to use:**
- Extending project CRUD operations
- Adding project-level settings
- Implementing project switching logic

**Steps:**
1. Add column to `Project` model in `models/db_models.py`
2. Create migration
3. Update repository in `repositories/project_repository.py`
4. Add schemas in `schemas/project.py`
5. Update router in `routers/project.py`
6. Update LDA service to handle new feature

**Example:**
```python
# models/db_models.py
class Project(Base):
    # Existing fields...
    new_feature = Column(String, nullable=True)

# repositories/project_repository.py
@staticmethod
async def update_new_feature(session: AsyncSession, project_id: int, new_feature: str):
    # Implementation
    pass
```

---

### implement-visualization

**Description:** Add or modify visualization features for LDA topics and results.

**When to use:**
- Creating new visualization types
- Enhancing existing pyLDAvis integration
- Adding custom topic visualizations

**Steps:**
1. Add method to `services/pyldavis_service.py`
2. Create endpoint in appropriate router
3. Generate visualization data
4. Create/update HTML template if needed
5. Test visualization rendering

**Example:**
```python
# In services/pyldavis_service.py
class PyLDAvisService:
    def generate_custom_visualization(self, project_id: int):
        lda_service = get_lda_service()
        # Generate visualization data
        return visualization_html
```

---

### add-crawler-source

**Description:** Add support for crawling from a new news source or website.

**When to use:**
- Supporting new Indonesian news sites
- Adding different content sources
- Implementing custom content extractors

**Steps:**
1. Add domain-specific extractor to `services/crawler.py`
2. Handle authentication or special requirements
3. Add error handling for the source
4. Test with multiple URLs from the source
5. Document source-specific requirements

**Example:**
```python
# In services/crawler.py
class CrawlerService:
    def crawl_new_source(self, url: str) -> dict:
        # Source-specific extraction logic
        if "newsource.com" in url:
            return self._extract_newsource(url)
        # Default extraction
        return self._extract_generic(url)
```

---

### fix-project-switching

**Description:** Fix issues related to project switching, model loading, and state management.

**When to use:**
- Projects not loading correctly
- Wrong model being used
- State inconsistencies after switching

**Steps:**
1. Check `services/lda_singleton.py` singleton implementation
2. Verify `lda_service.load_project()` is called correctly
3. Check `repositories/project_repository.py` for correct project retrieval
4. Ensure router uses `get_lda_service()` not `LDAService()`
5. Verify project document loading

**Example:**
```python
# Verify singleton is used correctly
from services.lda_singleton import get_lda_service

# CORRECT
lda_service = get_lda_service()

# WRONG - creates new instance
lda_service = LDAService()
```

---

### optimize-lda-training

**Description:** Optimize LDA model training performance and accuracy.

**When to use:**
- Training is too slow
- Poor topic coherence
- Need better hyperparameters

**Steps:**
1. Review parameters in `config.py`
2. Analyze current coherence scores
3. Adjust `NUM_TOPICS`, `PASSES`, `ITERATIONS`
4. Consider document filtering in preprocessing
5. Test with different parameters

**Parameters to tune:**
```python
# config.py
NUM_TOPICS = 5  # Try 3-20
PASSES = 15     # Try 10-50
ITERATIONS = 100  # Try 50-1000
ALPHA = 'symmetric'  # Try 'asymmetric'
BETA = None  # Try specific values
```

---

### handle-indonesian-text

**Description:** Properly handle Indonesian language text in processing and display.

**When to use:**
- Working with Indonesian content
- Fixing encoding issues
- Implementing Indonesian-specific features

**Steps:**
1. Use UTF-8 encoding throughout
2. Utilize Sastrawi for stemming
3. Use NLTK Indonesian stopwords
4. Consider Indonesian punctuation patterns
5. Test with real Indonesian news text

**Example:**
```python
# Indonesian text processing
import nltk
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Download Indonesian resources
nltk.download('stopwords')
from nltk.corpus import stopwords
indonesian_stopwords = set(stopwords.words('indonesian'))

# Use Sastrawi stemmer
factory = StemmerFactory()
stemmer = factory.create_stemmer()
```

---

## Skill Best Practices

1. **Always use the singleton**: When working with LDA, use `get_lda_service()` from `services/lda_singleton.py`

2. **Follow the layer pattern**: Router → Service → Repository → Database

3. **Validate with schemas**: Always define Pydantic schemas for API inputs/outputs

4. **Handle async correctly**: Use `async/await` for database operations and service calls

5. **Test with real data**: Use actual Indonesian news articles for testing

6. **Check authentication**: Use `Depends(get_current_user)` for protected endpoints

7. **Handle errors gracefully**: Use custom exceptions from `core/exceptions.py`

8. **Document your changes**: Update relevant documentation after implementing features
