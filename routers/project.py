"""
Project router for FastAPI
Handles project management for LDA models (MySQL-backed).
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.lda_service import LDAService
from services.lda_singleton import get_lda_service
from core.security import get_current_user
from core.database import get_session
from core.exceptions import NotFoundException
from models.db_models import User
from repositories.project_repository import ProjectRepository
from repositories.document_repository import DocumentRepository

router = APIRouter()

# Use singleton LDA service - shared across all routers
lda_service = get_lda_service()


async def _load_project_into_service(session: AsyncSession, project) -> tuple[bool, str]:
    """
    Load a DB project's Gensim model into the LDA service, passing the project's
    documents so the corpus can be rebuilt when needed.
    """
    documents = await DocumentRepository.list_documents(
        session, project_id=project.id, limit=10000
    )
    docs_data = [
        {"id": d.id, "title": d.title, "content": d.content, "url": d.url}
        for d in documents
    ]
    return lda_service.load_project_model(
        project_name=project.name,
        project_id=project.id,
        document_count=project.document_count,
        documents=docs_data,
    )


@router.get("/")
async def get_projects(session: AsyncSession = Depends(get_session)):
    """Get All Projects"""
    try:
        projects = await ProjectRepository.list_projects(session, status="active")
        return {
            'success': True,
            'data': [project.to_dict() for project in projects],
            'message': f'Found {len(projects)} projects'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting projects: {str(e)}'
        }


@router.post("/")
async def create_project(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new project.

    Request body:
    - name: Project name (required)
    - description: Project description (optional)
    - num_topics: Number of topics for LDA (optional, default: 5)
    """
    try:
        from pydantic import BaseModel, Field

        class ProjectCreateRequest(BaseModel):
            name: str = Field(..., min_length=2, max_length=100)
            description: str = Field(default="")
            num_topics: int = Field(default=5, ge=1, le=50)

        data = await request.json()
        project_req = ProjectCreateRequest(**data)

        if await ProjectRepository.name_exists(session, project_req.name):
            return {
                'success': False,
                'message': 'Project name already exists'
            }

        project = await ProjectRepository.create(
            session=session,
            name=project_req.name,
            description=project_req.description,
            num_topics=project_req.num_topics,
            document_count=0,
            coherence_score=0.0,
            created_by=current_user.id
        )

        return {
            'success': True,
            'data': project.to_dict(),
            'message': f'Project "{project.name}" created successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error creating project: {str(e)}'
        }


@router.get("/list")
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all projects for the admin UI"""
    try:
        projects = await ProjectRepository.list_projects(session)
        return {
            'success': True,
            'data': [p.to_dict() for p in projects],
            'message': f'Found {len(projects)} projects'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error listing projects: {str(e)}'
        }


@router.get("/stats/overview")
async def get_project_stats(session: AsyncSession = Depends(get_session)):
    """Get Project Statistics"""
    try:
        stats = await ProjectRepository.get_stats(session)
        # Serialize recent project ORM objects
        stats['recent_projects'] = [p.to_dict() for p in stats.get('recent_projects', [])]
        return {
            'success': True,
            'data': stats,
            'message': 'Project statistics retrieved successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting project stats: {str(e)}'
        }


@router.get("/{project_id}")
async def get_project(project_id: int, session: AsyncSession = Depends(get_session)):
    """Get Project by ID"""
    try:
        project = await ProjectRepository.get_by_id(session, project_id)

        if not project:
            return {
                'success': False,
                'message': 'Project not found'
            }

        return {
            'success': True,
            'data': project.to_dict(),
            'message': 'Project found successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting project: {str(e)}'
        }


@router.post("/{project_id}/load")
async def load_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Load Project Model"""
    try:
        project = await ProjectRepository.get_by_id(session, project_id)

        if not project:
            return {
                'success': False,
                'message': 'Project not found'
            }

        success, message = await _load_project_into_service(session, project)

        if success:
            return {
                'success': True,
                'data': {
                    'project': project.to_dict(),
                    'model_loaded': True,
                    'message': message
                },
                'message': f'Successfully loaded project: {project.name}'
            }
        else:
            return {
                'success': False,
                'message': message
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error loading project: {str(e)}'
        }


async def _delete_project(project_id: int, session: AsyncSession):
    """Shared delete logic: remove model files + DB row (cascades docs/runs)."""
    project = await ProjectRepository.get_by_id(session, project_id)
    if not project:
        raise NotFoundException("Project", project_id)

    if project.name:
        LDAService.delete_project_files(project.name)

    success = await ProjectRepository.delete(session, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete project from database'
        )
    return project.name


@router.delete("/{project_id}/delete")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete Project (and its documents/pipeline runs via cascade)."""
    try:
        name = await _delete_project(project_id, session)
        return {
            'success': True,
            'message': f'Project "{name}" deleted successfully'
        }
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error deleting project: {str(e)}'
        )


@router.delete("/{project_id}/delete-db")
async def delete_project_db(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete Project from Database (alias of /delete)."""
    return await delete_project(project_id, current_user, session)


@router.post("/{project_id}/clone")
async def clone_project(
    project_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Clone Project (metadata only; train to complete)."""
    try:
        data = await request.json()

        original = await ProjectRepository.get_by_id(session, project_id)
        if not original:
            return {
                'success': False,
                'message': 'Original project not found'
            }

        new_name = data.get('name', f"{original.name} (Copy)")
        new_description = data.get('description', f"Clone of {original.description or ''}")
        new_num_topics = data.get('num_topics', original.num_topics)

        if await ProjectRepository.name_exists(session, new_name):
            return {
                'success': False,
                'message': 'Project name already exists'
            }

        new_project = await ProjectRepository.create(
            session=session,
            name=new_name,
            description=new_description,
            num_topics=new_num_topics,
            document_count=0,
            coherence_score=0.0,
            created_by=current_user.id
        )

        return {
            'success': True,
            'data': {
                'new_project': new_project.to_dict(),
                'original_project': original.to_dict()
            },
            'message': f'Project cloned as "{new_name}". Train with documents to complete the clone.'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error cloning project: {str(e)}'
        }


@router.get("/{project_id}/documents")
async def get_project_documents(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get documents for a specific project."""
    try:
        project = await ProjectRepository.get_by_id(session, project_id)
        if not project:
            return {
                'success': False,
                'message': f'Project with ID {project_id} not found'
            }

        documents = await DocumentRepository.list_documents(
            session, project_id=project_id, limit=10000
        )

        return {
            'success': True,
            'data': {
                'project': project.to_dict(),
                'documents': [doc.to_dict() for doc in documents],
                'total': len(documents)
            },
            'message': f'Found {len(documents)} documents for project: {project.name}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting documents: {str(e)}'
        }


@router.get("/{project_id}/pyldavis")
async def get_project_pyldavis(
    project_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get pyLDAvis visualization data for a specific project."""
    try:
        project = await ProjectRepository.get_by_id(session, project_id)
        if not project:
            return {
                'success': False,
                'message': f'Project with ID {project_id} not found'
            }

        success, message = await _load_project_into_service(session, project)
        if not success:
            return {
                'success': False,
                'message': f'Failed to load project model: {message}'
            }

        pyldavis_data = lda_service.get_pyldavis_data()

        if pyldavis_data is None:
            return {
                'success': False,
                'message': 'Failed to prepare pyLDAvis visualization data. The model may not have been trained properly.'
            }

        return {
            'success': True,
            'data': pyldavis_data,
            'project': project.to_dict(),
            'message': f'pyLDAvis data prepared for project: {project.name}'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error preparing pyLDAvis data: {str(e)}'
        }
