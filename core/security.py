"""
Security utilities for FastAPI authentication

Includes password hashing/verification and JWT-based authentication backed by
the MySQL database (via UserRepository).
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from core.database import get_session
from models.db_models import User
from repositories.user_repository import UserRepository

# HTTP Bearer security scheme
security = HTTPBearer()

# Token expiration time (default 24 hours)
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing using pbkdf2_sha256 (no 72-byte limit, version-stable)
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000
)


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-SHA256."""
    return pwd_context.hash(password)


def verify_password(password: str, hash_value: str) -> bool:
    """
    Verify a password against a stored hash.

    Supports both:
    - New format: pbkdf2_sha256
    - Legacy format: bcrypt (for users migrated from the old JSON store)
    """
    if not hash_value:
        return False

    # Legacy bcrypt hashes start with $2a$, $2b$, etc.
    if hash_value.startswith('$2') and len(hash_value) > 3 and hash_value[3] == '$':
        try:
            from passlib.hash import bcrypt
            return bcrypt.verify(password, hash_value)
        except Exception:
            return False

    return pwd_context.verify(password, hash_value)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, Config.JWT_SECRET_KEY, algorithm="HS256")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Dependency to get the current authenticated user from a JWT token.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header
        session: Database session (injected)

    Returns:
        The authenticated ORM User

    Raises:
        HTTPException: If the token is invalid/expired or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await UserRepository.get_by_id(session, user_id)

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    """
    Optional version of get_current_user that returns None when no valid token
    is provided instead of raising.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, session)
    except HTTPException:
        return None
