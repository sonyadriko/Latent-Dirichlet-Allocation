from flask import Blueprint, request, jsonify
import jwt
import datetime
from functools import wraps
from config import Config
from models.user import User

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'success': False, 'message': 'Token format tidak valid'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token tidak ditemukan'}), 401
        
        try:
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = User.find_by_id(data['user_id'])
            if not current_user:
                return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token sudah expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token tidak valid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak valid'}), 400
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Semua field harus diisi'}), 400
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password minimal 6 karakter'}), 400
    
    user, error = User.create(name, email, password)
    
    if error:
        return jsonify({'success': False, 'message': error}), 400
    
    return jsonify({
        'success': True,
        'message': 'Registrasi berhasil',
        'user': user.to_dict()
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Data tidak valid'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'success': False, 'message': 'Email dan password harus diisi'}), 400
    
    user = User.find_by_email(email)
    
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Email atau password salah'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.JWT_SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'success': True,
        'message': 'Login berhasil',
        'token': token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify(current_user):
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({
        'success': True,
        'message': 'Logout berhasil'
    }), 200
