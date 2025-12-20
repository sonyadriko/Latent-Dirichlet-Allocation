import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lda-secret-key-2024'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-lda-2024'
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    RESULTS_DIR = os.path.join(DATA_DIR, 'results')
    
    # LDA Configuration
    NUM_TOPICS = 5
    NUM_WORDS_PER_TOPIC = 10
    PASSES = 15
    ITERATIONS = 100
    
    # Ensure directories exist
    @staticmethod
    def init_app():
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        os.makedirs(Config.RESULTS_DIR, exist_ok=True)
