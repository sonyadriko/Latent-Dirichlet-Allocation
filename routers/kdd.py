"""
KDD Pipeline router for FastAPI
Handles crawling, preprocessing, transforming, and data mining (LDA)
"""
import json
import os
from typing import Optional
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from config import Config
from services.preprocessing import TextPreprocessor
from services.lda_service import LDAService
from services.crawler import CrawlerService
from core.security import get_current_user
from core.state import kdd_state_manager, PipelineStatus
from models.user import User

router = APIRouter()

# Initialize services
preprocessor = TextPreprocessor()
lda_service = LDAService()
crawler_service = CrawlerService()


@router.get("/status")
async def get_status():
    """Get KDD Pipeline Status"""
    state = await kdd_state_manager.get_all()
    data_counts = await kdd_state_manager.get_data_counts()
    crawl_results = await kdd_state_manager.get_crawl_results()

    return {
        'success': True,
        'project_name': state.get('project_name'),
        'status': state['status'],
        'data_count': data_counts,
        'crawl_results': {
            'success_count': crawl_results['success_count'] if crawl_results else 0,
            'failed_count': crawl_results['failed_count'] if crawl_results else 0
        } if crawl_results else None
    }


@router.post("/crawl")
async def crawl(
    current_user: User = Depends(get_current_user),
    project_name: str = Form(...),
    file: UploadFile = File(...),
    num_topics: int = Form(default=Config.NUM_TOPICS)
):
    """Full KDD Pipeline: Crawl, Preprocess, Transform, and LDA Analysis"""
    project_name = project_name.strip()
    if not project_name:
        return {
            'success': False,
            'message': 'Nama project harus diisi'
        }

    # Read file content
    try:
        file_content = await file.read()
        file_text = file_content.decode('utf-8')
    except Exception as e:
        return {
            'success': False,
            'message': f'Gagal membaca file: {str(e)}'
        }

    # Check file extension
    if not file.filename.endswith('.txt'):
        return {
            'success': False,
            'message': 'File harus berformat .txt'
        }

    # Parse URLs from file
    urls = crawler_service.parse_urls_from_file(file_text)
    if not urls:
        return {
            'success': False,
            'message': 'Tidak ada URL valid ditemukan dalam file'
        }

    # Update state
    await kdd_state_manager.set('project_name', project_name)
    await kdd_state_manager.update_status('crawling', PipelineStatus.running)

    try:
        # ===== STEP 1: CRAWLING =====
        crawl_results = crawler_service.crawl_urls(urls, delay=0.5)
        await kdd_state_manager.set('crawl_results', crawl_results)

        if crawl_results['success_count'] == 0:
            await kdd_state_manager.update_status('crawling', PipelineStatus.error)
            return {
                'success': False,
                'message': 'Tidak ada konten berhasil di-crawl'
            }

        await kdd_state_manager.update_status('crawling', PipelineStatus.completed)
        await kdd_state_manager.set('raw_data', crawl_results['success'])
        await kdd_state_manager.set('selected_data', crawl_results['success'])
        await kdd_state_manager.update_status('selection', PipelineStatus.completed)

        # ===== STEP 2: PREPROCESSING =====
        await kdd_state_manager.update_status('preprocessing', PipelineStatus.running)
        documents = [item['content'] for item in crawl_results['success']]
        preprocessed = preprocessor.preprocess_documents(documents)

        preprocessed_data = []
        for i, item in enumerate(crawl_results['success']):
            preprocessed_data.append({
                'id': item.get('id', i),
                'title': item.get('title', ''),
                'original': item['content'],
                'tokens': preprocessed[i],
                'url': item.get('url', '')
            })

        await kdd_state_manager.set('preprocessed_data', preprocessed_data)
        await kdd_state_manager.update_status('preprocessing', PipelineStatus.completed)

        # ===== STEP 3: TRANSFORMING =====
        await kdd_state_manager.update_status('transforming', PipelineStatus.running)
        preprocessed_docs = [item['tokens'] for item in preprocessed_data]
        transform_result = lda_service.create_dictionary_and_corpus(preprocessed_docs)

        await kdd_state_manager.set('transformed_data', {
            'dictionary_size': transform_result['dictionary_size'],
            'corpus_size': transform_result['corpus_size'],
            'preprocessed_docs': preprocessed_docs
        })
        await kdd_state_manager.update_status('transforming', PipelineStatus.completed)

        # ===== STEP 4: DATA MINING (LDA) =====
        await kdd_state_manager.update_status('datamining', PipelineStatus.running)

        topics = lda_service.train_lda(num_topics=num_topics)
        doc_topics = lda_service.get_all_document_topics()

        try:
            coherence = lda_service.calculate_coherence(preprocessed_docs)
        except Exception:
            coherence = 0.0

        topic_distribution = lda_service.get_topic_distribution()

        # Compile results
        lda_results = {
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
                for d in preprocessed_data
            ],
            'crawl_stats': {
                'total_urls': crawl_results['total'],
                'success_count': crawl_results['success_count'],
                'failed_count': crawl_results['failed_count']
            }
        }

        # Save results
        results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
        lda_service.save_results(lda_results, results_file)

        # Save project data
        project_file = os.path.join(Config.RESULTS_DIR, f'{project_name}_data.json')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump({
                'project_name': project_name,
                'crawled_data': crawl_results['success'],
                'preprocessed_data': preprocessed_data
            }, f, indent=2, ensure_ascii=False)

        await kdd_state_manager.set('lda_results', lda_results)
        await kdd_state_manager.update_status('datamining', PipelineStatus.completed)

        return {
            'success': True,
            'message': f'Proses KDD selesai! {crawl_results["success_count"]} berita berhasil dianalisis.',
            'data': {
                'project_name': project_name,
                'crawl_stats': lda_results['crawl_stats'],
                'num_topics': num_topics,
                'topics': topics
            }
        }

    except Exception as e:
        await kdd_state_manager.update_status('crawling', PipelineStatus.error)
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.post("/upload-and-crawl")
async def upload_and_crawl(
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """Upload and Crawl URL (Step 1 Only)"""
    # Read file content
    try:
        file_content = await file.read()
        file_text = file_content.decode('utf-8')
    except Exception as e:
        return {
            'success': False,
            'message': f'Gagal membaca file: {str(e)}'
        }

    # Check file extension
    if not file.filename.endswith('.txt'):
        return {
            'success': False,
            'message': 'File harus berformat .txt'
        }

    # Parse URLs from file
    urls = crawler_service.parse_urls_from_file(file_text)
    if not urls:
        return {
            'success': False,
            'message': 'Tidak ada URL valid ditemukan dalam file'
        }

    # Update state
    await kdd_state_manager.update_status('crawling', PipelineStatus.running)

    try:
        # Crawl URLs
        crawl_results = crawler_service.crawl_urls(urls, delay=0.5)
        await kdd_state_manager.set('crawl_results', crawl_results)

        if crawl_results['success_count'] == 0:
            await kdd_state_manager.update_status('crawling', PipelineStatus.error)
            return {
                'success': False,
                'message': 'Tidak ada konten berhasil di-crawl'
            }

        await kdd_state_manager.update_status('crawling', PipelineStatus.completed)
        await kdd_state_manager.set('raw_data', crawl_results['success'])
        await kdd_state_manager.set('selected_data', crawl_results['success'])
        await kdd_state_manager.set('source_urls', urls)  # Store source URLs
        await kdd_state_manager.update_status('selection', PipelineStatus.completed)

        return {
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
        }

    except Exception as e:
        await kdd_state_manager.update_status('crawling', PipelineStatus.error)
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.post("/preprocessing")
async def preprocessing(current_user: User = Depends(get_current_user)):
    """Step 2: Text Preprocessing"""
    status = await kdd_state_manager.get_status('selection')
    if status != PipelineStatus.completed:
        return {
            'success': False,
            'message': 'Tahap selection harus diselesaikan terlebih dahulu'
        }

    try:
        selected_data = await kdd_state_manager.get('selected_data')
        documents = [item['content'] for item in selected_data]

        # Preprocessing
        preprocessed = preprocessor.preprocess_documents(documents)

        # Store preprocessed data with original info
        preprocessed_data = []
        for i, item in enumerate(selected_data):
            preprocessed_data.append({
                'id': item.get('id', i),
                'title': item.get('title', ''),
                'original': item['content'],
                'tokens': preprocessed[i]
            })

        await kdd_state_manager.set('preprocessed_data', preprocessed_data)
        await kdd_state_manager.update_status('preprocessing', PipelineStatus.completed)

        sample = [
            {
                'title': d['title'],
                'original_length': len(d['original']),
                'tokens_count': len(d['tokens']),
                'tokens_sample': d['tokens'][:10]
            }
            for d in preprocessed_data[:3]
        ]

        return {
            'success': True,
            'message': 'Preprocessing berhasil',
            'data': {
                'total_documents': len(preprocessed_data),
                'sample': sample
            }
        }

    except Exception as e:
        await kdd_state_manager.update_status('preprocessing', PipelineStatus.error)
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.post("/transforming")
async def transforming(current_user: User = Depends(get_current_user)):
    """Step 3: Bag of Words Transformation"""
    status = await kdd_state_manager.get_status('preprocessing')
    if status != PipelineStatus.completed:
        return {
            'success': False,
            'message': 'Tahap preprocessing harus diselesaikan terlebih dahulu'
        }

    try:
        preprocessed_data = await kdd_state_manager.get('preprocessed_data')
        preprocessed_docs = [item['tokens'] for item in preprocessed_data]

        # Create dictionary and corpus
        transform_result = lda_service.create_dictionary_and_corpus(preprocessed_docs)

        await kdd_state_manager.set('transformed_data', {
            'dictionary_size': transform_result['dictionary_size'],
            'corpus_size': transform_result['corpus_size'],
            'preprocessed_docs': preprocessed_docs
        })
        await kdd_state_manager.update_status('transforming', PipelineStatus.completed)

        return {
            'success': True,
            'message': 'Transformasi berhasil',
            'data': {
                'dictionary_size': transform_result['dictionary_size'],
                'corpus_size': transform_result['corpus_size'],
                'sample_bow': transform_result['sample_bow'][:10] if transform_result.get('sample_bow') else []
            }
        }

    except Exception as e:
        await kdd_state_manager.update_status('transforming', PipelineStatus.error)
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.post("/datamining")
async def datamining(request: Request, current_user: User = Depends(get_current_user)):
    """Step 4: LDA Topic Modeling"""
    data = await request.json() or {}
    num_topics = data.get('num_topics', Config.NUM_TOPICS)

    status = await kdd_state_manager.get_status('transforming')
    if status != PipelineStatus.completed:
        return {
            'success': False,
            'message': 'Tahap transforming harus diselesaikan terlebih dahulu'
        }

    try:
        # Get transformed data
        transformed_data = await kdd_state_manager.get('transformed_data')
        preprocessed_docs = transformed_data['preprocessed_docs']

        # Recreate dictionary and corpus if needed
        if lda_service.dictionary is None or lda_service.corpus is None:
            lda_service.create_dictionary_and_corpus(preprocessed_docs)

        # Train LDA model
        topics = lda_service.train_lda(num_topics=num_topics)

        # Get document-topic distribution
        doc_topics = lda_service.get_all_document_topics()

        # Calculate coherence
        try:
            coherence = lda_service.calculate_coherence(preprocessed_docs)
        except Exception as e:
            print(f"Coherence calculation skipped: {e}")
            coherence = 0.0

        # Get topic distribution
        topic_distribution = lda_service.get_topic_distribution()

        # Get preprocessed data for document info
        preprocessed_data = await kdd_state_manager.get('preprocessed_data')

        # Compile results
        lda_results = {
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
                for d in preprocessed_data
            ]
        }

        # Save results
        results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
        lda_service.save_results(lda_results, results_file)

        await kdd_state_manager.set('lda_results', lda_results)
        await kdd_state_manager.update_status('datamining', PipelineStatus.completed)

        return {
            'success': True,
            'message': 'Data mining berhasil',
            'data': lda_results
        }

    except Exception as e:
        await kdd_state_manager.update_status('datamining', PipelineStatus.error)
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.get("/results")
async def get_results():
    """Get LDA Results for Visualization"""
    try:
        # Try to load from state
        lda_results = await kdd_state_manager.get('lda_results')

        # If not in state, try loading from file
        if lda_results is None:
            results_file = os.path.join(Config.RESULTS_DIR, 'lda_results.json')
            lda_results = lda_service.load_results(results_file)
            await kdd_state_manager.set('lda_results', lda_results)

        if lda_results is None:
            return {
                'success': False,
                'message': 'Hasil LDA belum tersedia. Silakan jalankan proses data mining terlebih dahulu.'
            }

        return {
            'success': True,
            'data': lda_results
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error: {str(e)}'
        }


@router.post("/reset")
async def reset_pipeline(current_user: User = Depends(get_current_user)):
    """Reset KDD Pipeline"""
    await kdd_state_manager.reset()
    return {
        'success': True,
        'message': 'Pipeline berhasil direset'
    }


@router.get("/pyldavis")
async def get_pyldavis():
    """
    Get pyLDAvis visualization data for the current KDD pipeline results.

    Returns JSON data compatible with pyLDAvis JavaScript visualization.
    """
    try:
        # Check if LDA model exists in service
        if lda_service.lda_model is None:
            return {
                'success': False,
                'message': 'LDA model not trained yet. Please complete the data mining step first.'
            }

        # Get corpus from state
        transformed_data = await kdd_state_manager.get('transformed_data')

        if transformed_data is None:
            return {
                'success': False,
                'message': 'Transformed data not available. Please complete the transforming step first.'
            }

        # Prepare pyLDAvis data
        pyldavis_data = lda_service.get_pyldavis_data()

        if pyldavis_data is None:
            return {
                'success': False,
                'message': 'Failed to prepare pyLDAvis visualization data.'
            }

        return {
            'success': True,
            'data': pyldavis_data,
            'message': 'pyLDAvis data prepared successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error preparing pyLDAvis data: {str(e)}'
        }
