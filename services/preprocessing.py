import re
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except (LookupError, OSError):
    nltk.download('punkt_tab', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class TextPreprocessor:
    def __init__(self):
        # Initialize Sastrawi stemmer for Indonesian
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()
        
        # Indonesian stopwords
        self.stopwords = set(stopwords.words('indonesian'))
        
        # Additional Indonesian stopwords
        additional_stopwords = {
            'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'dengan', 'untuk',
            'pada', 'adalah', 'sebagai', 'dalam', 'tidak', 'akan', 'juga',
            'atau', 'tersebut', 'dapat', 'telah', 'ada', 'bisa', 'sudah',
            'saat', 'oleh', 'setelah', 'lebih', 'hanya', 'seperti', 'serta',
            'bahwa', 'mereka', 'kami', 'kita', 'ia', 'dia', 'anda', 'saya',
            'kamu', 'apa', 'siapa', 'kapan', 'dimana', 'mengapa', 'bagaimana',
            'jika', 'maka', 'karena', 'namun', 'tetapi', 'sedangkan', 'sementara',
            'antara', 'hingga', 'sampai', 'selama', 'sejak', 'ketika', 'sebelum',
            'sesudah', 'agar', 'supaya', 'meski', 'meskipun', 'walaupun', 'bila',
            'pun', 'lah', 'kah', 'nya', 'mu', 'ku', 'para', 'hal', 'sebuah',
            'seorang', 'suatu', 'salah', 'satu', 'dua', 'tiga', 'empat', 'lima'
        }
        self.stopwords.update(additional_stopwords)
    
    def case_folding(self, text):
        """Convert text to lowercase"""
        return text.lower()
    
    def remove_punctuation(self, text):
        """Remove punctuation and special characters"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize(self, text):
        """Tokenize text into words"""
        return word_tokenize(text)
    
    def remove_stopwords(self, tokens):
        """Remove stopwords from tokens"""
        return [token for token in tokens if token not in self.stopwords and len(token) > 2]
    
    def stem(self, tokens):
        """Apply stemming to tokens"""
        return [self.stemmer.stem(token) for token in tokens]
    
    def preprocess(self, text):
        """Full preprocessing pipeline"""
        # Step 1: Case folding
        text = self.case_folding(text)
        
        # Step 2: Remove punctuation
        text = self.remove_punctuation(text)
        
        # Step 3: Tokenization
        tokens = self.tokenize(text)
        
        # Step 4: Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Step 5: Stemming
        tokens = self.stem(tokens)
        
        return tokens
    
    def preprocess_documents(self, documents):
        """Preprocess multiple documents"""
        preprocessed = []
        for doc in documents:
            tokens = self.preprocess(doc)
            preprocessed.append(tokens)
        return preprocessed
