"""
Project Repository

Handles data access for project operations.
"""
from typing import Optional, List

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import Project


class ProjectRepository:
    """
    Repository for Project model.

    Provides CRUD operations and query methods for projects.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        name: str,
        description: Optional[str] = None,
        num_topics: int = 5,
        document_count: int = 0,
        coherence_score: float = 0.0,
        model_path: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            session: Database session
            name: Project name (must be unique)
            description: Project description
            num_topics: Number of topics
            document_count: Number of documents
            coherence_score: Coherence score
            model_path: Path to saved model
            created_by: User ID who created the project

        Returns:
            Created Project instance
        """
        project = Project(
            name=name,
            description=description,
            num_topics=num_topics,
            document_count=document_count,
            coherence_score=coherence_score,
            model_path=model_path,
            created_by=created_by
        )

        session.add(project)
        await session.flush()
        await session.refresh(project)

        return project

    @staticmethod
    async def get_by_id(session: AsyncSession, project_id: int) -> Optional[Project]:
        """Get a project by ID."""
        result = await session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Optional[Project]:
        """Get a project by name."""
        result = await session.execute(
            select(Project).where(Project.name == name)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_projects(
        session: AsyncSession,
        created_by: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Project]:
        """
        List projects with optional filters.

        Args:
            session: Database session
            created_by: Filter by creator user ID
            status: Filter by status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Project instances
        """
        query = select(Project)

        if created_by:
            query = query.where(Project.created_by == created_by)
        if status:
            query = query.where(Project.status == status)

        query = query.order_by(Project.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        num_topics: Optional[int] = None,
        document_count: Optional[int] = None,
        coherence_score: Optional[float] = None,
        model_path: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Project]:
        """
        Update project fields.

        Args:
            session: Database session
            project_id: Project ID to update
            name: New name
            description: New description
            num_topics: New number of topics
            document_count: New document count
            coherence_score: New coherence score
            model_path: New model path
            status: New status

        Returns:
            Updated Project or None
        """
        project = await ProjectRepository.get_by_id(session, project_id)
        if project:
            if name is not None:
                project.name = name
            if description is not None:
                project.description = description
            if num_topics is not None:
                project.num_topics = num_topics
            if document_count is not None:
                project.document_count = document_count
            if coherence_score is not None:
                project.coherence_score = coherence_score
            if model_path is not None:
                project.model_path = model_path
            if status is not None:
                project.status = status

            await session.flush()
            await session.refresh(project)

        return project

    @staticmethod
    async def delete(session: AsyncSession, project_id: int) -> bool:
        """
        Delete a project.

        Args:
            session: Database session
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        project = await ProjectRepository.get_by_id(session, project_id)
        if project:
            await session.delete(project)
            return True
        return False

    @staticmethod
    async def name_exists(session: AsyncSession, name: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a project name already exists.

        Args:
            session: Database session
            name: Name to check
            exclude_id: Exclude this project ID from check (for updates)

        Returns:
            True if name exists, False otherwise
        """
        query = select(Project.id).where(Project.name == name)

        if exclude_id:
            query = query.where(Project.id != exclude_id)

        result = await session.execute(query)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_by_creator(session: AsyncSession, user_id: int) -> List[Project]:
        """Get all projects created by a specific user."""
        result = await session.execute(
            select(Project)
            .where(Project.created_by == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_stats(session: AsyncSession) -> dict:
        """
        Get project statistics.

        Returns:
            Dictionary with project statistics
        """
        total = await session.execute(select(func.count(Project.id)))
        total_projects = total.scalar() or 0

        total_docs = await session.execute(select(func.sum(Project.document_count)))
        total_documents = total_docs.scalar() or 0

        avg_coherence = await session.execute(select(func.avg(Project.coherence_score)))
        average_coherence = avg_coherence.scalar() or 0.0

        total_topics = await session.execute(select(func.sum(Project.num_topics)))
        sum_topics = total_topics.scalar() or 0

        # Get topic distribution
        topic_dist_result = await session.execute(
            select(Project.num_topics, func.count(Project.id))
            .group_by(Project.num_topics)
        )
        topic_distribution = {str(num_topics): count for num_topics, count in topic_dist_result.all()}

        # Get recent projects
        recent_result = await session.execute(
            select(Project)
            .order_by(Project.created_at.desc())
            .limit(5)
        )
        recent_projects = list(result.scalars().all())

        return {
            "total_projects": total_projects,
            "total_documents": total_documents,
            "average_coherence": round(average_coherence, 3),
            "total_topics": sum_topics,
            "topic_distribution": topic_distribution,
            "recent_projects": recent_projects
        }

    @staticmethod
    async def search(
        session: AsyncSession,
        search_term: str,
        limit: int = 20
    ) -> List[Project]:
        """
        Search projects by name or description.

        Args:
            session: Database session
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of matching projects
        """
        search_pattern = f"%{search_term}%"

        result = await session.execute(
            select(Project)
            .where(
                or_(
                    Project.name.ilike(search_pattern),
                    Project.description.ilike(search_pattern)
                )
            )
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_active_with_model(session: AsyncSession) -> List[Project]:
        """Get all active projects that have a model saved."""
        result = await session.execute(
            select(Project)
            .where(
                and_(
                    Project.status == "active",
                    Project.model_path.isnot(None)
                )
            )
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
