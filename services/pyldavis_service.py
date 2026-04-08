"""
pyLDAvis Service for preparing interactive LDA visualization data
"""
import json
import numpy as np
import pandas as pd
from gensim.models import LdaModel
from gensim import corpora
from config import Config


class PyLDAvisService:
    """
    Service for preparing pyLDAvis visualization data from Gensim LDA models.

    pyLDAvis provides an interactive visualization with:
    - Left panel: Intertopic Distance Map (bubbles = topics, size = topic prevalence)
    - Right panel: Top terms for selected topic with adjustable relevance (lambda) slider
    """

    @staticmethod
    def prepare_data(lda_model, dictionary, corpus, sort_topics=True):
        """
        Prepare pyLDAvis visualization data from Gensim model.

        Args:
            lda_model: Trained Gensim LDA model
            dictionary: Gensim dictionary
            corpus: Corpus in bag-of-words format
            sort_topics: Whether to sort topics by relevance

        Returns:
            Prepared pyLDAvis data object
        """
        try:
            import pyLDAvis.gensim_models as gensimvis
        except ImportError:
            # Fallback for older pyLDAvis versions
            import pyLDAvis.gensim as gensimvis

        vis_data = gensimvis.prepare(
            lda_model,
            corpus,
            dictionary,
            sort_topics=sort_topics
        )
        return vis_data

    @staticmethod
    def get_json_data(vis_data):
        """
        Convert pyLDAvis visualization data to JSON-serializable format.

        Args:
            vis_data: pyLDAvis prepared visualization data

        Returns:
            Dictionary with JSON-serializable visualization data
        """
        return {
            'topic_order': vis_data.topic_order.tolist() if hasattr(vis_data.topic_order, 'tolist') else list(vis_data.topic_order),
            'topic_coordinates': vis_data.topic_coordinates.to_dict(orient='records'),
            'topic_info': vis_data.topic_info.to_dict(orient='records'),
            'token_table': vis_data.token_table.to_dict(orient='records'),
            'R': vis_data.R,
            'lambda_step': vis_data.lambda_step,
            'mds': vis_data.mds if hasattr(vis_data, 'mds') else 'tsne'
        }

    @staticmethod
    def get_html(vis_data, template_type='gensim'):
        """
        Generate HTML for pyLDAvis visualization.

        Args:
            vis_data: pyLDAvis prepared visualization data
            template_type: Template type ('gensim' or 'general')

        Returns:
            HTML string for the visualization
        """
        try:
            import pyLDAvis
            return pyLDAvis.prepare(vis_data, template_type=template_type)
        except Exception as e:
            # Fallback: return basic HTML
            return f'<div class="error">Error generating pyLDAvis HTML: {str(e)}</div>'

    @staticmethod
    def save_html(vis_data, filepath):
        """
        Save pyLDAvis visualization to HTML file.

        Args:
            vis_data: pyLDAvis prepared visualization data
            filepath: Path to save HTML file
        """
        try:
            import pyLDAvis
            html_data = pyLDAvis.save_html(vis_data, filepath)
            return True, "HTML saved successfully"
        except Exception as e:
            return False, f"Error saving HTML: {str(e)}"

    @staticmethod
    def prepare_from_project(project_name):
        """
        Prepare pyLDAvis data from a saved project.

        Args:
            project_name: Name of the project

        Returns:
            Dictionary with visualization data or error
        """
        import os
        from services.lda_service import LDAService

        lda_service = LDAService()
        project_folder = os.path.join(Config.RESULTS_DIR, project_name.replace(' ', '_').lower())
        model_path = os.path.join(project_folder, 'lda_model')

        # Check if model files exist
        if not os.path.exists(model_path + '_model') or not os.path.exists(model_path + '_dict'):
            return {
                'success': False,
                'message': f'Model files not found for project: {project_name}'
            }

        try:
            # Load model and dictionary
            lda_service.load_model(model_path)

            # Check if we need corpus (for visualization)
            # For basic visualization, we can use just the model and dictionary
            # but pyLDAvis requires corpus for full visualization

            return {
                'success': True,
                'message': 'Model loaded successfully. Use prepare_data with corpus for full visualization.'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error loading project: {str(e)}'
            }

    @staticmethod
    def get_topic_terms_data(lda_model, dictionary, num_terms=30):
        """
        Extract topic-term data for visualization.

        Args:
            lda_model: Trained Gensim LDA model
            dictionary: Gensim dictionary
            num_terms: Number of terms per topic

        Returns:
            List of topics with their terms and weights
        """
        topics_data = []

        for topic_id in range(lda_model.num_topics):
            # Get top terms for this topic
            topic_terms = lda_model.show_topic(topic_id, topn=num_terms)

            terms_data = []
            for term, weight in topic_terms:
                terms_data.append({
                    'term': term,
                    'weight': float(weight),
                    'log_lift': float(np.log(weight + 1e-10)),
                    'log_prob': float(np.log(weight))
                })

            topics_data.append({
                'topic_id': topic_id,
                'topic_name': f'Topic {topic_id + 1}',
                'terms': terms_data,
                'frequency': sum(t['weight'] for t in terms_data),
                'term_count': len(terms_data)
            })

        return topics_data

    @staticmethod
    def get_topic_coordinates_data(lda_model, corpus, mds='tsne'):
        """
        Calculate topic coordinates for 2D visualization using MDS.

        Args:
            lda_model: Trained Gensim LDA model
            corpus: Corpus in bag-of-words format
            mds: MDS method ('tsne', 'mmds', 'pcoa')

        Returns:
            DataFrame with topic coordinates
        """
        try:
            from sklearn.manifold import MDS
            from sklearn.decomposition import PCA

            # Get topic-term matrix
            num_topics = lda_model.num_topics
            topic_term_matrix = np.zeros((num_topics, len(lda_model.id2word)))

            for topic_id in range(num_topics):
                for term_id, weight in lda_model.get_topics()[topic_id].nonzero()[0]:
                    topic_term_matrix[topic_id, term_id] = lda_model.get_topics()[topic_id, term_id]

            # Calculate distances
            if mds == 'tsne':
                from sklearn.manifold import TSNE
                coords = TSNE(n_components=2, random_state=42).fit_transform(topic_term_matrix)
            elif mds == 'pcoa':
                coords = PCA(n_components=2, random_state=42).fit_transform(topic_term_matrix)
            else:  # mmds (metric MDS)
                coords = MDS(n_components=2, random_state=42, dissimilarity='precomputed').fit_transform(
                    1 - np.corrcoef(topic_term_matrix)
                )

            # Create DataFrame
            df = pd.DataFrame({
                'topics': [f'Topic {i+1}' for i in range(num_topics)],
                'x': coords[:, 0],
                'y': coords[:, 1],
                'topics_order': list(range(num_topics)),
                'cluster': [1] * num_topics,
                'Freq': [1.0] * num_topics  # Placeholder, will be calculated
            })

            # Calculate topic frequencies from corpus
            topic_dist = np.zeros(num_topics)
            for doc_bow in corpus:
                for topic_id, prob in lda_model.get_document_topics(doc_bow, minimum_probability=0):
                    topic_dist[topic_id] += prob

            df['Freq'] = topic_dist / topic_dist.sum() if topic_dist.sum() > 0 else np.ones(num_topics) / num_topics

            return df

        except Exception as e:
            print(f"Error calculating topic coordinates: {e}")
            # Return simple coordinates as fallback
            num_topics = lda_model.num_topics
            angles = np.linspace(0, 2*np.pi, num_topics, endpoint=False)
            df = pd.DataFrame({
                'topics': [f'Topic {i+1}' for i in range(num_topics)],
                'x': np.cos(angles),
                'y': np.sin(angles),
                'topics_order': list(range(num_topics)),
                'cluster': [1] * num_topics,
                'Freq': [1.0 / num_topics] * num_topics
            })
            return df
