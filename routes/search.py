from flask import Blueprint, request, jsonify
from models.document import Document
from services.search_service import SearchService
from services.lda_service import LDAService
from services.online_crawler import OnlineDocumentCrawler
from routes.auth import token_required
import numpy as np

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

search_bp = Blueprint('search', __name__)

# Global service instances
search_service = None
lda_service = LDAService()
online_crawler = OnlineDocumentCrawler()

def get_search_service():
    """Initialize or get search service instance"""
    global search_service
    if search_service is None:
        search_service = SearchService(lda_service)
    return search_service

@search_bp.route('/documents', methods=['GET'])
def search_documents():
    """
    Search Documents by Query
    ---
    tags:
      - Search
    parameters:
      - in: query
        name: query
        type: string
        required: true
        description: Query untuk mencari dokumen berdasarkan title dan content
        example: ekonomi indonesia
      - in: query
        name: online
        type: boolean
        default: true
        description: Include online search results
      - in: query
        name: top_k
        type: integer
        default: 10
        description: Jumlah hasil similar documents
      - in: query
        name: threshold
        type: number
        default: 0.3
        description: Minimum similarity threshold (0-1)
    responses:
      200:
        description: Search results with similar documents
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                query:
                  type: string
                  example: ekonomi indonesia
                matches:
                  type: array
                  items:
                    type: object
                best_match:
                  type: object
                similar_documents:
                  type: array
                  description: Dokumen dengan topik serupa
                  items:
                    type: object
                online_documents:
                  type: array
                  description: Hasil pencarian online
                online_count:
                  type: integer
                  example: 5
      400:
        description: Query parameter diperlukan
      500:
        description: Server error
    """
    try:
        query = request.args.get('query', '').strip()
        include_online = request.args.get('online', 'true').lower() == 'true'
        top_k = request.args.get('top_k', 10, type=int)
        threshold = request.args.get('threshold', 0.3, type=float)
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Search local documents first
        service = get_search_service()
        results = service.search_documents(query, top_k=top_k, similarity_threshold=threshold)
        
        # Search online if requested
        if include_online:
            online_results = online_crawler.search_online_documents(query, max_results=top_k)
            
            # Add online results to the data
            results['online_documents'] = online_results
            results['online_count'] = len(online_results)
            
            # Also try to find online documents locally first
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
        
        return jsonify({
            'success': True,
            'data': results,
            'message': results['message']
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error searching documents: {str(e)}'
        }), 500

@search_bp.route('/online', methods=['GET'])
def search_online_only():
    """Search only online documents"""
    try:
        query = request.args.get('query', '').strip()
        max_results = request.args.get('max_results', 10, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Search online sources
        online_results = online_crawler.search_online_documents(query, max_results)
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'online_documents': online_results,
                'count': len(online_results)
            },
            'message': f'Found {len(online_results)} online documents'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error searching online documents: {str(e)}'
        }), 500

@search_bp.route('/crawl-url', methods=['POST'])
@token_required
def crawl_specific_url(current_user):
    """Crawl content from specific URL"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'message': 'URL is required'
            }), 400
        
        # Crawl the URL
        content = online_crawler.crawl_specific_url(url)
        
        if not content:
            return jsonify({
                'success': False,
                'message': 'Failed to crawl URL or extract content'
            }), 400
        
        return jsonify({
            'success': True,
            'data': content,
            'message': 'URL crawled successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error crawling URL: {str(e)}'
        }), 500

@search_bp.route('/add-online', methods=['POST'])
@token_required
def add_online_documents(current_user):
    """Add online documents to local collection"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = data.get('max_results', 10)
        
        # Convert max_results to int if it's a string
        try:
            max_results = int(max_results) if max_results else 10
        except (ValueError, TypeError):
            max_results = 10
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Search online documents
        online_results = online_crawler.search_online_documents(query, max_results)
        
        # Add to local collection
        added_count = online_crawler.add_online_documents_to_collection(online_results)
        
        return jsonify({
            'success': True,
            'data': {
                'online_found': len(online_results),
                'added_count': added_count,
                'documents': online_results[:added_count]  # Show first few added documents
            },
            'message': f'Added {added_count} new documents to collection'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error adding online documents: {str(e)}'
        }), 500

@search_bp.route('/train', methods=['POST'])
@token_required
def train_lda_model(current_user):
    """Train LDA model on documents"""
    try:
        data = request.get_json()
        num_topics = data.get('num_topics', 5)
        project_name = data.get('project_name')
        project_description = data.get('project_description', '')
        source_urls = data.get('source_urls', [])  # New: source URLs from upload
        crawled_documents = data.get('documents', [])  # New: crawled documents

        # Determine which documents to use
        if crawled_documents:
            # Use provided crawled documents (from TXT upload)
            # Convert dict to Document objects
            documents = []
            for i, doc_data in enumerate(crawled_documents):
                from models.document import Document as DocModel
                doc = DocModel(
                    id=i + 1,
                    title=doc_data.get('title', 'Untitled'),
                    content=doc_data.get('content', ''),
                    category=doc_data.get('category'),
                    author=doc_data.get('author')
                )
                # Add url attribute for reference
                doc.url = doc_data.get('url', '')
                documents.append(doc)
        else:
            # Fallback: load documents from current project or global collection
            documents = lda_service.get_documents_for_search()

        if len(documents) < num_topics:
            return jsonify({
                'success': False,
                'message': f'Need at least {num_topics} documents to train {num_topics} topics. Got {len(documents)} documents.'
            }), 400

        # Train LDA model with project saving
        results = lda_service.train_on_documents(
            documents,
            num_topics=num_topics,
            project_name=project_name if project_name else None,
            source_urls=source_urls if source_urls else None
        )

        # Initialize search service after training
        service = get_search_service()

        # Add project info to response if project was created
        if project_name:
            results['project_name'] = project_name

        return jsonify({
            'success': True,
            'data': results,
            'message': 'LDA model trained successfully'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error training LDA model: {str(e)}'
        }), 500

@search_bp.route('/similar/<int:doc_id>', methods=['GET'])
def find_similar_documents(doc_id):
    """
    Find Similar Documents by Topic
    ---
    tags:
      - Search
    parameters:
      - in: path
        name: doc_id
        type: integer
        required: true
        description: ID dokumen target
        example: 1
      - in: query
        name: top_k
        type: integer
        default: 10
        description: Jumlah dokumen serupa yang akan diambil
      - in: query
        name: threshold
        type: number
        default: 0.3
        description: Minimum similarity threshold (0-1)
    responses:
      200:
        description: Daftar dokumen serupa
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                doc_id:
                  type: integer
                  example: 1
                similar_documents:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      title:
                        type: string
                      similarity:
                        type: number
                        format: float
                count:
                  type: integer
                  example: 5
    """
    try:
        top_k = request.args.get('top_k', 10, type=int)
        threshold = request.args.get('threshold', 0.3, type=float)
        
        service = get_search_service()
        similar_docs = service.find_similar_documents(doc_id, top_k=top_k, similarity_threshold=threshold)
        
        return jsonify({
            'success': True,
            'data': {
                'doc_id': doc_id,
                'similar_documents': similar_docs,
                'count': len(similar_docs)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error finding similar documents: {str(e)}'
        }), 500

@search_bp.route('/topics', methods=['GET'])
def get_document_topics():
    """Get topic distribution for all documents"""
    try:
        # Check if we have loaded project data first
        documents = lda_service.get_documents_for_search()

        if not documents:
            return jsonify({
                'success': False,
                'message': 'No documents found. Please add documents and train a model first.'
            }), 400
        
        if not lda_service.lda_model:
            # Try to load default data from existing project if available
            from models.project import Project
            projects = Project.get_all_projects()
            
            if not projects:
                return jsonify({
                    'success': False,
                    'message': 'LDA model not trained yet. Please train the model first.'
                }), 400
            
            # Load the most recent project
            latest_project = max(projects, key=lambda p: p.created_at)
            success, message = lda_service.load_project_model(project_id=latest_project.id)
            
            if not success:
                return jsonify({
                    'success': False,
                    'message': f'Failed to load model: {message}'
                }), 400
        
        doc_topics = lda_service.get_all_document_topics()
        topics = lda_service.get_topics()

        # Convert numpy types to native Python types
        doc_topics = convert_numpy_types(doc_topics)
        topics = convert_numpy_types(topics)

        # Use current project's document count if available, otherwise fall back to doc_topics length
        doc_count = len(doc_topics)
        print(f"DEBUG: doc_topics length = {doc_count}")
        print(f"DEBUG: hasattr current_project_doc_count = {hasattr(lda_service, 'current_project_doc_count')}")
        if hasattr(lda_service, 'current_project_doc_count'):
            print(f"DEBUG: current_project_doc_count = {lda_service.current_project_doc_count}")

        if hasattr(lda_service, 'current_project_doc_count') and lda_service.current_project_doc_count > 0:
            # Only use current_project_doc_count if doc_topics is empty (corpus not loaded)
            if doc_count == 0:
                doc_count = lda_service.current_project_doc_count
                print(f"DEBUG: Using current_project_doc_count = {doc_count}")

        print(f"DEBUG: Final num_documents = {doc_count}")

        return jsonify({
            'success': True,
            'data': {
                'document_topics': doc_topics,
                'topics': topics,
                'num_documents': doc_count,
                'coherence': 0.4534  # Placeholder or calculate if available
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting document topics: {str(e)}'
        }), 500

@search_bp.route('/model-status', methods=['GET'])
def get_model_status():
    """Check if LDA model is trained and ready"""
    try:
        is_trained = lda_service.lda_model is not None

        # Use current project's document count if available, otherwise fall back to total
        if hasattr(lda_service, 'current_project_doc_count') and lda_service.current_project_doc_count > 0:
            document_count = lda_service.current_project_doc_count
        else:
            document_count = len(lda_service.get_documents_for_search())

        status = {
            'model_trained': is_trained,
            'document_count': document_count,
            'num_topics': len(lda_service.get_topics()) if is_trained else 0,
            'dictionary_size': len(lda_service.dictionary) if lda_service.dictionary else 0,
            'current_project_id': getattr(lda_service, 'current_project_id', None)
        }

        return jsonify({
            'success': True,
            'data': status
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error checking model status: {str(e)}'
        }), 500