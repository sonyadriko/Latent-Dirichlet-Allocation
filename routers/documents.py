"""
Document router for FastAPI
Handles manual document input and document management
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.db_models import Document
from repositories.document_repository import DocumentRepository
from repositories.project_repository import ProjectRepository

router = APIRouter()


# Schemas
class ManualDocumentCreate(BaseModel):
    """Schema for creating a single manual document"""
    title: str = Field(..., min_length=1, max_length=500, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    project_id: Optional[int] = Field(None, description="Associated project ID (optional)")


class ManualDocumentBulkCreate(BaseModel):
    """Schema for creating multiple manual documents"""
    documents: List[dict] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of documents with 'title' and 'content' fields"
    )
    project_id: Optional[int] = Field(None, description="Associated project ID (optional)")


class ManualDocumentUpdate(BaseModel):
    """Schema for updating a manual document"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Document title")
    content: Optional[str] = Field(None, min_length=1, description="Document content")


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    title: str
    content: str
    url: Optional[str]
    tokens_count: int
    dominant_topic: Optional[int]
    dominant_prob: Optional[float]
    project_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response"""
    documents: List[DocumentResponse]
    total: int


class BulkCreateResponse(BaseModel):
    """Schema for bulk create response"""
    created_count: int
    documents: List[DocumentResponse]
    message: str


@router.post("/manual", response_model=DocumentResponse)
async def create_manual_document(
    document_data: ManualDocumentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a single manual document.

    Args:
        document_data: Document title and content
        current_user: Authenticated user
        session: Database session

    Returns:
        Created document
    """
    try:
        # Verify/create project if provided
        if document_data.project_id:
            project = await ProjectRepository.get_by_id(session, document_data.project_id)

            # If not in database, check JSON file and create in database
            if not project:
                from models.project import Project as JSONProject
                json_project = JSONProject.get_project_by_id(document_data.project_id)

                if json_project:
                    # Create project in database from JSON data
                    project = await ProjectRepository.create(
                        session=session,
                        name=json_project.name,
                        description=json_project.description,
                        num_topics=json_project.num_topics,
                        document_count=0,
                        coherence_score=json_project.coherence_score,
                        created_by=json_project.created_by
                    )
                    await session.flush()
                    print(f"Created project in database from JSON: {json_project.name} (ID: {project.id})")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Project with ID {document_data.project_id} not found"
                    )

        # Create document
        document = await DocumentRepository.create(
            session=session,
            title=document_data.title,
            content=document_data.content,
            url=None,  # Manual documents don't have URLs
            project_id=document_data.project_id
        )

        await session.commit()
        await session.refresh(document)

        # Update project document_count in JSON file if project_id is provided
        if document_data.project_id:
            try:
                from models.project import Project as JSONProject
                json_project = JSONProject.get_project_by_id(document_data.project_id)
                if json_project:
                    # Count actual documents in database for this project
                    doc_count = await DocumentRepository.count(
                        session=session,
                        project_id=document_data.project_id
                    )
                    # Update JSON project document_count
                    JSONProject.update_project_documents(
                        project_id=document_data.project_id,
                        source_urls=json_project.source_urls or [],
                        documents=json_project.documents or [],
                        num_topics=json_project.num_topics,
                        document_count=doc_count,
                        coherence_score=json_project.coherence_score
                    )
            except Exception as e:
                # Log error but don't fail the request
                print(f"Warning: Failed to update project document_count: {e}")

        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            url=document.url,
            tokens_count=document.tokens_count or 0,
            dominant_topic=document.dominant_topic,
            dominant_prob=document.dominant_prob,
            project_id=document.project_id,
            created_at=document.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating document: {str(e)}"
        )


@router.post("/manual/bulk", response_model=BulkCreateResponse)
async def create_manual_documents_bulk(
    bulk_data: ManualDocumentBulkCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create multiple manual documents at once.

    Args:
        bulk_data: List of documents and optional project_id
        current_user: Authenticated user
        session: Database session

    Returns:
        Created documents count and list
    """
    try:
        # Verify/create project if provided
        if bulk_data.project_id:
            project = await ProjectRepository.get_by_id(session, bulk_data.project_id)

            # If not in database, check JSON file and create in database
            if not project:
                from models.project import Project as JSONProject
                json_project = JSONProject.get_project_by_id(bulk_data.project_id)

                if json_project:
                    # Create project in database from JSON data
                    project = await ProjectRepository.create(
                        session=session,
                        name=json_project.name,
                        description=json_project.description,
                        num_topics=json_project.num_topics,
                        document_count=0,  # Will be updated after documents are created
                        coherence_score=json_project.coherence_score,
                        created_by=json_project.created_by
                    )
                    await session.flush()
                    print(f"Created project in database from JSON: {json_project.name} (ID: {project.id})")
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Project with ID {bulk_data.project_id} not found"
                    )

        # Validate document data
        for i, doc in enumerate(bulk_data.documents):
            if "title" not in doc or not doc["title"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document at index {i} is missing 'title' field"
                )
            if "content" not in doc or not doc["content"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Document at index {i} is missing 'content' field"
                )

        # Create documents in bulk
        documents = await DocumentRepository.create_bulk(
            session=session,
            documents=bulk_data.documents,
            project_id=bulk_data.project_id
        )

        await session.commit()

        # Refresh all documents to get their IDs
        for doc in documents:
            await session.refresh(doc)

        response_docs = [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                url=doc.url,
                tokens_count=doc.tokens_count or 0,
                dominant_topic=doc.dominant_topic,
                dominant_prob=doc.dominant_prob,
                project_id=doc.project_id,
                created_at=doc.created_at.isoformat()
            )
            for doc in documents
        ]

        # Update project document_count in JSON file if project_id is provided
        if bulk_data.project_id:
            try:
                from models.project import Project as JSONProject
                json_project = JSONProject.get_project_by_id(bulk_data.project_id)
                if json_project:
                    # Count actual documents in database for this project
                    doc_count = await DocumentRepository.count(
                        session=session,
                        project_id=bulk_data.project_id
                    )
                    # Update JSON project document_count
                    JSONProject.update_project_documents(
                        project_id=bulk_data.project_id,
                        source_urls=json_project.source_urls or [],
                        documents=json_project.documents or [],
                        num_topics=json_project.num_topics,
                        document_count=doc_count,
                        coherence_score=json_project.coherence_score
                    )
            except Exception as e:
                # Log error but don't fail the request
                print(f"Warning: Failed to update project document_count: {e}")

        return BulkCreateResponse(
            created_count=len(documents),
            documents=response_docs,
            message=f"Successfully created {len(documents)} documents"
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating documents: {str(e)}"
        )


@router.get("/manual", response_model=DocumentListResponse)
async def get_manual_documents(
    project_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get manual documents for a project.

    Args:
        project_id: Filter by project (optional)
        limit: Maximum number of results
        offset: Number of results to skip
        current_user: Authenticated user
        session: Database session

    Returns:
        List of documents
    """
    try:
        documents = await DocumentRepository.list_documents(
            session=session,
            project_id=project_id,
            limit=limit,
            offset=offset
        )

        response_docs = [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                url=doc.url,
                tokens_count=doc.tokens_count or 0,
                dominant_topic=doc.dominant_topic,
                dominant_prob=doc.dominant_prob,
                project_id=doc.project_id,
                created_at=doc.created_at.isoformat()
            )
            for doc in documents
        ]

        # Return in consistent format with other endpoints
        return {
            'success': True,
            'documents': response_docs,
            'total': len(response_docs)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving documents: {str(e)}"
        )


@router.delete("/manual/{document_id}")
async def delete_manual_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a manual document.

    Args:
        document_id: ID of document to delete
        current_user: Authenticated user
        session: Database session

    Returns:
        Success message
    """
    try:
        # Check if document exists
        document = await DocumentRepository.get_by_id(session, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found"
            )

        # Delete document
        success = await DocumentRepository.delete(session, document_id)

        if success:
            await session.commit()
            return {
                "success": True,
                "message": f"Document '{document.title}' deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.put("/manual/{document_id}", response_model=DocumentResponse)
async def update_manual_document(
    document_id: int,
    update_data: ManualDocumentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a manual document's title or content.

    Args:
        document_id: ID of document to update
        update_data: Fields to update (title, content)
        current_user: Authenticated user
        session: Database session

    Returns:
        Updated document
    """
    try:
        # Check if document exists
        existing_doc = await DocumentRepository.get_by_id(session, document_id)
        if not existing_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found"
            )

        # Update document
        updated_doc = await DocumentRepository.update(
            session=session,
            document_id=document_id,
            title=update_data.title,
            content=update_data.content
        )

        if updated_doc:
            await session.commit()
            return DocumentResponse(
                id=updated_doc.id,
                title=updated_doc.title,
                content=updated_doc.content,
                url=updated_doc.url,
                tokens_count=updated_doc.tokens_count or 0,
                dominant_topic=updated_doc.dominant_topic,
                dominant_prob=updated_doc.dominant_prob,
                project_id=updated_doc.project_id,
                created_at=updated_doc.created_at.isoformat()
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update document"
            )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating document: {str(e)}"
        )


@router.post("/manual/{document_id}/add-to-project")
async def add_document_to_project(
    document_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Add a standalone document to a project.

    Args:
        document_id: ID of document to add
        project_id: ID of project to add to
        current_user: Authenticated user
        session: Database session

    Returns:
        Success message
    """
    try:
        # Check if document exists
        document = await DocumentRepository.get_by_id(session, document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found"
            )

        # Check if project exists
        project = await ProjectRepository.get_by_id(session, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )

        # Update document's project
        updated_doc = await DocumentRepository.update(
            session=session,
            document_id=document_id,
            project_id=project_id
        )

        if updated_doc:
            await session.commit()

            # Update project document count
            await ProjectRepository.update_document_count(session, project_id)
            await session.commit()

            return {
                "success": True,
                "message": f"Document '{document.title}' added to project '{project.name}'"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add document to project"
            )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding document to project: {str(e)}"
        )
