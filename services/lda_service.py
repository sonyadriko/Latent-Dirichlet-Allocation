import json
import os
from gensim import corpora
from gensim.models import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from config import Config

class LDAService:
    def __init__(self):
        self.dictionary = None
        self.corpus = None
        self.lda_model = None
        self.num_topics = Config.NUM_TOPICS
        self.num_words = Config.NUM_WORDS_PER_TOPIC
    
    def create_dictionary_and_corpus(self, preprocessed_docs):
        """Create dictionary and corpus from preprocessed documents"""
        # Create dictionary
        self.dictionary = corpora.Dictionary(preprocessed_docs)
        
        # Filter extremes - adjusted for smaller datasets
        if len(self.dictionary) > 10:
            self.dictionary.filter_extremes(no_below=1, no_above=0.95)
        
        # Create corpus (bag of words)
        self.corpus = [self.dictionary.doc2bow(doc) for doc in preprocessed_docs]
        
        return {
            'dictionary_size': len(self.dictionary),
            'corpus_size': len(self.corpus),
            'sample_bow': self.corpus[0] if self.corpus else []
        }
    
    def train_lda(self, num_topics=None, passes=None, iterations=None):
        """Train LDA model"""
        if self.corpus is None or self.dictionary is None:
            raise ValueError("Dictionary and corpus must be created first")
        
        num_topics = num_topics or self.num_topics
        passes = passes or Config.PASSES
        iterations = iterations or Config.ITERATIONS
        
        self.lda_model = LdaModel(
            corpus=self.corpus,
            id2word=self.dictionary,
            num_topics=num_topics,
            random_state=42,
            update_every=1,
            chunksize=100,
            passes=passes,
            alpha='auto',
            per_word_topics=True,
            iterations=iterations
        )
        
        return self.get_topics()
    
    def get_topics(self):
        """Get topics with top words"""
        if self.lda_model is None:
            return []
        
        topics = []
        for idx, topic in self.lda_model.print_topics(-1, num_words=self.num_words):
            # Parse topic string to get words and weights
            words = []
            parts = topic.split(' + ')
            for part in parts:
                try:
                    weight, word = part.split('*')
                    word = word.strip().strip('"')
                    weight = float(weight.strip())
                    words.append({'word': word, 'weight': round(weight, 4)})
                except:
                    continue
            
            topics.append({
                'topic_id': idx,
                'topic_name': f'Topik {idx + 1}',
                'words': words
            })
        
        return topics
    
    def get_document_topics(self, doc_bow):
        """Get topic distribution for a document"""
        if self.lda_model is None:
            return []
        
        doc_topics = self.lda_model.get_document_topics(doc_bow)
        return [(topic_id, round(prob, 4)) for topic_id, prob in doc_topics]
    
    def get_all_document_topics(self):
        """Get topic distribution for all documents"""
        if self.lda_model is None or self.corpus is None:
            return []
        
        doc_topics = []
        for idx, doc_bow in enumerate(self.corpus):
            topics = self.get_document_topics(doc_bow)
            # Get dominant topic
            if topics:
                dominant = max(topics, key=lambda x: x[1])
                doc_topics.append({
                    'doc_id': idx,
                    'dominant_topic': dominant[0],
                    'dominant_prob': dominant[1],
                    'all_topics': topics
                })
        
        return doc_topics
    
    def calculate_coherence(self, preprocessed_docs):
        """Calculate coherence score"""
        if self.lda_model is None:
            return 0
        
        try:
            coherence_model = CoherenceModel(
                model=self.lda_model,
                texts=preprocessed_docs,
                dictionary=self.dictionary,
                coherence='c_v'
            )
            return round(coherence_model.get_coherence(), 4)
        except Exception as e:
            print(f"Coherence calculation error: {e}")
            return 0
    
    def get_topic_distribution(self):
        """Get distribution of documents across topics"""
        doc_topics = self.get_all_document_topics()
        
        distribution = {}
        for doc in doc_topics:
            topic_id = str(doc['dominant_topic'])  # Convert to string for JSON
            if topic_id not in distribution:
                distribution[topic_id] = 0
            distribution[topic_id] += 1
        
        return distribution
    
    def save_model(self, filepath):
        """Save LDA model and dictionary"""
        if self.lda_model:
            self.lda_model.save(filepath + '_model')
        if self.dictionary:
            self.dictionary.save(filepath + '_dict')
    
    def load_model(self, filepath):
        """Load LDA model and dictionary"""
        if os.path.exists(filepath + '_model'):
            self.lda_model = LdaModel.load(filepath + '_model')
        if os.path.exists(filepath + '_dict'):
            self.dictionary = corpora.Dictionary.load(filepath + '_dict')
    
    def save_results(self, results, filepath):
        """Save results to JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    def load_results(self, filepath):
        """Load results from JSON"""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_document_topic_vector(self, doc_bow):
        """Get full topic distribution vector for a document"""
        if self.lda_model is None:
            return []
        
        # Get topic distribution with minimum probability 0
        doc_topics = self.lda_model.get_document_topics(doc_bow, minimum_probability=0)
        
        # Convert to dense format with all topics
        topic_vector = []
        for topic_id in range(self.lda_model.num_topics):
            # Find probability for this topic
            prob = 0.0
            for tid, p in doc_topics:
                if tid == topic_id:
                    prob = p
                    break
            topic_vector.append((topic_id, round(prob, 4)))
        
        return topic_vector
    
    def train_on_documents(self, documents, num_topics=None):
        """Train LDA model on a list of document objects"""
        from services.preprocessing import TextPreprocessor
        
        # Preprocess documents
        preprocessor = TextPreprocessor()
        self.preprocessor = preprocessor  # Store for later use
        
        preprocessed_docs = []
        doc_contents = [doc.content for doc in documents]
        
        print(f"Preprocessing {len(documents)} documents...")
        preprocessed_docs = preprocessor.preprocess_documents(doc_contents)
        
        # Create dictionary and corpus
        print("Creating dictionary and corpus...")
        self.create_dictionary_and_corpus(preprocessed_docs)
        
        # Train LDA model
        print(f"Training LDA with {num_topics or self.num_topics} topics...")
        topics = self.train_lda(num_topics=num_topics)
        
        # Calculate coherence
        coherence = self.calculate_coherence(preprocessed_docs)
        
        return {
            'num_documents': len(documents),
            'dictionary_size': len(self.dictionary),
            'num_topics': len(topics),
            'coherence_score': coherence,
            'topics': topics
        }
