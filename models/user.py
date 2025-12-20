import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

class User:
    USERS_FILE = os.path.join(Config.DATA_DIR, 'users.json')
    
    def __init__(self, id, name, email, password_hash):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
    
    @staticmethod
    def _load_users():
        if os.path.exists(User.USERS_FILE):
            with open(User.USERS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def _save_users(users):
        os.makedirs(os.path.dirname(User.USERS_FILE), exist_ok=True)
        with open(User.USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    
    @staticmethod
    def create(name, email, password):
        users = User._load_users()
        
        # Check if email already exists
        if any(u['email'] == email for u in users):
            return None, "Email sudah terdaftar"
        
        # Generate new ID
        new_id = max([u['id'] for u in users], default=0) + 1
        
        # Create new user
        new_user = {
            'id': new_id,
            'name': name,
            'email': email,
            'password_hash': generate_password_hash(password)
        }
        
        users.append(new_user)
        User._save_users(users)
        
        return User(new_id, name, email, new_user['password_hash']), None
    
    @staticmethod
    def find_by_email(email):
        users = User._load_users()
        for u in users:
            if u['email'] == email:
                return User(u['id'], u['name'], u['email'], u['password_hash'])
        return None
    
    @staticmethod
    def find_by_id(user_id):
        users = User._load_users()
        for u in users:
            if u['id'] == user_id:
                return User(u['id'], u['name'], u['email'], u['password_hash'])
        return None
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
