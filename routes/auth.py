from flask import Blueprint, request, jsonify
import jwt
import datetime
from functools import wraps
from config import Config
from models.user import User
from flasgger import swag_from

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
    """
    Register User Baru
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        description: Data user baru
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - password
          properties:
            name:
              type: string
              example: John Doe
              description: Nama lengkap user
            email:
              type: string
              format: email
              example: john@example.com
              description: Email user
            password:
              type: string
              format: password
              example: password123
              minLength: 6
              description: Password minimal 6 karakter
    responses:
      201:
        description: Registrasi berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Registrasi berhasil
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: John Doe
                email:
                  type: string
                  example: john@example.com
      400:
        description: Data tidak valid atau user sudah ada
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Email sudah terdaftar
    """
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
    """
    Login User
    ---
    tags:
      - Authentication
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        description: Login credentials
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
              example: john@example.com
              description: Email user
            password:
              type: string
              format: password
              example: password123
              description: Password user
    responses:
      200:
        description: Login berhasil
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Login berhasil
            token:
              type: string
              example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: John Doe
                email:
                  type: string
                  example: john@example.com
      401:
        description: Email atau password salah
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Email atau password salah
      400:
        description: Data tidak valid
    """
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
    """
    Verifikasi JWT Token
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Token valid
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            user:
              type: object
              properties:
                id:
                  type: integer
                  example: 1
                name:
                  type: string
                  example: John Doe
                email:
                  type: string
                  example: john@example.com
      401:
        description: Token tidak valid atau expired
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            message:
              type: string
              example: Token tidak valid
    """
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout User
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Logout berhasil (client-side token removal)
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Logout berhasil
    """
    return jsonify({
        'success': True,
        'message': 'Logout berhasil'
    }), 200
