# LDA Topic Modeling — Feature Docs

FastAPI application for LDA topic modeling on Indonesian business news. Implements a full KDD pipeline (Crawl → Preprocess → Transform → Mine) with project management, manual document input, and interactive visualization.

## Feature Docs

| # | Feature | Description |
|---|---------|-------------|
| [01](01-authentication.md) | **Authentication** | JWT register/login, 24h token, bcrypt/PBKDF2 password support |
| [02](02-kdd-pipeline.md) | **KDD Pipeline** | Full 4-stage pipeline from URL crawl to trained LDA model |
| [03](03-project-management.md) | **Project Management** | Create, load, clone, delete LDA projects |
| [04](04-document-management.md) | **Document Management** | Manual text input, bulk creation, edit/delete |
| [05](05-search-similarity.md) | **Search & Similarity** | Keyword + topic-based search, similar docs, model training |
| [06](06-visualization.md) | **Visualization** | Interactive pyLDAvis topic map per project |
| [07](07-indonesian-nlp.md) | **Indonesian NLP** | Preprocessing pipeline: Sastrawi stemming, stopwords, Gensim LDA config |

## Quick API Reference

```
Auth:        POST /api/auth/register  POST /api/auth/login
KDD:         POST /api/kdd/crawl      GET  /api/kdd/status
Projects:    GET  /api/projects/      DELETE /api/projects/{id}/delete
Documents:   POST /api/documents/manual/bulk  GET /api/documents/manual
Search:      GET  /api/search/documents       POST /api/search/train
Vis:         GET  /api/projects/{id}/pyldavis
Health:      GET  /api/health
Swagger UI:  http://localhost:3030/docs
```

## Pages

| URL | Purpose |
|-----|---------|
| `/` | Landing page |
| `/login` | Login |
| `/register` | Register |
| `/admin` | KDD pipeline + project management |
| `/projects` | Project list + document viewer |
| `/manual-input` | Manual document entry |
| `/visualization` | pyLDAvis topic visualization |
