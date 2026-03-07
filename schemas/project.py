"""
Pydantic schemas for Project Management
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProjectResponse(BaseModel):
    """Schema for project response"""
    id: int
    name: str
    description: str
    num_topics: int
    document_count: int
    coherence_score: float
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    name: str = Field(..., min_length=2, max_length=100, description="Project name")
    description: str = Field(default="", max_length=500, description="Project description")
    num_topics: int = Field(default=5, ge=1, le=50, description="Number of topics")


class ProjectStats(BaseModel):
    """Schema for project statistics"""
    total_projects: int
    total_documents: int
    average_coherence: float
    total_topics: int
    topic_distribution: Dict[int, int]
    recent_projects: List[ProjectResponse]


class LoadProjectResponse(BaseModel):
    """Schema for load project response"""
    model_config = {"protected_namespaces": ()}

    project: ProjectResponse
    model_loaded: bool
    message: str


class CloneProjectRequest(BaseModel):
    """Schema for clone project request"""
    name: Optional[str] = Field(None, description="Name for cloned project")
    description: Optional[str] = Field(None, description="Description for cloned project")
    num_topics: Optional[int] = Field(None, ge=1, le=50, description="Number of topics")


class CloneProjectResponse(BaseModel):
    """Schema for clone project response"""
    new_project: ProjectResponse
    original_project: ProjectResponse
