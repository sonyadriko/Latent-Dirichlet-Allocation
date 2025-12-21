from flask import Blueprint, request, jsonify
from models.project import Project
from services.lda_service import LDAService
from services.search_service import SearchService
from routes.auth import token_required

project_bp = Blueprint('project', __name__)

# Global LDA service instance
lda_service = LDAService()

@project_bp.route('/', methods=['GET'])
def get_projects():
    """Get all available projects"""
    try:
        projects = Project.get_all_projects()
        return jsonify({
            'success': True,
            'data': [project.to_dict() for project in projects],
            'message': f'Found {len(projects)} projects'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting projects: {str(e)}'
        }), 500

@project_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get specific project details"""
    try:
        project = Project.get_project_by_id(project_id)
        
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': project.to_dict(),
            'message': 'Project found successfully'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting project: {str(e)}'
        }), 500

@project_bp.route('/<int:project_id>/load', methods=['POST'])
@token_required
def load_project(current_user, project_id):
    """Load a specific project's LDA model"""
    try:
        project = Project.get_project_by_id(project_id)
        
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project not found'
            }), 404
        
        # Load the project model
        success, message = lda_service.switch_to_project(project_id)
        
        if success:
            return jsonify({
                'success': True,
                'data': {
                    'project': project.to_dict(),
                    'model_loaded': True,
                    'message': message
                },
                'message': f'Successfully loaded project: {project.name}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error loading project: {str(e)}'
        }), 500

@project_bp.route('/<int:project_id>/delete', methods=['DELETE'])
@token_required
def delete_project(current_user, project_id):
    """Delete (deactivate) a project"""
    try:
        project = Project.get_project_by_id(project_id)
        
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project not found'
            }), 404
        
        # Delete the project
        success = Project.delete_project(project_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Project "{project.name}" deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to delete project'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting project: {str(e)}'
        }), 500

@project_bp.route('/<int:project_id>/clone', methods=['POST'])
@token_required
def clone_project(current_user, project_id):
    """Clone a project with different settings"""
    try:
        data = request.get_json()
        
        original_project = Project.get_project_by_id(project_id)
        if not original_project:
            return jsonify({
                'success': False,
                'message': 'Original project not found'
            }), 404
        
        new_name = data.get('name', f"{original_project.name} (Copy)")
        new_description = data.get('description', f"Clone of {original_project.description}")
        num_topics = data.get('num_topics', original_project.num_topics)
        
        # Create new project (but don't train yet)
        new_project, error = Project.create(
            name=new_name,
            description=new_description,
            num_topics=num_topics,
            document_count=0,  # Will be updated after training
            coherence_score=0.0,  # Will be updated after training
            created_by=current_user.id
        )
        
        if error:
            return jsonify({
                'success': False,
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'new_project': new_project.to_dict(),
                'original_project': original_project.to_dict()
            },
            'message': f'Project cloned as "{new_name}". Train with documents to complete the clone.'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error cloning project: {str(e)}'
        }), 500

@project_bp.route('/stats', methods=['GET'])
def get_project_stats():
    """Get overall project statistics"""
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
        
        return jsonify({
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
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error getting project stats: {str(e)}'
        }), 500