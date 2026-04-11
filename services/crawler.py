import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urlparse

class CrawlerService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.timeout = 30

    def extract_content(self, html, url):
        """Extract article content from HTML"""
        soup = BeautifulSoup(html, 'lxml')

        # Special handling for Gramedia.com products
        if 'gramedia.com/products' in url:
            return self._extract_gramedia_product(soup, url)

        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
            element.decompose()

        # Try to find article title
        title = ''
        title_candidates = [
            soup.find('h1'),
            soup.find('title'),
            soup.find('meta', {'property': 'og:title'}),
            soup.find('meta', {'name': 'title'})
        ]
        
        for candidate in title_candidates:
            if candidate:
                if candidate.name == 'meta':
                    title = candidate.get('content', '')
                else:
                    title = candidate.get_text(strip=True)
                if title:
                    break
        
        # Try to find article content using common patterns
        content = ''
        
        # Common article container selectors
        article_selectors = [
            {'class_': re.compile(r'article.*content|content.*article|post.*content|entry.*content', re.I)},
            {'class_': re.compile(r'article.*body|body.*article|post.*body', re.I)},
            {'class_': 'article-content'},
            {'class_': 'article-body'},
            {'class_': 'post-content'},
            {'class_': 'entry-content'},
            {'class_': 'content'},
            {'class_': 'detail-text'},
            {'class_': 'read__content'},
            {'itemprop': 'articleBody'},
        ]
        
        # Try article tag first
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50])
        
        # If article tag doesn't have enough content, try other selectors
        if len(content) < 200:
            for selector in article_selectors:
                container = soup.find('div', selector)
                if container:
                    paragraphs = container.find_all('p')
                    temp_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                    if len(temp_content) > len(content):
                        content = temp_content
        
        # Fallback: get all paragraphs
        if len(content) < 200:
            all_paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in all_paragraphs if len(p.get_text(strip=True)) > 50])
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Extract date if possible
        date = ''
        date_meta = soup.find('meta', {'property': 'article:published_time'}) or \
                    soup.find('meta', {'name': 'pubdate'}) or \
                    soup.find('time')
        if date_meta:
            if date_meta.name == 'meta':
                date = date_meta.get('content', '')
            elif date_meta.name == 'time':
                date = date_meta.get('datetime', '') or date_meta.get_text(strip=True)
        
        return {
            'title': title[:500] if title else 'Untitled',
            'content': content,
            'date': date[:50] if date else '',
            'url': url
        }

    def _extract_gramedia_product(self, soup, url):
        """Extract product data from Gramedia.com using JSON-LD"""
        import json

        title = 'Untitled'
        content = ''
        author = 'Gramedia'

        # Try to get from JSON-LD DataFeed
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for DataFeed format (Gramedia books)
                    if data.get('@type') == 'DataFeed' and 'dataFeedElement' in data:
                        elements = data['dataFeedElement']
                        if elements and len(elements) > 0:
                            book = elements[0]
                            title = book.get('name', title)
                            content = book.get('description', '')
                            if 'author' in book:
                                author = book['author'].get('name', author) if isinstance(book['author'], dict) else author
                            break

                    # Check for @graph format (Product)
                    elif '@graph' in data:
                        for item in data['@graph']:
                            if item.get('@type') == 'Product':
                                title = item.get('name', title)
                                content = item.get('description', '')
                                break
                        if content:
                            break
            except (json.JSONDecodeError, KeyError, TypeError):
                continue

        # Fallback to h1 if no title found
        if not title or title == 'Untitled':
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

        return {
            'title': title[:500] if title else 'Untitled',
            'content': content,
            'date': '',
            'url': url
        }

    def crawl_url(self, url):
        """Crawl a single URL and extract content"""
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None, f"Invalid URL: {url}"
            
            # Make request
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                return None, f"Not HTML content: {content_type}"
            
            # Extract content
            article = self.extract_content(response.text, url)
            
            # Validate content
            if len(article['content']) < 100:
                return None, f"Content too short: {len(article['content'])} chars"
            
            return article, None
            
        except requests.exceptions.Timeout:
            return None, f"Timeout: {url}"
        except requests.exceptions.RequestException as e:
            return None, f"Request error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def crawl_urls(self, urls, delay=1):
        """Crawl multiple URLs"""
        results = {
            'success': [],
            'failed': [],
            'total': len(urls),
            'success_count': 0,
            'failed_count': 0
        }
        
        for i, url in enumerate(urls):
            url = url.strip()
            if not url or url.startswith('#'):
                continue
            
            article, error = self.crawl_url(url)
            
            if article:
                article['id'] = i + 1
                results['success'].append(article)
                results['success_count'] += 1
            else:
                results['failed'].append({'url': url, 'error': error})
                results['failed_count'] += 1
            
            # Delay between requests to be polite
            if i < len(urls) - 1:
                time.sleep(delay)
        
        return results
    
    def parse_urls_from_file(self, file_content):
        """Parse URLs from uploaded file content"""
        lines = file_content.strip().split('\n')
        urls = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Check if it looks like a URL
                if line.startswith('http://') or line.startswith('https://'):
                    urls.append(line)
                elif '.' in line and '/' in line:
                    # Try adding https://
                    urls.append('https://' + line)
        
        return urls
