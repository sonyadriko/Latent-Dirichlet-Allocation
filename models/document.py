import json
import os
from config import Config

class Document:
    DOCUMENTS_FILE = os.path.join(Config.DATA_DIR, 'documents.json')
    
    def __init__(self, id, title, content, category=None, author=None):
        self.id = id
        self.title = title
        self.content = content
        self.category = category
        self.author = author
    
    @staticmethod
    def _load_documents():
        """Load all documents from JSON file"""
        if os.path.exists(Document.DOCUMENTS_FILE):
            with open(Document.DOCUMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def get_all_documents():
        """Get all documents as Document objects"""
        docs_data = Document._load_documents()
        return [Document(
            id=doc['id'],
            title=doc['title'],
            content=doc['content'],
            category=doc.get('category'),
            author=doc.get('author')
        ) for doc in docs_data]
    
    @staticmethod
    def search_by_title(query):
        """Search documents by title"""
        query = query.lower()
        documents = Document.get_all_documents()
        
        results = []
        for doc in documents:
            if query in doc.title.lower():
                results.append(doc)
        
        return results
    
    @staticmethod
    def search_by_title_fuzzy(query, threshold=85):
        """Search documents by title using fuzzy matching"""
        from difflib import SequenceMatcher
        
        query = query.lower()
        documents = Document.get_all_documents()
        
        results = []
        for doc in documents:
            title_lower = doc.title.lower()
            
            # First check: exact substring match (highest priority)
            if query in title_lower:
                results.append((doc, 100, 'title'))  # Perfect match score + match type
                continue
            
            # Second check: word-level matching
            query_words = query.split()
            title_words = title_lower.split()
            
            # Check if any query word appears in title
            word_matches = sum(1 for qw in query_words if any(qw in tw for tw in title_words))
            if word_matches > 0:
                word_score = (word_matches / len(query_words)) * 90  # Max 90% for word match
                if word_score >= threshold:
                    results.append((doc, word_score, 'title'))
                    continue
            
            # Last resort: fuzzy character matching (only if threshold is lower)
            if threshold < 80:
                similarity = SequenceMatcher(None, query, title_lower).ratio() * 100
                if similarity >= threshold:
                    results.append((doc, similarity, 'title'))
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return only documents without the similarity score
        return [doc for doc, similarity, match_type in results]
    
    @staticmethod
    def search_by_title_or_content(query, threshold=75):
        """Search documents by title OR content using fuzzy matching"""
        from difflib import SequenceMatcher
        
        query = query.lower()
        documents = Document.get_all_documents()
        
        results = []
        for doc in documents:
            title_lower = doc.title.lower()
            content_lower = doc.content.lower()
            
            # Priority 1: Exact substring match in title (highest priority)
            if query in title_lower:
                results.append((doc, 100, 'title'))  # Perfect match score + match type
                continue
            
            # Priority 2: Word-level matching in title
            query_words = query.split()
            title_words = title_lower.split()
            
            title_word_matches = sum(1 for qw in query_words if any(qw in tw for tw in title_words))
            if title_word_matches > 0:
                title_score = (title_word_matches / len(query_words)) * 95  # Max 95% for title word match
                if title_score >= threshold:
                    results.append((doc, title_score, 'title'))
                    continue
            
            # Priority 3: Exact substring match in content (lower priority)
            if query in content_lower:
                results.append((doc, 70, 'content'))  # Lower score for content match
                continue
            
            # Priority 4: Word-level matching in content
            content_words = content_lower.split()
            content_word_matches = sum(1 for qw in query_words if any(qw in cw for cw in content_words))
            if content_word_matches > 0:
                content_score = (content_word_matches / len(query_words)) * 65  # Max 65% for content word match
                if content_score >= threshold - 15:  # Lower threshold for content matches
                    results.append((doc, content_score, 'content'))
                    continue
        
        # Sort by similarity score (highest first), then by match type (title > content)
        results.sort(key=lambda x: (x[1], 0 if x[2] == 'title' else 1), reverse=True)
        
        # Return documents with match info
        return [{'doc': doc, 'score': score, 'match_type': match_type} for doc, score, match_type in results]
    
    @staticmethod
    def get_document_by_id(doc_id):
        """Get document by ID"""
        documents = Document.get_all_documents()
        for doc in documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def to_dict(self):
        """Convert document to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'author': self.author
        }
    
    def get_excerpt(self, max_length=200):
        """Get short excerpt of content"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."