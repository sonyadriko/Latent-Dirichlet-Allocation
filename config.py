import os
import json

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lda-secret-key-2024'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-lda-2024'
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    RESULTS_DIR = os.path.join(DATA_DIR, 'results')
    EXCLUDED_KEYWORDS_FILE = os.path.join(DATA_DIR, 'excluded_keywords.json')

    # Database Configuration (SQLite for single-container deployment)
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'sqlite+aiosqlite:///' + os.path.join(DATA_DIR, 'lda_app.db')
    )

    # LDA Configuration
    NUM_TOPICS = 5
    NUM_WORDS_PER_TOPIC = 10
    PASSES = 15
    ITERATIONS = 100

    # Topic Keywords Exclusion (default stopwords for topic visualization)
    EXCLUDED_KEYWORDS = []

    @staticmethod
    def get_excluded_keywords(project_name=None):
        """
        Get excluded keywords for a project.
        Can be overridden per project or globally.
        Loads from persistent file storage.
        """
        # Load from file for persistence
        Config._load_excluded_keywords()
        return Config.EXCLUDED_KEYWORDS

    @staticmethod
    def set_excluded_keywords(keywords):
        """Set global excluded keywords and persist to file"""
        Config.EXCLUDED_KEYWORDS = keywords
        Config._save_excluded_keywords()

    @staticmethod
    def _load_excluded_keywords():
        """Load excluded keywords from file"""
        try:
            if os.path.exists(Config.EXCLUDED_KEYWORDS_FILE):
                with open(Config.EXCLUDED_KEYWORDS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    Config.EXCLUDED_KEYWORDS = data.get('keywords', [])
            else:
                Config.EXCLUDED_KEYWORDS = []
        except Exception as e:
            print(f"Error loading excluded keywords: {e}")
            Config.EXCLUDED_KEYWORDS = []

    @staticmethod
    def _save_excluded_keywords():
        """Save excluded keywords to file"""
        try:
            os.makedirs(Config.DATA_DIR, exist_ok=True)
            with open(Config.EXCLUDED_KEYWORDS_FILE, 'w', encoding='utf-8') as f:
                json.dump({'keywords': Config.EXCLUDED_KEYWORDS}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving excluded keywords: {e}")

    # Ensure directories exist
    @staticmethod
    def init_app():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.RESULTS_DIR, exist_ok=True)
        # Load excluded keywords on startup
        Config._load_excluded_keywords()
