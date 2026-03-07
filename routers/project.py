"""
Project router for FastAPI
Handles project management for LDA models
"""
from typing import Optional
from fastapi import APIRouter, Request, Depends
from models.project import Project
from services.lda_service import LDAService
from core.security import get_current_user
from models.user import User

router = APIRouter()

# Global LDA service instance
lda_service = LDAService()


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
async def delete_project(project_id: int, current_user: User = Depends(get_current_user)):
    """Delete Project"""
    try:
        project = Project.get_project_by_id(project_id)

        if not project:
            return {
                'success': False,
                'message': 'Project not found'
            }

        # Delete the project
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
