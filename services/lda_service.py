import json
import os
from datetime import datetime
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
        self.current_project_id = None  # Track currently loaded project
        self.current_project_doc_count = 0  # Track document count for current project
        self.current_project_documents = []  # Store current project documents for search
    
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
        """Save LDA model, dictionary, and corpus"""
        if self.lda_model:
            self.lda_model.save(filepath + '_model')
        if self.dictionary:
            self.dictionary.save(filepath + '_dict')
        if self.corpus:
            # Save corpus using corpora.MmCorpus for efficient storage
            corpora.MmCorpus.serialize(filepath + '_mm', self.corpus)
    
    def load_model(self, filepath):
        """Load LDA model, dictionary, and corpus

        Note: For backward compatibility, corpus loading is optional.
        Projects trained before this fix may not have corpus files (.mm).
        Such projects will need to be retrained to save corpus properly.
        """
        if os.path.exists(filepath + '_model'):
            self.lda_model = LdaModel.load(filepath + '_model')
        if os.path.exists(filepath + '_dict'):
            self.dictionary = corpora.Dictionary.load(filepath + '_dict')
        if os.path.exists(filepath + '_mm'):
            # Load corpus from Matrix Market format
            self.corpus = corpora.MmCorpus(filepath + '_mm')
        else:
            # Warning: corpus not found - visualization may show incorrect data
            print(f"Warning: Corpus file not found for {filepath}. Retrain project to fix this.")
    
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
    
    def train_on_documents(self, documents, num_topics=None, project_name=None, save_model=True,
                          source_urls=None):
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
        actual_num_topics = num_topics or self.num_topics
        print(f"Training LDA with {actual_num_topics} topics...")
        topics = self.train_lda(num_topics=actual_num_topics)

        # Calculate coherence
        coherence = self.calculate_coherence(preprocessed_docs)

        # Prepare document data for saving (minimal info)
        documents_data = [
            {
                'id': doc.id if hasattr(doc, 'id') else i,
                'title': doc.title,
                'url': doc.url if hasattr(doc, 'url') else None,
                'content_preview': doc.content[:200] if len(doc.content) > 200 else doc.content
            }
            for i, doc in enumerate(documents)
        ]

        result = {
            'num_documents': len(documents),
            'dictionary_size': len(self.dictionary),
            'num_topics': len(topics),
            'coherence_score': coherence,
            'topics': topics,
            'documents_data': documents_data
        }

        # Save model if project name is provided
        if save_model and project_name:
            model_path = self.save_project_model(
                project_name, coherence, len(documents), actual_num_topics,
                source_urls=source_urls or [],
                documents_data=documents_data
            )
            result['model_path'] = model_path

        return result
    
    def save_project_model(self, project_name, coherence_score, doc_count, num_topics,
                          source_urls=None, documents_data=None):
        """Save trained model for a specific project"""
        from models.project import Project

        # Create project folder
        project_folder = os.path.join(Config.RESULTS_DIR, project_name.replace(' ', '_').lower())
        os.makedirs(project_folder, exist_ok=True)

        # Save model and dictionary
        model_path = os.path.join(project_folder, 'lda_model')
        self.save_model(model_path)

        # Save results with documents info
        results_file = os.path.join(project_folder, 'results.json')
        results = {
            'project_name': project_name,
            'coherence_score': coherence_score,
            'document_count': doc_count,
            'num_topics': num_topics,
            'topics': self.get_topics(),
            'training_date': datetime.now().isoformat(),
            'source_urls': source_urls or [],
            'documents': documents_data or []
        }
        self.save_results(results, results_file)

        # Save documents data separately for easy access
        documents_file = os.path.join(project_folder, 'documents.json')
        with open(documents_file, 'w', encoding='utf-8') as f:
            json.dump(documents_data or [], f, indent=2, ensure_ascii=False)

        # Save source URLs separately for easy access
        urls_file = os.path.join(project_folder, 'source_urls.txt')
        with open(urls_file, 'w', encoding='utf-8') as f:
            for url in source_urls or []:
                f.write(url + '\n')

        # Create project record
        try:
            project, error = Project.create(
                name=project_name,
                description=f"LDA model with {num_topics} topics on {doc_count} documents",
                num_topics=num_topics,
                document_count=doc_count,
                coherence_score=coherence_score,
                source_urls=source_urls or [],
                documents=documents_data or []
            )

            if project:
                return project.model_path
        except Exception as e:
            print(f"Error creating project record: {e}")

        return model_path
    
    def load_project_model(self, project_id=None, project_name=None):
        """Load trained model for a specific project"""
        from models.project import Project
        from services.preprocessing import TextPreprocessor

        try:
            # Get project by ID or name
            if project_id:
                project = Project.get_project_by_id(project_id)
            elif project_name:
                project = Project.get_project_by_name(project_name)
            else:
                return False, "Project ID or name is required"

            if not project:
                return False, "Project not found"

            # Build model path
            project_folder = os.path.join(Config.RESULTS_DIR, project.name.replace(' ', '_').lower())
            model_path = os.path.join(project_folder, 'lda_model')

            # Load model
            if os.path.exists(model_path + '_model') and os.path.exists(model_path + '_dict'):
                self.load_model(model_path)

                # Track current project for proper document count
                self.current_project_id = project.id
                self.current_project_doc_count = project.document_count

                # Store project documents for search functionality
                self.current_project_documents = project.documents or []

                # If no documents in metadata, try loading from project folder
                if not self.current_project_documents:
                    project_documents_file = os.path.join(project_folder, 'documents.json')
                    if os.path.exists(project_documents_file):
                        with open(project_documents_file, 'r', encoding='utf-8') as f:
                            self.current_project_documents = json.load(f)

                # Rebuild corpus if not loaded (for backward compatibility)
                if self.corpus is None:
                    print(f"Rebuilding corpus for project: {project.name}")
                    print(f"  project.documents exists: {bool(project.documents)}")
                    print(f"  project.document_count: {project.document_count}")
                    try:
                        preprocessor = TextPreprocessor()
                        doc_contents = []

                        # Try to get documents from project metadata first
                        if project.documents:
                            print(f"  Using project.documents ({len(project.documents)} items)")
                            # Handle both 'content' and 'content_preview' fields
                            doc_contents = [doc.get('content') or doc.get('content_preview', '') for doc in project.documents]
                            doc_contents = [c for c in doc_contents if c]  # Filter out empty
                            print(f"  Extracted {len(doc_contents)} contents from project.documents")
                        else:
                            # Fallback 1: try to load from project folder's documents.json
                            project_folder = os.path.join(Config.RESULTS_DIR, project.name.replace(' ', '_').lower())
                            project_documents_file = os.path.join(project_folder, 'documents.json')
                            print(f"  project.documents is empty, trying project folder documents.json")
                            print(f"  project documents.json path: {project_documents_file}")
                            print(f"  project documents.json exists: {os.path.exists(project_documents_file)}")
                            if os.path.exists(project_documents_file):
                                with open(project_documents_file, 'r', encoding='utf-8') as f:
                                    project_docs = json.load(f)
                                print(f"  Loaded {len(project_docs)} docs from project documents.json")
                                # Use content_preview from project documents
                                doc_contents = [doc.get('content') or doc.get('content_preview', '') for doc in project_docs]
                                doc_contents = [c for c in doc_contents if c]  # Filter out empty
                                print(f"  Using {len(doc_contents)} documents from project documents.json")
                            else:
                                # Fallback 2: try to load from global documents.json
                                print(f"  project documents.json NOT FOUND, trying global documents.json")
                                documents_file = os.path.join(Config.DATA_DIR, 'documents.json')
                                print(f"  global documents.json path: {documents_file}")
                                print(f"  global documents.json exists: {os.path.exists(documents_file)}")
                                if os.path.exists(documents_file):
                                    with open(documents_file, 'r', encoding='utf-8') as f:
                                        all_docs = json.load(f)
                                    print(f"  Loaded {len(all_docs)} docs from global documents.json")
                                    # Use the first N documents matching the project's document count
                                    doc_contents = [doc.get('content', '') for doc in all_docs[:project.document_count] if doc.get('content')]
                                    print(f"  Using {len(doc_contents)} documents from global documents.json")
                                else:
                                    print(f"  global documents.json NOT FOUND!")

                        print(f"  Final doc_contents length: {len(doc_contents)}")

                        if doc_contents:
                            print(f"  Preprocessing {len(doc_contents)} documents...")
                            # Preprocess
                            preprocessed_docs = preprocessor.preprocess_documents(doc_contents)
                            print(f"  Preprocessed {len(preprocessed_docs)} docs")

                            # Rebuild corpus using existing dictionary
                            print(f"  Building corpus with dictionary (vocab size: {len(self.dictionary)})")
                            self.corpus = [self.dictionary.doc2bow(doc) for doc in preprocessed_docs]
                            print(f"  Corpus built: {len(self.corpus)} docs")

                            # Save corpus for future use
                            print(f"  Saving corpus to {model_path}_mm")
                            corpora.MmCorpus.serialize(model_path + '_mm', self.corpus)
                            print(f"Corpus rebuilt ({len(self.corpus)} docs) and saved for {project.name}")
                        else:
                            print(f"ERROR: No doc_contents available!")
                    except Exception as e:
                        print(f"Warning: Could not rebuild corpus: {e}")
                        import traceback
                        traceback.print_exc()

                return True, f"Successfully loaded project: {project.name}"
            else:
                return False, "Model files not found for this project"

        except Exception as e:
            return False, f"Error loading project model: {str(e)}"
    
    def get_available_projects(self):
        """Get list of all available projects"""
        from models.project import Project
        
        try:
            projects = Project.get_all_projects()
            return [p.to_dict() for p in projects]
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
    
    def switch_to_project(self, project_id):
        """Switch to a specific project model"""
        success, message = self.load_project_model(project_id=project_id)
        return success, message

    def get_documents_for_search(self):
        """Get documents for search -优先使用当前项目文档"""
        if self.current_project_documents:
            from models.document import Document
            return [
                Document(
                    id=doc.get('id', i),
                    title=doc.get('title', 'Untitled'),
                    content=doc.get('content') or doc.get('content_preview', ''),
                    category=doc.get('category'),
                    author=doc.get('author')
                )
                for i, doc in enumerate(self.current_project_documents)
            ]
        # Fallback to global documents
        from models.document import Document
        return Document.get_all_documents()

    def get_pyldavis_data(self, corpus=None, sort_topics=True):
        """
        Prepare pyLDAvis visualization data from current model.

        Args:
            corpus: Corpus in bag-of-words format (uses self.corpus if None)
            sort_topics: Whether to sort topics by relevance

        Returns:
            Dictionary with pyLDAvis data or None if model not trained
        """
        if self.lda_model is None or self.dictionary is None:
            return None

        # Use provided corpus or fall back to instance corpus
        if corpus is None:
            corpus = self.corpus

        if corpus is None:
            return None

        try:
            from services.pyldavis_service import PyLDAvisService

            vis_data = PyLDAvisService.prepare_data(
                self.lda_model,
                self.dictionary,
                corpus,
                sort_topics=sort_topics
            )

            return PyLDAvisService.get_json_data(vis_data)

        except Exception as e:
            print(f"Error preparing pyLDAvis data: {e}")
            return None

    def save_pyldavis_html(self, filepath, corpus=None):
        """
        Save pyLDAvis visualization to HTML file.

        Args:
            filepath: Path to save HTML file
            corpus: Corpus in bag-of-words format (uses self.corpus if None)

        Returns:
            Tuple (success: bool, message: str)
        """
        if self.lda_model is None or self.dictionary is None:
            return False, "Model not trained"

        if corpus is None:
            corpus = self.corpus

        if corpus is None:
            return False, "Corpus not available"

        try:
            from services.pyldavis_service import PyLDAvisService

            vis_data = PyLDAvisService.prepare_data(
                self.lda_model,
                self.dictionary,
                corpus,
                sort_topics=True
            )

            return PyLDAvisService.save_html(vis_data, filepath)

        except Exception as e:
            return False, f"Error saving pyLDAvis HTML: {str(e)}"

    @staticmethod
    def delete_project_files(project_name: str) -> bool:
        """
        Delete all files associated with a project.

        Args:
            project_name: Name of the project whose files should be deleted

        Returns:
            True if files were deleted, False if folder didn't exist
        """
        import shutil

        project_folder = os.path.join(
            Config.RESULTS_DIR,
            project_name.replace(' ', '_').lower()
        )

        if os.path.exists(project_folder):
            try:
                shutil.rmtree(project_folder)
                return True
            except Exception as e:
                print(f"Error deleting project files: {e}")
                return False
        return False
