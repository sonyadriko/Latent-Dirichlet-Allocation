import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lda-secret-key-2024'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-lda-2024'
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    RESULTS_DIR = os.path.join(DATA_DIR, 'results')

    # Database Configuration (external MySQL)
    # An explicit DATABASE_URL always wins; otherwise it is composed from the
    # individual MYSQL_* env vars. charset=utf8mb4 is REQUIRED so multibyte
    # content (curly quotes, etc.) is stored correctly.
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'lda_app')

    DATABASE_URL = os.environ.get('DATABASE_URL') or (
        f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    )

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
