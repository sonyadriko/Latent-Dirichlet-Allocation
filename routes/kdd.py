from flask import Blueprint, request, jsonify
import json
import os
from config import Config
from services.preprocessing import TextPreprocessor
from services.lda_service import LDAService
from services.crawler import CrawlerService
from routes.auth import token_required

kdd_bp = Blueprint('kdd', __name__)

# Global state for KDD pipeline
kdd_state = {
    'project_name': None,
    'raw_data': None,
    'selected_data': None,
    'preprocessed_data': None,
    'transformed_data': None,
    'lda_results': None,
    'crawl_results': None,
    'status': {
        'crawling': 'pending',
        'selection': 'pending',
        'preprocessing': 'pending',
        'transforming': 'pending',
        'datamining': 'pending'
    }
}

# Initialize services
preprocessor = TextPreprocessor()
lda_service = LDAService()
crawler_service = CrawlerService()

def load_sample_data():
    """Load sample news data"""
    news_file = os.path.join(Config.DATA_DIR, 'news.json')
    if os.path.exists(news_file):
        with open(news_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@kdd_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get KDD Pipeline Status
    ---
    tags:
      - KDD Pipeline
    responses:
      200:
        description: Status pipeline KDD
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            project_name:
              type: string
              example: my_project
              description: Nama project saat ini
            status:
              type: object
              description: Status setiap tahap KDD
              properties:
                crawling:
                  type: string
                  enum: [pending, running, completed, error]
                  example: completed
                selection:
                  type: string
                  example: completed
                preprocessing:
                  type: string
                  example: completed
                transforming:
                  type: string
                  example: completed
                datamining:
                  type: string
                  example: running
            data_count:
              type: object
              properties:
                raw:
                  type: integer
                  example: 50
                selected:
                  type: integer
                  example: 50
                preprocessed:
                  type: integer
                  example: 50
            crawl_results:
              type: object
              properties:
                success_count:
                  type: integer
                  example: 45
                failed_count:
                  type: integer
                  example: 5
    """
    return jsonify({
        'success': True,
        'project_name': kdd_state['project_name'],
        'status': kdd_state['status'],
        'data_count': {
            'raw': len(kdd_state['raw_data']) if kdd_state['raw_data'] else 0,
            'selected': len(kdd_state['selected_data']) if kdd_state['selected_data'] else 0,
            'preprocessed': len(kdd_state['preprocessed_data']) if kdd_state['preprocessed_data'] else 0
        },
        'crawl_results': {
            'success_count': kdd_state['crawl_results']['success_count'] if kdd_state['crawl_results'] else 0,
            'failed_count': kdd_state['crawl_results']['failed_count'] if kdd_state['crawl_results'] else 0
        } if kdd_state['crawl_results'] else None
    }), 200


@kdd_bp.route('/crawl', methods=['POST'])
@token_required
def crawl(current_user):
    """
    Full KDD Pipeline: Crawl, Preprocess, Transform, and LDA Analysis
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: project_name
        type: string
        required: true
        description: Nama project untuk menyimpan hasil
        example: analisa-berita-2024
      - in: formData
        name: file
        type: file
        required: true
        description: File .txt berisi list URL berita (satu URL per baris)
      - in: formData
        name: num_topics
        type: integer
        required: false
        default: 5
        description: Jumlah topik yang akan diekstrak
        example: 5
    responses:
      200:
        description: Proses KDD berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Proses KDD selesai! 45 berita berhasil dianalisis.
            data:
              type: object
              properties:
                project_name:
                  type: string
                  example: analisa-berita-2024
                crawl_stats:
                  type: object
                  properties:
                    total_urls:
                      type: integer
                      example: 50
                    success_count:
                      type: integer
                      example: 45
                    failed_count:
                      type: integer
                      example: 5
                num_topics:
                  type: integer
                  example: 5
                topics:
                  type: array
                  items:
                    type: object
                    properties:
                      topic_id:
                        type: integer
                        example: 0
                      words:
                        type: array
                        items:
                          type: string
                        example: ["ekonomi", "pertumbuhan", "indonesia", "investasi"]
                      weight:
                        type: number
                        format: float
                        example: 0.0234
      400:
        description: Error dalam request atau processing
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Nama project harus diisi
      401:
        description: Unauthorized - Token tidak valid
      500:
        description: Server error
    """
    try:
        # Get project name
        project_name = request.form.get('project_name', '').strip()
        if not project_name:
            return jsonify({
                'success': False,
                'message': 'Nama project harus diisi'
            }), 400

        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan. Upload file .txt berisi link berita.'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang dipilih'
            }), 400

        # Check file extension
        if not file.filename.endswith('.txt'):
            return jsonify({
                'success': False,
                'message': 'File harus berformat .txt'
            }), 400

        # Read file content
        file_content = file.read().decode('utf-8')
        urls = crawler_service.parse_urls_from_file(file_content)

        if not urls:
            return jsonify({
                'success': False,
                'message': 'Tidak ada URL valid ditemukan dalam file'
            }), 400

        # Update state
        kdd_state['project_name'] = project_name
        kdd_state['status']['crawling'] = 'running'

        # ===== STEP 1: CRAWLING =====
        crawl_results = crawler_service.crawl_urls(urls, delay=0.5)
        kdd_state['crawl_results'] = crawl_results

        if crawl_results['success_count'] == 0:
            kdd_state['status']['crawling'] = 'error'
            return jsonify({
                'success': False,
                'message': 'Tidak ada konten berhasil di-crawl',
                'data': {
                    'failed': crawl_results['failed'][:10]
                }
            }), 400

        kdd_state['status']['crawling'] = 'completed'
        kdd_state['raw_data'] = crawl_results['success']
        kdd_state['selected_data'] = crawl_results['success']
        kdd_state['status']['selection'] = 'completed'

        # ===== STEP 2: PREPROCESSING =====
        kdd_state['status']['preprocessing'] = 'running'
        documents = [item['content'] for item in kdd_state['selected_data']]
        preprocessed = preprocessor.preprocess_documents(documents)

        kdd_state['preprocessed_data'] = []
        for i, item in enumerate(kdd_state['selected_data']):
            kdd_state['preprocessed_data'].append({
                'id': item.get('id', i),
                'title': item.get('title', ''),
                'original': item['content'],
                'tokens': preprocessed[i],
                'url': item.get('url', '')
            })
        kdd_state['status']['preprocessing'] = 'completed'

        # ===== STEP 3: TRANSFORMING =====
        kdd_state['status']['transforming'] = 'running'
        preprocessed_docs = [item['tokens'] for item in kdd_state['preprocessed_data']]
        transform_result = lda_service.create_dictionary_and_corpus(preprocessed_docs)

        kdd_state['transformed_data'] = {
            'dictionary_size': transform_result['dictionary_size'],
            'corpus_size': transform_result['corpus_size'],
            'preprocessed_docs': preprocessed_docs
        }
        kdd_state['status']['transforming'] = 'completed'

        # ===== STEP 4: DATA MINING (LDA) =====
        kdd_state['status']['datamining'] = 'running'
        num_topics = int(request.form.get('num_topics', Config.NUM_TOPICS))

        topics = lda_service.train_lda(num_topics=num_topics)
        doc_topics = lda_service.get_all_document_topics()

        try:
            coherence = lda_service.calculate_coherence(preprocessed_docs)
        except Exception:
            coherence = 0.0

        topic_distribution = lda_service.get_topic_distribution()

        # Compile results
        kdd_state['lda_results'] = {
            'project_name': project_name,
            'num_topics': num_topics,
            'topics': topics,
            'document_topics': doc_topics,
            'coherence_score': coherence,
            'topic_distribution': topic_distribution,
            'documents': [
                {
                    'id': d['id'],
                    'title': d['title'],
                    'tokens_count': len(d['tokens']),
                    'url': d.get('url', '')
                }
                for d in kdd_state['preprocessed_data']
            ],
            'crawl_stats': {
                'total_urls': crawl_results['total'],
                'success_count': crawl_results['success_count'],
                'failed_count': crawl_results['failed_count']
            }
        }

        # Save results
        results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
        lda_service.save_results(kdd_state['lda_results'], results_file)

        # Save project data
        project_file = os.path.join(Config.RESULTS_DIR, f'{project_name}_data.json')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump({
                'project_name': project_name,
                'crawled_data': crawl_results['success'],
                'preprocessed_data': kdd_state['preprocessed_data']
            }, f, indent=2, ensure_ascii=False)

        kdd_state['status']['datamining'] = 'completed'

        return jsonify({
            'success': True,
            'message': f'Proses KDD selesai! {crawl_results["success_count"]} berita berhasil dianalisis.',
            'data': {
                'project_name': project_name,
                'crawl_stats': kdd_state['lda_results']['crawl_stats'],
                'num_topics': num_topics,
                'topics': topics
            }
        }), 200

    except Exception as e:
        import traceback
        print(f"Crawling error: {traceback.format_exc()}")
        kdd_state['status']['crawling'] = 'error'
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/upload-and-crawl', methods=['POST'])
@token_required
def upload_and_crawl(current_user):
    """
    Upload dan Crawl URL (Step 1 Only)
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: File .txt berisi list URL berita (satu URL per baris)
    responses:
      200:
        description: Crawling berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Crawling completed successfully
            data:
              type: object
              properties:
                total:
                  type: integer
                  example: 50
                success_count:
                  type: integer
                  example: 45
                failed_count:
                  type: integer
                  example: 5
                sample:
                  type: array
                  items:
                    type: object
                  description: Sample dari hasil crawl
      400:
        description: Error dalam request
      401:
        description: Unauthorized
    """
    try:
        # Get uploaded file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'File tidak ditemukan. Upload file .txt berisi link berita.'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Tidak ada file yang dipilih'
            }), 400

        # Check file extension
        if not file.filename.endswith('.txt'):
            return jsonify({
                'success': False,
                'message': 'File harus berformat .txt'
            }), 400

        # Read file content
        file_content = file.read().decode('utf-8')
        urls = crawler_service.parse_urls_from_file(file_content)

        if not urls:
            return jsonify({
                'success': False,
                'message': 'Tidak ada URL valid ditemukan dalam file'
            }), 400

        # Update state
        kdd_state['status']['crawling'] = 'running'

        # Crawl URLs
        crawl_results = crawler_service.crawl_urls(urls, delay=0.5)
        kdd_state['crawl_results'] = crawl_results

        if crawl_results['success_count'] == 0:
            kdd_state['status']['crawling'] = 'error'
            return jsonify({
                'success': False,
                'message': 'Tidak ada konten berhasil di-crawl',
                'data': {
                    'failed': crawl_results['failed'][:10]
                }
            }), 400

        kdd_state['status']['crawling'] = 'completed'
        kdd_state['raw_data'] = crawl_results['success']
        kdd_state['selected_data'] = crawl_results['success']
        kdd_state['status']['selection'] = 'completed'
        kdd_state['source_urls'] = urls  # Store source URLs

        return jsonify({
            'success': True,
            'message': 'Crawling completed successfully',
            'data': {
                'total': crawl_results['total'],
                'success_count': crawl_results['success_count'],
                'failed_count': crawl_results['failed_count'],
                'source_urls': urls,  # Return source URLs
                'documents': crawl_results['success'],  # Return all crawled documents
                'sample': crawl_results['success'][:3] if crawl_results['success'] else []
            }
        }), 200

    except Exception as e:
        import traceback
        print(f"Upload and crawl error: {traceback.format_exc()}")
        kdd_state['status']['crawling'] = 'error'
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/preprocessing', methods=['POST'])
@token_required
def preprocessing(current_user):
    """
    Step 2: Text Preprocessing
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    responses:
      200:
        description: Preprocessing berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Preprocessing berhasil
            data:
              type: object
              properties:
                total_documents:
                  type: integer
                  example: 45
                sample:
                  type: array
                  items:
                    type: object
                    properties:
                      title:
                        type: string
                      original_length:
                        type: integer
                      tokens_count:
                        type: integer
                      tokens_sample:
                        type: array
                        items:
                          type: string
      400:
        description: Tahap selection harus diselesaikan terlebih dahulu
      401:
        description: Unauthorized
    """
    try:
        if kdd_state['status']['selection'] != 'completed':
            return jsonify({
                'success': False,
                'message': 'Tahap selection harus diselesaikan terlebih dahulu'
            }), 400

        # Extract content from selected data
        documents = [item['content'] for item in kdd_state['selected_data']]

        # Preprocessing
        preprocessed = preprocessor.preprocess_documents(documents)

        # Store preprocessed data with original info
        kdd_state['preprocessed_data'] = []
        for i, item in enumerate(kdd_state['selected_data']):
            kdd_state['preprocessed_data'].append({
                'id': item.get('id', i),
                'title': item.get('title', ''),
                'original': item['content'],
                'tokens': preprocessed[i]
            })

        kdd_state['status']['preprocessing'] = 'completed'

        return jsonify({
            'success': True,
            'message': 'Preprocessing berhasil',
            'data': {
                'total_documents': len(kdd_state['preprocessed_data']),
                'sample': [
                    {
                        'title': d['title'],
                        'original_length': len(d['original']),
                        'tokens_count': len(d['tokens']),
                        'tokens_sample': d['tokens'][:10]
                    }
                    for d in kdd_state['preprocessed_data'][:3]
                ]
            }
        }), 200

    except Exception as e:
        kdd_state['status']['preprocessing'] = 'error'
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/transforming', methods=['POST'])
@token_required
def transforming(current_user):
    """
    Step 3: Bag of Words Transformation
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    responses:
      200:
        description: Transformasi berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Transformasi berhasil
            data:
              type: object
              properties:
                dictionary_size:
                  type: integer
                  example: 1250
                  description: Jumlah unik kata dalam dictionary
                corpus_size:
                  type: integer
                  example: 45
                  description: Jumlah dokumen dalam corpus
                sample_bow:
                  type: array
                  description: Sample bag of words
                  items:
                    type: array
      400:
        description: Tahap preprocessing harus diselesaikan terlebih dahulu
      401:
        description: Unauthorized
    """
    try:
        if kdd_state['status']['preprocessing'] != 'completed':
            return jsonify({
                'success': False,
                'message': 'Tahap preprocessing harus diselesaikan terlebih dahulu'
            }), 400

        # Get preprocessed tokens
        preprocessed_docs = [item['tokens'] for item in kdd_state['preprocessed_data']]

        # Create dictionary and corpus
        transform_result = lda_service.create_dictionary_and_corpus(preprocessed_docs)

        kdd_state['transformed_data'] = {
            'dictionary_size': transform_result['dictionary_size'],
            'corpus_size': transform_result['corpus_size'],
            'preprocessed_docs': preprocessed_docs
        }

        kdd_state['status']['transforming'] = 'completed'

        return jsonify({
            'success': True,
            'message': 'Transformasi berhasil',
            'data': {
                'dictionary_size': transform_result['dictionary_size'],
                'corpus_size': transform_result['corpus_size'],
                'sample_bow': transform_result['sample_bow'][:10] if transform_result['sample_bow'] else []
            }
        }), 200

    except Exception as e:
        kdd_state['status']['transforming'] = 'error'
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/datamining', methods=['POST'])
@token_required
def datamining(current_user):
    """
    Step 4: LDA Topic Modeling
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        description: Parameter untuk LDA training
        required: false
        schema:
          type: object
          properties:
            num_topics:
              type: integer
              default: 5
              example: 5
              description: Jumlah topik yang akan diekstrak
    responses:
      200:
        description: Data mining berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Data mining berhasil
            data:
              type: object
              properties:
                num_topics:
                  type: integer
                  example: 5
                topics:
                  type: array
                  items:
                    type: object
                    properties:
                      topic_id:
                        type: integer
                      words:
                        type: array
                        items:
                          type: string
                      weight:
                        type: number
                document_topics:
                  type: array
                  description: Distribusi topik per dokumen
                coherence_score:
                  type: number
                  format: float
                  description: Koherensi topik (c_v measure)
      400:
        description: Tahap transforming harus diselesaikan terlebih dahulu
      401:
        description: Unauthorized
    """
    try:
        if kdd_state['status']['transforming'] != 'completed':
            return jsonify({
                'success': False,
                'message': 'Tahap transforming harus diselesaikan terlebih dahulu'
            }), 400

        data = request.get_json() or {}
        num_topics = data.get('num_topics', Config.NUM_TOPICS)

        # Recreate dictionary and corpus if lost (due to Flask reloader)
        preprocessed_docs = kdd_state['transformed_data']['preprocessed_docs']
        if lda_service.dictionary is None or lda_service.corpus is None:
            lda_service.create_dictionary_and_corpus(preprocessed_docs)

        # Train LDA model
        topics = lda_service.train_lda(num_topics=num_topics)

        # Get document-topic distribution
        doc_topics = lda_service.get_all_document_topics()

        # Calculate coherence (skip if fails)
        try:
            coherence = lda_service.calculate_coherence(preprocessed_docs)
        except Exception as e:
            print(f"Coherence calculation skipped: {e}")
            coherence = 0.0

        # Get topic distribution
        topic_distribution = lda_service.get_topic_distribution()

        # Compile results
        kdd_state['lda_results'] = {
            'num_topics': num_topics,
            'topics': topics,
            'document_topics': doc_topics,
            'coherence_score': coherence,
            'topic_distribution': topic_distribution,
            'documents': [
                {
                    'id': d['id'],
                    'title': d['title'],
                    'tokens_count': len(d['tokens'])
                }
                for d in kdd_state['preprocessed_data']
            ]
        }

        # Save results
        results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
        lda_service.save_results(kdd_state['lda_results'], results_file)

        kdd_state['status']['datamining'] = 'completed'

        return jsonify({
            'success': True,
            'message': 'Data mining berhasil',
            'data': kdd_state['lda_results']
        }), 200

    except Exception as e:
        import traceback
        print(f"Data mining error: {traceback.format_exc()}")
        kdd_state['status']['datamining'] = 'error'
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/results', methods=['GET'])
def get_results():
    """
    Get LDA Results untuk Visualization
    ---
    tags:
      - KDD Pipeline
    responses:
      200:
        description: Hasil LDA analysis
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                num_topics:
                  type: integer
                  example: 5
                topics:
                  type: array
                  items:
                    type: object
                document_topics:
                  type: array
                coherence_score:
                  type: number
                  format: float
                topic_distribution:
                  type: object
      404:
        description: Hasil LDA belum tersedia
    """
    try:
        # Try to load from file if not in memory
        if kdd_state['lda_results'] is None:
            results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
            kdd_state['lda_results'] = lda_service.load_results(results_file)

        if kdd_state['lda_results'] is None:
            return jsonify({
                'success': False,
                'message': 'Hasil LDA belum tersedia. Silakan jalankan proses data mining terlebih dahulu.'
            }), 404

        return jsonify({
            'success': True,
            'data': kdd_state['lda_results']
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@kdd_bp.route('/reset', methods=['POST'])
@token_required
def reset_pipeline(current_user):
    """
    Reset KDD Pipeline
    ---
    tags:
      - KDD Pipeline
    security:
      - Bearer: []
    responses:
      200:
        description: Pipeline berhasil direset
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Pipeline berhasil direset
      401:
        description: Unauthorized
    """
    global kdd_state
    kdd_state = {
        'project_name': None,
        'raw_data': None,
        'selected_data': None,
        'preprocessed_data': None,
        'transformed_data': None,
        'lda_results': None,
        'crawl_results': None,
        'status': {
            'crawling': 'pending',
            'selection': 'pending',
            'preprocessing': 'pending',
            'transforming': 'pending',
            'datamining': 'pending'
        }
    }

    return jsonify({
        'success': True,
        'message': 'Pipeline berhasil direset'
    }), 200
