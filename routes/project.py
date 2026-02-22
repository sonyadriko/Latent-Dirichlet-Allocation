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
    """
    Get All Projects
    ---
    tags:
      - Projects
    responses:
      200:
        description: Daftar semua projects
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: Analisa Berita Ekonomi
                  description:
                    type: string
                    example: Topic modeling pada berita ekonomi Indonesia
                  num_topics:
                    type: integer
                    example: 5
                  document_count:
                    type: integer
                    example: 45
                  coherence_score:
                    type: number
                    format: float
                    example: 0.523
                  created_at:
                    type: string
                    format: date-time
            message:
              type: string
              example: Found 3 projects
    """
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
    """
    Get Project by ID
    ---
    tags:
      - Projects
    parameters:
      - in: path
        name: project_id
        type: integer
        required: true
        description: Project ID
        example: 1
    responses:
      200:
        description: Detail project
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                description:
                  type: string
                num_topics:
                  type: integer
                document_count:
                  type: integer
                coherence_score:
                  type: number
                  format: float
            message:
              type: string
              example: Project found successfully
      404:
        description: Project tidak ditemukan
    """
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
    """
    Load Project Model
    ---
    tags:
      - Projects
    security:
      - Bearer: []
    parameters:
      - in: path
        name: project_id
        type: integer
        required: true
        description: Project ID untuk diload model-nya
        example: 1
    responses:
      200:
        description: Project model berhasil diload
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                project:
                  type: object
                model_loaded:
                  type: boolean
                  example: true
                message:
                  type: string
            message:
              type: string
              example: Successfully loaded project: Analisa Berita
      404:
        description: Project tidak ditemukan
      401:
        description: Unauthorized
    """
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
    """
    Delete Project
    ---
    tags:
      - Projects
    security:
      - Bearer: []
    parameters:
      - in: path
        name: project_id
        type: integer
        required: true
        description: Project ID untuk dihapus
        example: 1
    responses:
      200:
        description: Project berhasil dihapus
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            message:
              type: string
              example: Project "Analisa Berita" deleted successfully
      404:
        description: Project tidak ditemukan
      401:
        description: Unauthorized
    """
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
    """
    Clone Project
    ---
    tags:
      - Projects
    security:
      - Bearer: []
    parameters:
      - in: path
        name: project_id
        type: integer
        required: true
        description: Project ID asal untuk di-clone
        example: 1
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
              example: Analisa Berita (Copy)
              description: Nama untuk project baru
            description:
              type: string
              example: Clone of Analisa Berita
              description: Deskripsi untuk project baru
            num_topics:
              type: integer
              example: 5
              description: Jumlah topik (default: sama dengan original)
    responses:
      200:
        description: Project berhasil di-clone
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                new_project:
                  type: object
                original_project:
                  type: object
            message:
              type: string
              example: Project cloned as "Analisa Berita (Copy)". Train with documents to complete the clone.
      404:
        description: Original project tidak ditemukan
      401:
        description: Unauthorized
    """
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
    """
    Get Project Statistics
    ---
    tags:
      - Projects
    responses:
      200:
        description: Statistik project secara keseluruhan
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                total_projects:
                  type: integer
                  example: 5
                total_documents:
                  type: integer
                  example: 234
                average_coherence:
                  type: number
                  format: float
                  example: 0.487
                total_topics:
                  type: integer
                  example: 25
                topic_distribution:
                  type: object
                  example: {"5": 3, "10": 2}
                  description: Distribusi jumlah topik per project
                recent_projects:
                  type: array
                  items:
                    type: object
                  description: 5 project terbaru
            message:
              type: string
              example: Project statistics retrieved successfully
    """
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
