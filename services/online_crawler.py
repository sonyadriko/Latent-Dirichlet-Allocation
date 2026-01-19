import requests
from bs4 import BeautifulSoup
import time
import json
from urllib.parse import urljoin, urlparse
from models.document import Document
import os

class OnlineDocumentCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.timeout = 30
        
        # Online document sources
        self.sources = {
            'goodreads': {
                'search_url': 'https://www.goodreads.com/search',
                'params': {'q': '', 'search_type': 'books'},
                'result_selector': '.bookTitle',
                'url_selector': 'a'
            },
            'google_books': {
                'search_url': 'https://www.googleapis.com/books/v1/volumes',
                'params': {'q': '', 'maxResults': 10, 'langRestrict': 'id'},
                'api_only': True
            },
            'wikipedia_id': {
                'search_url': 'https://id.wikipedia.org/wiki/Special:Search',
                'params': {'search': '', 'go': 'Go'},
                'content_selector': '#mw-content-text p'
            }
        }
    
    def search_online_documents(self, query, max_results=10):
        """Search documents from multiple online sources"""
        results = []
        
        try:
            # Search Google Books API
            google_results = self._search_google_books(query, max_results)
            results.extend(google_results)
        except Exception as e:
            print(f"Google Books search error: {e}")
        
        try:
            # Search Wikipedia Indonesia
            wiki_results = self._search_wikipedia_id(query, max_results)
            results.extend(wiki_results)
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        return results
    
    def _search_google_books(self, query, max_results=10):
        """Search using Google Books API"""
        try:
            params = self.sources['google_books']['params'].copy()
            params['q'] = f"{query} novel indonesia"
            params['maxResults'] = max_results
            
            response = requests.get(
                self.sources['google_books']['search_url'],
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = []
                
                for item in data.get('items', []):
                    info = item.get('volumeInfo', {})
                    
                    # Extract title and description
                    title = info.get('title', '')
                    description = info.get('description', '')
                    
                    if not title:
                        continue
                    
                    # Create document content
                    content = description or f"Buku berjudul '{title}'"
                    
                    # Add additional info
                    authors = info.get('authors', [])
                    categories = info.get('categories', [])
                    published_date = info.get('publishedDate', '')
                    
                    doc = {
                        'id': f"gb_{item.get('id', '')}",
                        'title': title,
                        'content': content,
                        'author': ', '.join(authors) if authors else 'Unknown',
                        'category': categories[0] if categories else 'Fiksi',
                        'published_date': published_date,
                        'source': 'google_books',
                        'info_link': info.get('infoLink', ''),
                        'preview_link': info.get('previewLink', '')
                    }
                    
                    documents.append(doc)
                
                return documents
            
        except Exception as e:
            print(f"Google Books search error: {e}")
        
        return []
    
    def _search_wikipedia_id(self, query, max_results=5):
        """Search Wikipedia Indonesia"""
        try:
            # Build search URL
            search_url = f"https://id.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': f"{query} novel",
                'srlimit': max_results,
                'format': 'json',
                'utf8': 1
            }
            
            response = requests.get(search_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                documents = []
                
                search_results = data.get('query', {}).get('search', [])
                
                for result in search_results:
                    title = result.get('title', '')
                    pageid = result.get('pageid', '')
                    
                    if not title:
                        continue
                    
                    # Get page content
                    content = self._get_wikipedia_content(pageid)
                    
                    doc = {
                        'id': f"wiki_{pageid}",
                        'title': title,
                        'content': content,
                        'author': 'Wikipedia',
                        'category': 'Referensi',
                        'published_date': '',
                        'source': 'wikipedia',
                        'info_link': f"https://id.wikipedia.org/wiki/{title.replace(' ', '_')}",
                        'preview_link': f"https://id.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    }
                    
                    documents.append(doc)
                
                return documents
            
        except Exception as e:
            print(f"Wikipedia search error: {e}")
        
        return []
    
    def _get_wikipedia_content(self, pageid):
        """Get content from Wikipedia page"""
        try:
            url = f"https://id.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'prop': 'extracts',
                'pageids': pageid,
                'exintro': True,
                'explaintext': True,
                'format': 'json',
                'utf8': 1
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get('query', {}).get('pages', {})
                
                for page_data in pages.values():
                    content = page_data.get('extract', '')
                    return content[:1000]  # Limit content length
        
        except Exception as e:
            print(f"Error getting Wikipedia content: {e}")
        
        return "Konten tidak tersedia"
    
    def crawl_specific_url(self, url):
        """Crawl content from specific URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Extract title
            title = ''
            title_candidates = [
                soup.find('h1'),
                soup.find('title'),
                soup.find('meta', {'property': 'og:title'})
            ]
            
            for candidate in title_candidates:
                if candidate:
                    if candidate.name == 'meta':
                        title = candidate.get('content', '')
                    else:
                        title = candidate.get_text(strip=True)
                    if title:
                        break
            
            # Extract content
            content = ''
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
            
            return {
                'title': title[:500] if title else 'Untitled',
                'content': content[:2000] if content else 'No content available',
                'source': 'custom_url',
                'info_link': url
            }
            
        except Exception as e:
            print(f"Error crawling URL {url}: {e}")
            return None
    
    def add_online_documents_to_collection(self, online_docs):
        """Add online documents to local collection"""
        documents = Document.get_all_documents()
        
        # Get next ID
        next_id = max([doc.id for doc in documents], default=0) + 1
        
        new_documents = []
        
        for online_doc in online_docs:
            # Check if document already exists (by title)
            existing = Document.search_by_title(online_doc['title'])
            if existing:
                continue
            
            # Create new document
            new_doc = Document(
                id=next_id,
                title=online_doc['title'],
                content=online_doc['content'],
                category=online_doc.get('category', 'Online'),
                author=online_doc.get('author', 'Online Source')
            )
            
            # Add to list
            new_documents.append(new_doc)
            next_id += 1
        
        # Save to file
        if new_documents:
            self._save_documents_to_file(documents + new_documents)
        
        return len(new_documents)
    
    def _save_documents_to_file(self, documents):
        """Save documents to JSON file"""
        docs_data = [doc.to_dict() for doc in documents]
        
        with open(Document.DOCUMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(docs_data, f, indent=2, ensure_ascii=False)