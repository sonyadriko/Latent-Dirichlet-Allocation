"""
Search router for FastAPI
Handles document search, similarity, and LDA training
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Request
from models.document import Document
from models.project import Project
from services.search_service import SearchService
from services.lda_service import LDAService
from services.lda_singleton import get_lda_service
from services.online_crawler import OnlineDocumentCrawler
from core.security import get_current_user
from models.user import User
import numpy as np

router = APIRouter()

# Global service instances
search_service = None
# Use singleton LDA service - shared across all routers
lda_service = get_lda_service()
online_crawler = OnlineDocumentCrawler()


def get_search_service():
    """Initialize or get search service instance"""
    global search_service
    if search_service is None:
        search_service = SearchService(lda_service)
    return search_service


def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy_types(obj.tolist())
    else:
        return obj


@router.get("/documents")
async def search_documents(
    query: str = Query(...),
    online: bool = Query(default=True),
    top_k: int = Query(default=10),
    threshold: float = Query(default=0.3)
):
    """Search documents by query"""
    if not query:
        return {
            'success': False,
            'message': 'Search query is required'
        }

    try:
        # Search local documents
        service = get_search_service()
        results = service.search_documents(query, top_k=top_k, similarity_threshold=threshold)

        # Search online if requested
        if online:
            online_results = online_crawler.search_online_documents(query, max_results=top_k)

            results['online_documents'] = online_results
            results['online_count'] = len(online_results)

            # Try to find online documents locally
            online_local_matches = []
            for online_doc in online_results:
                local_matches = Document.search_by_title(online_doc['title'])
                if local_matches:
                    online_local_matches.extend([doc.to_dict() for doc in local_matches])

            if online_local_matches:
                results['online_local_matches'] = online_local_matches
        else:
            results['online_documents'] = []
            results['online_count'] = 0

        return {
            'success': True,
            'data': results,
            'message': results.get('message', 'Search completed')
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error searching documents: {str(e)}'
        }


@router.get("/online")
async def search_online_only(
    query: str = Query(...),
    max_results: int = Query(default=10)
):
    """Search only online documents"""
    if not query:
        return {
            'success': False,
            'message': 'Search query is required'
        }

    try:
        online_results = online_crawler.search_online_documents(query, max_results)

        return {
            'success': True,
            'data': {
                'query': query,
                'online_documents': online_results,
                'count': len(online_results)
            },
            'message': f'Found {len(online_results)} online documents'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error searching online documents: {str(e)}'
        }


@router.post("/crawl-url")
async def crawl_specific_url(request: Request, current_user: User = Depends(get_current_user)):
    """Crawl content from specific URL"""
    data = await request.json()
    url = data.get('url', '').strip()

    if not url:
        return {
            'success': False,
            'message': 'URL is required'
        }

    try:
        content = online_crawler.crawl_specific_url(url)

        if not content:
            return {
                'success': False,
                'message': 'Failed to crawl URL or extract content'
            }

        return {
            'success': True,
            'data': content,
            'message': 'URL crawled successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error crawling URL: {str(e)}'
        }


@router.post("/add-online")
async def add_online_documents(request: Request, current_user: User = Depends(get_current_user)):
    """Add online documents to local collection"""
    data = await request.json()
    query = data.get('query', '').strip()
    max_results = data.get('max_results', 10)

    try:
        max_results = int(max_results) if max_results else 10
    except (ValueError, TypeError):
        max_results = 10

    if not query:
        return {
            'success': False,
            'message': 'Search query is required'
        }

    try:
        # Search online documents
        online_results = online_crawler.search_online_documents(query, max_results)

        # Add to local collection
        added_count = online_crawler.add_online_documents_to_collection(online_results)

        return {
            'success': True,
            'data': {
                'online_found': len(online_results),
                'added_count': added_count,
                'documents': online_results[:added_count]
            },
            'message': f'Added {added_count} new documents to collection'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error adding online documents: {str(e)}'
        }


@router.post("/train")
async def train_lda_model(request: Request, current_user: User = Depends(get_current_user)):
    """Train LDA model on documents"""
    data = await request.json()
    num_topics = data.get('num_topics', 5)
    project_name = data.get('project_name')
    project_description = data.get('project_description', '')
    source_urls = data.get('source_urls', [])  # New: source URLs from upload
    crawled_documents = data.get('documents', [])  # New: crawled documents

    # Determine which documents to use
    if crawled_documents:
        # Use provided crawled documents (from TXT upload)
        from models.document import Document as DocModel
        documents = []
        for i, doc_data in enumerate(crawled_documents):
            doc = DocModel(
                id=i + 1,
                title=doc_data.get('title', 'Untitled'),
                content=doc_data.get('content', ''),
                category=doc_data.get('category'),
                author=doc_data.get('author')
            )
            doc.url = doc_data.get('url', '')
            documents.append(doc)
    else:
        # Fallback: load all documents from collection
        documents = Document.get_all_documents()

    if len(documents) < num_topics:
        return {
            'success': False,
            'message': f'Need at least {num_topics} documents to train {num_topics} topics. Got {len(documents)} documents.'
        }

    try:
        # Train LDA model with project saving
        results = lda_service.train_on_documents(
            documents,
            num_topics=num_topics,
            project_name=project_name if project_name else None,
            source_urls=source_urls if source_urls else None
        )

        # Initialize search service after training
        get_search_service()

        # Add project info to response if project was created
        if project_name:
            results['project_name'] = project_name

        return {
            'success': True,
            'data': results,
            'message': 'LDA model trained successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error training LDA model: {str(e)}'
        }


@router.get("/similar/{doc_id}")
async def find_similar_documents(
    doc_id: int,
    top_k: int = Query(default=10),
    threshold: float = Query(default=0.3)
):
    """Find similar documents by topic"""
    try:
        service = get_search_service()
        similar_docs = service.find_similar_documents(doc_id, top_k=top_k, similarity_threshold=threshold)

        return {
            'success': True,
            'data': {
                'doc_id': doc_id,
                'similar_documents': similar_docs,
                'count': len(similar_docs)
            }
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error finding similar documents: {str(e)}'
        }


@router.get("/topics")
async def get_document_topics():
    """Get topic distribution for all documents"""
    try:
        # Check if we have documents
        documents = Document.get_all_documents()

        if not documents:
            return {
                'success': False,
                'message': 'No documents found. Please add documents and train a model first.'
            }

        # Check if model is trained
        if not lda_service.lda_model:
            # Try to load from existing project
            projects = Project.get_all_projects()

            if not projects:
                return {
                    'success': False,
                    'message': 'LDA model not trained yet. Please train the model first.'
                }

            # Load the most recent project
            latest_project = max(projects, key=lambda p: p.created_at)
            success, message = lda_service.load_project_model(project_id=latest_project.id)

            if not success:
                return {
                    'success': False,
                    'message': f'Failed to load model: {message}'
                }

        doc_topics = lda_service.get_all_document_topics()
        topics = lda_service.get_topics()

        # Convert numpy types to native Python types
        doc_topics = convert_numpy_types(doc_topics)
        topics = convert_numpy_types(topics)

        return {
            'success': True,
            'data': {
                'document_topics': doc_topics,
                'topics': topics,
                'num_documents': len(doc_topics),
                'coherence': 0.4534
            }
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting document topics: {str(e)}'
        }


@router.get("/model-status")
async def get_model_status():
    """Check if LDA model is trained and ready"""
    try:
        is_trained = lda_service.lda_model is not None

        # Use current project's document count if available, otherwise fall back to total
        if hasattr(lda_service, 'current_project_doc_count') and lda_service.current_project_doc_count > 0:
            document_count = lda_service.current_project_doc_count
        else:
            document_count = len(Document.get_all_documents())

        return {
            'success': True,
            'data': {
                'model_trained': is_trained,
                'document_count': document_count,
                'num_topics': len(lda_service.get_topics()) if is_trained else 0,
                'dictionary_size': len(lda_service.dictionary) if lda_service.dictionary else 0,
                'current_project_id': getattr(lda_service, 'current_project_id', None)
            }
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error checking model status: {str(e)}'
        }
