import json
import os
from passlib.context import CryptContext
from config import Config

# Password hashing using pbkdf2_sha256
# No 72-byte limit, compatible with all passlib versions
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000
)


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-SHA256."""
    return pwd_context.hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    """Verify password against hash.

    Supports both:
    - New format: pbkdf2_sha256
    - Old format: bcrypt (for existing users)
    """
    # Check if it's a bcrypt hash (starts with $2a$, $2b$, etc)
    if hash_value.startswith('$2') and hash_value[3] == '$':
        try:
            from passlib.hash import bcrypt
            return bcrypt.verify(password, hash_value)
        except Exception:
            return False

    # Otherwise use pbkdf2_sha256
    return pwd_context.verify(password, hash_value)


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
            'password_hash': hash_password(password)
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
        return verify_password(password, self.password_hash)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email
        }
