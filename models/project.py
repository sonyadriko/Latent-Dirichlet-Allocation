import json
import os
from datetime import datetime
from config import Config

class Project:
    PROJECTS_FILE = os.path.join(Config.DATA_DIR, 'projects.json')
    
    def __init__(self, id, name, description, num_topics, document_count, coherence_score, created_by=None):
        self.id = id
        self.name = name
        self.description = description
        self.num_topics = num_topics
        self.document_count = document_count
        self.coherence_score = coherence_score
        self.created_by = created_by
        self.created_at = datetime.now().isoformat()
        self.model_path = None
        self.status = 'active'
    
    @staticmethod
    def _load_projects():
        """Load all projects from JSON file"""
        if os.path.exists(Project.PROJECTS_FILE):
            with open(Project.PROJECTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def _save_projects(projects):
        """Save projects to JSON file"""
        os.makedirs(os.path.dirname(Project.PROJECTS_FILE), exist_ok=True)
        with open(Project.PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def create(name, description, num_topics, document_count, coherence_score, created_by=None):
        """Create a new project"""
        projects = Project._load_projects()
        
        # Check if project name already exists
        if any(p['name'].lower() == name.lower() for p in projects):
            return None, "Project name already exists"
        
        # Generate new ID
        new_id = max([p['id'] for p in projects], default=0) + 1
        
        # Create new project
        project = Project(new_id, name, description, num_topics, document_count, coherence_score, created_by)
        project.model_path = f"project_{new_id}_model"
        
        # Add to projects list
        projects.append(project.to_dict())
        Project._save_projects(projects)
        
        return project, None
    
    @staticmethod
    def get_all_projects():
        """Get all projects"""
        projects = Project._load_projects()
        return [Project.from_dict(p) for p in projects if p['status'] == 'active']
    
    @staticmethod
    def get_project_by_id(project_id):
        """Get project by ID"""
        projects = Project._load_projects()
        for p in projects:
            if p['id'] == project_id and p['status'] == 'active':
                return Project.from_dict(p)
        return None
    
    @staticmethod
    def get_project_by_name(name):
        """Get project by name"""
        projects = Project._load_projects()
        for p in projects:
            if p['name'].lower() == name.lower() and p['status'] == 'active':
                return Project.from_dict(p)
        return None
    
    @staticmethod
    def delete_project(project_id):
        """Delete (deactivate) a project"""
        projects = Project._load_projects()
        for p in projects:
            if p['id'] == project_id:
                p['status'] = 'deleted'
                p['deleted_at'] = datetime.now().isoformat()
                break
        
        Project._save_projects(projects)
        return True
    
    def to_dict(self):
        """Convert project to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'num_topics': self.num_topics,
            'document_count': self.document_count,
            'coherence_score': self.coherence_score,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'model_path': self.model_path,
            'status': self.status
        }
    
    @staticmethod
    def from_dict(data):
        """Create project from dictionary"""
        project = Project(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            num_topics=data['num_topics'],
            document_count=data['document_count'],
            coherence_score=data['coherence_score'],
            created_by=data.get('created_by')
        )
        project.created_at = data.get('created_at')
        project.model_path = data.get('model_path')
        project.status = data.get('status', 'active')
        return project