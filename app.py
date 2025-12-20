from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.kdd import kdd_bp
from routes.search import search_bp

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Configuration
app.config.from_object(Config)
Config.init_app()

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(kdd_bp, url_prefix='/api/kdd')
app.register_blueprint(search_bp, url_prefix='/api/search')

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
    return {'status': 'ok', 'message': 'Server is running'}

if __name__ == '__main__':
    print("="*50)
    print("LDA Business News Trend Application")
    print("="*50)
    print("Server running at: http://localhost:5001")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5001)
