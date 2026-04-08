"""
Document Repository

Handles data access for document operations.
"""
from typing import Optional, List

from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.db_models import Document


class DocumentRepository:
    """
    Repository for Document model.

    Provides CRUD operations and query methods for documents.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        title: str,
        content: str,
        url: Optional[str] = None,
        tokens_count: int = 0,
        dominant_topic: Optional[int] = None,
        dominant_prob: Optional[float] = None,
        project_id: Optional[int] = None
    ) -> Document:
        """
        Create a new document.

        Args:
            session: Database session
            title: Document title
            content: Document content
            url: Source URL
            tokens_count: Number of tokens after preprocessing
            dominant_topic: Dominant topic ID
            dominant_prob: Dominant topic probability
            project_id: Associated project ID

        Returns:
            Created Document instance
        """
        document = Document(
            title=title,
            content=content,
            url=url,
            tokens_count=tokens_count,
            dominant_topic=dominant_topic,
            dominant_prob=dominant_prob,
            project_id=project_id
        )

        session.add(document)
        await session.flush()
        await session.refresh(document)

        return document

    @staticmethod
    async def create_bulk(
        session: AsyncSession,
        documents: List[dict],
        project_id: Optional[int] = None
    ) -> List[Document]:
        """
        Create multiple documents in bulk.

        Args:
            session: Database session
            documents: List of document dictionaries
            project_id: Associated project ID

        Returns:
            List of created Document instances
        """
        doc_instances = []
        for doc_data in documents:
            doc = Document(
                title=doc_data.get("title", ""),
                content=doc_data.get("content", ""),
                url=doc_data.get("url"),
                tokens_count=doc_data.get("tokens_count", 0),
                dominant_topic=doc_data.get("dominant_topic"),
                dominant_prob=doc_data.get("dominant_prob"),
                project_id=project_id
            )
            doc_instances.append(doc)

        session.add_all(doc_instances)
        await session.flush()

        for doc in doc_instances:
            await session.refresh(doc)

        return doc_instances

    @staticmethod
    async def get_by_id(session: AsyncSession, document_id: int) -> Optional[Document]:
        """Get a document by ID."""
        result = await session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        session: AsyncSession,
        project_id: Optional[int] = None,
        dominant_topic: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """
        List documents with optional filters.

        Args:
            session: Database session
            project_id: Filter by project
            dominant_topic: Filter by dominant topic
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of Document instances
        """
        query = select(Document)

        if project_id:
            query = query.where(Document.project_id == project_id)
        if dominant_topic is not None:
            query = query.where(Document.dominant_topic == dominant_topic)

        query = query.order_by(Document.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update(
        session: AsyncSession,
        document_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        tokens_count: Optional[int] = None,
        dominant_topic: Optional[int] = None,
        dominant_prob: Optional[float] = None
    ) -> Optional[Document]:
        """
        Update document fields.

        Args:
            session: Database session
            document_id: Document ID to update
            title: New title
            content: New content
            url: New URL
            tokens_count: New token count
            dominant_topic: New dominant topic
            dominant_prob: New dominant topic probability

        Returns:
            Updated Document or None
        """
        document = await DocumentRepository.get_by_id(session, document_id)
        if document:
            if title is not None:
                document.title = title
            if content is not None:
                document.content = content
            if url is not None:
                document.url = url
            if tokens_count is not None:
                document.tokens_count = tokens_count
            if dominant_topic is not None:
                document.dominant_topic = dominant_topic
            if dominant_prob is not None:
                document.dominant_prob = dominant_prob

            await session.flush()
            await session.refresh(document)

        return document

    @staticmethod
    async def delete(session: AsyncSession, document_id: int) -> bool:
        """
        Delete a document.

        Args:
            session: Database session
            document_id: Document ID to delete

        Returns:
            True if deleted, False if not found
        """
        document = await DocumentRepository.get_by_id(session, document_id)
        if document:
            await session.delete(document)
            return True
        return False

    @staticmethod
    async def delete_by_project(session: AsyncSession, project_id: int) -> int:
        """
        Delete all documents for a project.

        Args:
            session: Database session
            project_id: Project ID

        Returns:
            Number of deleted documents
        """
        result = await session.execute(
            delete(Document).where(Document.project_id == project_id)
        )
        return result.rowcount

    @staticmethod
    async def count(
        session: AsyncSession,
        project_id: Optional[int] = None,
        dominant_topic: Optional[int] = None
    ) -> int:
        """Count documents with optional filters."""
        query = select(func.count(Document.id))

        if project_id:
            query = query.where(Document.project_id == project_id)
        if dominant_topic is not None:
            query = query.where(Document.dominant_topic == dominant_topic)

        result = await session.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def search(
        session: AsyncSession,
        search_term: str,
        project_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Document]:
        """
        Search documents by title or content.

        Args:
            session: Database session
            search_term: Search term
            project_id: Filter by project
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        search_pattern = f"%{search_term}%"

        query = select(Document).where(
            or_(
                Document.title.ilike(search_pattern),
                Document.content.ilike(search_pattern)
            )
        )

        if project_id:
            query = query.where(Document.project_id == project_id)

        query = query.order_by(Document.created_at.desc()).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_topic_distribution(
        session: AsyncSession,
        project_id: Optional[int] = None
    ) -> dict:
        """
        Get distribution of documents across topics.

        Args:
            session: Database session
            project_id: Filter by project

        Returns:
            Dictionary mapping topic IDs to document counts
        """
        query = select(
            Document.dominant_topic,
            func.count(Document.id)
        ).where(Document.dominant_topic.isnot(None))

        if project_id:
            query = query.where(Document.project_id == project_id)

        query = query.group_by(Document.dominant_topic)

        result = await session.execute(query)
        return {str(topic_id): count for topic_id, count in result.all()}

    @staticmethod
    async def get_by_topic(
        session: AsyncSession,
        topic_id: int,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Document]:
        """
        Get documents for a specific topic.

        Args:
            session: Database session
            topic_id: Topic ID
            project_id: Filter by project
            limit: Maximum number of results

        Returns:
            List of documents for the topic
        """
        query = select(Document).where(
            and_(
                Document.dominant_topic == topic_id,
                Document.dominant_prob.isnot(None)
            )
        )

        if project_id:
            query = query.where(Document.project_id == project_id)

        query = query.order_by(Document.dominant_prob.desc()).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def update_topic_assignments(
        session: AsyncSession,
        document_topics: List[dict]
    ) -> int:
        """
        Bulk update topic assignments for documents.

        Args:
            session: Database session
            document_topics: List of dicts with document_id, dominant_topic, dominant_prob

        Returns:
            Number of updated documents
        """
        updated_count = 0
        for assignment in document_topics:
            doc_id = assignment.get("document_id")
            topic = assignment.get("dominant_topic")
            prob = assignment.get("dominant_prob")

            if doc_id is not None:
                document = await DocumentRepository.get_by_id(session, doc_id)
                if document:
                    document.dominant_topic = topic
                    document.dominant_prob = prob
                    updated_count += 1

        await session.flush()
        return updated_count
