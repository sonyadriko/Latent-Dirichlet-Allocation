"""
Authentication router for FastAPI
Handles user registration, login, token verification, and logout
"""
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from models.db_models import User
from repositories.user_repository import UserRepository

router = APIRouter()


@router.post("/register")
async def register(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Register a new user

    Expects JSON body with:
    - **name**: Full name of the user (min 2 characters)
    - **email**: Valid email address
    - **password**: Password (min 6 characters)
    """
    data = await request.json()

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    # Validate input
    if not all([name, email, password]):
        return {
            'success': False,
            'message': 'Semua field harus diisi'
        }

    if len(password) < 6:
        return {
            'success': False,
            'message': 'Password minimal 6 karakter'
        }

    # Reject duplicate emails
    if await UserRepository.email_exists(session, email):
        return {
            'success': False,
            'message': 'Email sudah terdaftar'
        }

    user = await UserRepository.create(
        session=session,
        name=name,
        email=email,
        password_hash=hash_password(password)
    )

    return {
        'success': True,
        'message': 'Registrasi berhasil',
        'user': user.to_dict()
    }


@router.post("/login")
async def login(request: Request, session: AsyncSession = Depends(get_session)):
    """
    User login

    Expects JSON body with:
    - **email**: User email address
    - **password**: User password

    Returns JWT access token on successful authentication
    """
    data = await request.json()

    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return {
            'success': False,
            'message': 'Email dan password harus diisi'
        }

    user = await UserRepository.get_by_email_with_password(session, email)

    if not user or not verify_password(password, user.password_hash):
        return {
            'success': False,
            'message': 'Email atau password salah'
        }

    # Generate JWT token
    token = create_access_token(data={"user_id": user.id})

    return {
        'success': True,
        'message': 'Login berhasil',
        'token': token,
        'user': user.to_dict()
    }


@router.get("/verify")
async def verify(current_user: User = Depends(get_current_user)):
    """
    Verify JWT token and get current user

    Requires valid Bearer token in Authorization header
    """
    return {
        'success': True,
        'user': current_user.to_dict()
    }


@router.post("/logout")
async def logout():
    """
    User logout

    Note: JWT tokens are stateless. Logout is handled client-side
    by removing the token from storage.
    """
    return {
        'success': True,
        'message': 'Logout berhasil'
    }
