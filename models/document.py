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