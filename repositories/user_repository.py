"""
User Repository

Handles data access for user operations.
"""
from typing import Optional, List

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import User


class UserRepository:
    """
    Repository for User model.

    Provides CRUD operations and query methods for users.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        email: str,
        password_hash: str
    ) -> User:
        """
        Create a new user.

        Args:
            session: Database session
            name: User's full name
            email: User's email address
            password_hash: Bcrypt hash of the password

        Returns:
            Created User instance
        """
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )

        session.add(user)
        await session.flush()
        await session.refresh(user)

        return user

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email_with_password(session: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email including password hash for authentication.

        Note: Only use this for authentication verification.
        """
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(
        session: AsyncSession,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[User]:
        """
        List users with optional filters.

        Args:
            session: Database session
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of User instances
        """
        query = select(User)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        query = query.order_by(User.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        password_hash: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[User]:
        """
        Update user fields.

        Args:
            session: Database session
            user_id: User ID to update
            name: New name
            email: New email
            password_hash: New password hash
            is_active: New active status

        Returns:
            Updated User or None
        """
        user = await UserRepository.get_by_id(session, user_id)
        if user:
            if name is not None:
                user.name = name
            if email is not None:
                user.email = email
            if password_hash is not None:
                user.password_hash = password_hash
            if is_active is not None:
                user.is_active = is_active

            await session.flush()
            await session.refresh(user)

        return user

    @staticmethod
    async def delete(session: AsyncSession, user_id: int) -> bool:
        """
        Delete a user.

        Args:
            session: Database session
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        user = await UserRepository.get_by_id(session, user_id)
        if user:
            await session.delete(user)
            return True
        return False

    @staticmethod
    async def email_exists(session: AsyncSession, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if an email address already exists.

        Args:
            session: Database session
            email: Email to check
            exclude_id: Exclude this user ID from check (for updates)

        Returns:
            True if email exists, False otherwise
        """
        query = select(User.id).where(User.email == email)

        if exclude_id:
            query = query.where(User.id != exclude_id)

        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def count(session: AsyncSession, is_active: Optional[bool] = None) -> int:
        """Count users with optional filter."""
        from sqlalchemy import func

        query = select(func.count(User.id))

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        result = await session.execute(query)
        return result.scalar() or 0
