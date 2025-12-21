from flask import Blueprint, request, jsonify
from models.document import Document
from services.search_service import SearchService
from services.lda_service import LDAService
from services.online_crawler import OnlineDocumentCrawler
from routes.auth import token_required

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
    """Search documents by title and find similar documents"""
    try:
        query = request.args.get('query', '').strip()
        include_online = request.args.get('online', 'true').lower() == 'true'
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query is required'
            }), 400
        
        # Search local documents first
        service = get_search_service()
        results = service.search_documents(query, top_k=10)
        
        # Search online if requested
        if include_online:
            online_results = online_crawler.search_online_documents(query, max_results=5)
            
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
        max_results = data.get('max_results', 10, type=int)
        
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
        
        # Load all documents
        documents = Document.get_all_documents()
        
        if len(documents) < num_topics:
            return jsonify({
                'success': False,
                'message': f'Need at least {num_topics} documents to train {num_topics} topics'
            }), 400
        
        # Train LDA model with project saving
        results = lda_service.train_on_documents(
            documents, 
            num_topics=num_topics, 
            project_name=project_name if project_name else None
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
    """Find documents similar to a specific document"""
    try:
        top_k = request.args.get('top_k', 5, type=int)
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
        if not lda_service.lda_model:
            return jsonify({
                'success': False,
                'message': 'LDA model not trained yet. Please train the model first.'
            }), 400
        
        doc_topics = lda_service.get_all_document_topics()
        topics = lda_service.get_topics()
        
        return jsonify({
            'success': True,
            'data': {
                'document_topics': doc_topics,
                'topics': topics,
                'num_documents': len(doc_topics)
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
        document_count = len(Document.get_all_documents())
        
        status = {
            'model_trained': is_trained,
            'document_count': document_count,
            'num_topics': len(lda_service.get_topics()) if is_trained else 0,
            'dictionary_size': len(lda_service.dictionary) if lda_service.dictionary else 0
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