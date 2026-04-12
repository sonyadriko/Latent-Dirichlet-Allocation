"""
Project router for FastAPI
Handles project management for LDA models
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from models.project import Project
from services.lda_service import LDAService
from services.lda_singleton import get_lda_service
from core.security import get_current_user
from core.database import get_session
from models.user import User
from core.exceptions import NotFoundException

router = APIRouter()

# Use singleton LDA service - shared across all routers
lda_service = get_lda_service()


@router.get("/")
async def get_projects():
    """Get All Projects"""
    try:
        projects = Project.get_all_projects()
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


@router.get("/list")
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all projects for the admin UI"""
    from repositories.project_repository import ProjectRepository

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


@router.get("/{project_id}")
async def get_project(project_id: int):
    """Get Project by ID"""
    try:
        project = Project.get_project_by_id(project_id)

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
async def load_project(project_id: int, current_user: User = Depends(get_current_user)):
    """Load Project Model"""
    try:
        project = Project.get_project_by_id(project_id)

        if not project:
            return {
                'success': False,
                'message': 'Project not found'
            }

        # Load the project model
        success, message = lda_service.switch_to_project(project_id)

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


@router.delete("/{project_id}/delete")
async def delete_project(project_id: int):
    """Delete Project (JSON-based for backward compatibility)"""
    try:
        project = Project.get_project_by_id(project_id)

        if not project:
            return {
                'success': False,
                'message': f'Project not found: {project_id}'
            }

        # Delete model files from filesystem
        if project.name:
            LDAService.delete_project_files(project.name)

        # Delete from JSON file
        success = Project.delete_project(project_id)

        if success:
            return {
                'success': True,
                'message': f'Project "{project.name}" deleted successfully'
            }
        else:
            return {
                'success': False,
                'message': 'Failed to delete project'
            }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error deleting project: {str(e)}'
        }


@router.delete("/{project_id}/delete-db")
async def delete_project_db(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete Project from Database"""
    from repositories.project_repository import ProjectRepository

    try:
        # Get project first
        project = await ProjectRepository.get_by_id(session, project_id)
        if not project:
            raise NotFoundException("Project", project_id)

        # Delete model files from filesystem
        if project.name:
            LDAService.delete_project_files(project.name)

        # Delete from database (cascade deletes documents, pipeline_runs)
        success = await ProjectRepository.delete(session, project_id)

        if success:
            return {
                'success': True,
                'message': f'Project "{project.name}" deleted successfully'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to delete project from database'
            )

    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error deleting project: {str(e)}'
        )


@router.post("/{project_id}/clone")
async def clone_project(project_id: int, request: Request, current_user: User = Depends(get_current_user)):
    """Clone Project"""
    try:
        data = await request.json()

        original_project = Project.get_project_by_id(project_id)
        if not original_project:
            return {
                'success': False,
                'message': 'Original project not found'
            }

        new_name = data.get('name', f"{original_project.name} (Copy)")
        new_description = data.get('description', f"Clone of {original_project.description}")
        new_num_topics = data.get('num_topics', original_project.num_topics)

        # Create new project (but don't train yet)
        new_project, error = Project.create(
            name=new_name,
            description=new_description,
            num_topics=new_num_topics,
            document_count=0,
            coherence_score=0.0,
            created_by=current_user.id
        )

        if error:
            return {
                'success': False,
                'message': error
            }

        return {
            'success': True,
            'data': {
                'new_project': new_project.to_dict(),
                'original_project': original_project.to_dict()
            },
            'message': f'Project cloned as "{new_name}". Train with documents to complete the clone.'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error cloning project: {str(e)}'
        }


@router.get("/stats/overview")
async def get_project_stats():
    """Get Project Statistics"""
    try:
        projects = Project.get_all_projects()

        total_projects = len(projects)
        total_documents = sum(p.document_count for p in projects)
        avg_coherence = sum(p.coherence_score for p in projects) / total_projects if total_projects > 0 else 0
        total_topics = sum(p.num_topics for p in projects)

        # Topic distribution
        topic_dist = {}
        for project in projects:
            topic_dist[project.num_topics] = topic_dist.get(project.num_topics, 0) + 1

        return {
            'success': True,
            'data': {
                'total_projects': total_projects,
                'total_documents': total_documents,
                'average_coherence': round(avg_coherence, 3),
                'total_topics': total_topics,
                'topic_distribution': topic_dist,
                'recent_projects': [p.to_dict() for p in sorted(projects, key=lambda x: x.created_at, reverse=True)[:5]]
            },
            'message': 'Project statistics retrieved successfully'
        }

    except Exception as e:
        return {
            'success': False,
            'message': f'Error getting project stats: {str(e)}'
        }


@router.get("/{project_id}/pyldavis")
async def get_project_pyldavis(project_id: int):
    """
    Get pyLDAvis visualization data for a specific project.

    Args:
        project_id: ID of the project

    Returns JSON data compatible with pyLDAvis JavaScript visualization.
    """
    try:
        # Get project
        project = Project.get_project_by_id(project_id)

        if not project:
            return {
                'success': False,
                'message': f'Project with ID {project_id} not found'
            }

        # Load project model
        success, message = lda_service.load_project_model(project_id=project_id)

        if not success:
            return {
                'success': False,
                'message': f'Failed to load project model: {message}'
            }

        # Try to load preprocessed data for the project if available
        import os
        import json
        from config import Config

        project_folder = os.path.join(Config.RESULTS_DIR, project.name.replace(' ', '_').lower())
        data_file = os.path.join(project_folder, f'{project.name}_data.json')

        corpus = None
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                    # Reconstruct corpus from preprocessed data
                    if 'preprocessed_data' in project_data:
                        from services.preprocessing import TextPreprocessor
                        preprocessor = TextPreprocessor()
                        preprocessed_docs = [item['tokens'] for item in project_data['preprocessed_data']]
                        corpus = [lda_service.dictionary.doc2bow(doc) for doc in preprocessed_docs]
            except Exception as e:
                print(f"Warning: Could not load corpus from project data: {e}")

        # Prepare pyLDAvis data
        pyldavis_data = lda_service.get_pyldavis_data(corpus=corpus)

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
