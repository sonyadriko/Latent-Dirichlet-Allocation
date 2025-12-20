import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from models.document import Document

class SearchService:
    def __init__(self, lda_service):
        self.lda_service = lda_service
    
    def search_documents(self, query, top_k=10):
        """Search documents by title query"""
        # Find documents matching the query
        matches = Document.search_by_title(query)
        
        if not matches:
            return {
                'query': query,
                'matches': [],
                'message': 'No documents found matching your query'
            }
        
        # Get the best match (exact or first match)
        best_match = matches[0]
        
        # Find similar documents based on topic similarity
        similar_docs = self.find_similar_documents(best_match.id, exclude_self=True, top_k=top_k)
        
        return {
            'query': query,
            'matches': [doc.to_dict() for doc in matches],
            'best_match': best_match.to_dict(),
            'similar_documents': similar_docs,
            'message': f'Found {len(matches)} document(s) matching "{query}"'
        }
    
    def find_similar_documents(self, doc_id, exclude_self=True, top_k=5, similarity_threshold=0.3):
        """Find documents in the same topic cluster"""
        if not self.lda_service.lda_model or not self.lda_service.corpus:
            return []
        
        # Get the target document's topic distribution
        all_docs = Document.get_all_documents()
        target_doc = Document.get_document_by_id(doc_id)
        
        if not target_doc:
            return []
        
        # Preprocess target document and get its topic vector
        preprocessor = self.lda_service.preprocessor if hasattr(self.lda_service, 'preprocessor') else None
        if not preprocessor:
            from services.preprocessing import TextPreprocessor
            preprocessor = TextPreprocessor()
        
        # Get topic distribution for target document
        target_tokens = preprocessor.preprocess(target_doc.content)
        target_bow = self.lda_service.dictionary.doc2bow(target_tokens)
        target_topics = self.lda_service.get_document_topic_vector(target_bow)
        
        # Calculate similarity with all other documents
        similarities = []
        
        for i, doc in enumerate(all_docs):
            if exclude_self and doc.id == doc_id:
                continue
            
            # Get document's topic distribution
            if i < len(self.lda_service.corpus):
                doc_topics = self.lda_service.get_document_topic_vector(self.lda_service.corpus[i])
                similarity = self._calculate_topic_similarity(target_topics, doc_topics)
                
                if similarity >= similarity_threshold:
                    similarities.append({
                        'document': doc.to_dict(),
                        'similarity_score': round(similarity, 3),
                        'dominant_topic': self._get_dominant_topic(doc_topics)
                    })
        
        # Sort by similarity score and return top_k results
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:top_k]
    
    def get_document_topic_vector(self, doc_content):
        """Get topic distribution for a document content"""
        if not self.lda_service.lda_model or not self.lda_service.dictionary:
            return []
        
        # Preprocess document
        from services.preprocessing import TextPreprocessor
        preprocessor = TextPreprocessor()
        tokens = preprocessor.preprocess(doc_content)
        
        # Convert to bag of words
        bow = self.lda_service.dictionary.doc2bow(tokens)
        
        return self.lda_service.get_document_topic_vector(bow)
    
    def _calculate_topic_similarity(self, topics1, topics2):
        """Calculate cosine similarity between two topic distributions"""
        if not topics1 or not topics2:
            return 0.0
        
        # Convert to dense vectors
        max_topics = max(
            max([t[0] for t in topics1], default=0),
            max([t[0] for t in topics2], default=0)
        ) + 1
        
        vec1 = np.zeros(max_topics)
        vec2 = np.zeros(max_topics)
        
        for topic_id, prob in topics1:
            vec1[topic_id] = prob
        
        for topic_id, prob in topics2:
            vec2[topic_id] = prob
        
        # Calculate cosine similarity
        similarity = cosine_similarity([vec1], [vec2])[0][0]
        return similarity
    
    def _get_dominant_topic(self, topics):
        """Get the dominant topic from topic distribution"""
        if not topics:
            return None
        
        dominant = max(topics, key=lambda x: x[1])
        return {
            'topic_id': dominant[0],
            'probability': round(dominant[1], 3)
        }
    
    def build_document_index(self):
        """Build topic vectors for all documents"""
        if not self.lda_service.lda_model:
            return False
        
        documents = Document.get_all_documents()
        
        # Preprocess all documents
        from services.preprocessing import TextPreprocessor
        preprocessor = TextPreprocessor()
        
        preprocessed_docs = []
        for doc in documents:
            tokens = preprocessor.preprocess(doc.content)
            preprocessed_docs.append(tokens)
        
        # Update LDA service with preprocessed documents
        self.lda_service.create_dictionary_and_corpus(preprocessed_docs)
        
        return True