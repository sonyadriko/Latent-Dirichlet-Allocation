from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from config import Config
from routes.auth import auth_bp
from routes.kdd import kdd_bp
from routes.search import search_bp
from routes.project import project_bp

# Initialize Flask app
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# Configuration
app.config.from_object(Config)
Config.init_app()

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Swagger Configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "LDA Topic Modeling API",
        "description": "API untuk LDA Topic Modeling pada berita bisnis Indonesia dengan KDD Pipeline",
        "contact": {
            "name": "API Support",
            "email": "support@lda-api.com"
        },
        "version": "1.0.0"
    },
    "host": "localhost:3030",
    "basePath": "/api",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header menggunakan format: 'Bearer {token}'"
        }
    },
    "tags": [
        {
            "name": "Authentication",
            "description": "API endpoints untuk autentikasi user"
        },
        {
            "name": "KDD Pipeline",
            "description": "API endpoints untuk KDD Pipeline (Crawling, Preprocessing, Transforming, Data Mining)"
        },
        {
            "name": "Search",
            "description": "API endpoints untuk pencarian dokumen"
        },
        {
            "name": "Projects",
            "description": "API endpoints untuk manajemen project"
        },
        {
            "name": "Health",
            "description": "API endpoint untuk health check"
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(kdd_bp, url_prefix='/api/kdd')
app.register_blueprint(search_bp, url_prefix='/api/search')
app.register_blueprint(project_bp, url_prefix='/api/projects')

# Routes for pages
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/visualization')
def visualization():
    return render_template('visualization.html')

# Health check
@app.route('/api/health')
def health():
    """
    Health Check Endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: Server is running
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
            message:
              type: string
              example: Server is running
    """
    return {'status': 'ok', 'message': 'Server is running'}

if __name__ == '__main__':
    print("="*50)
    print("LDA Business News Trend Application")
    print("="*50)
    print("Server running at: http://localhost:3030")
    print("API Documentation: http://localhost:3030/docs")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=3030)
