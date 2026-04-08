"""
SQLAlchemy ORM Models for LDA Application

Defines the database schema for:
- Users
- Projects
- Pipeline Runs
- Documents
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class User(Base):
    """
    User model for authentication and project ownership.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="created_by_user",
        lazy="selectin"
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="user",
        lazy="selectin"
    )

    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding password)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Project(Base):
    """
    Project model for LDA model management.
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    num_topics: Mapped[int] = mapped_column(Integer, default=5)
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    coherence_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Model storage
    model_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, archived, deleted

    # Foreign keys
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="projects",
        lazy="selectin"
    )
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun",
        back_populates="project",
        lazy="selectin",
        order_by="desc(PipelineRun.started_at)"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Convert project to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "num_topics": self.num_topics,
            "document_count": self.document_count,
            "coherence_score": self.coherence_score,
            "model_path": self.model_path,
            "status": self.status,
            "created_by": self.created_by,
            "created_by_user": self.created_by_user.to_dict() if self.created_by_user else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PipelineRun(Base):
    """
    Pipeline run model for tracking KDD pipeline execution.
    Replaces the in-memory kdd_state with persistent storage.
    """
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Pipeline status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending"  # pending, running, completed, error, cancelled
    )

    # Individual stage statuses
    crawling_status: Mapped[str] = mapped_column(String(20), default="pending")
    preprocessing_status: Mapped[str] = mapped_column(String(20), default="pending")
    transforming_status: Mapped[str] = mapped_column(String(20), default="pending")
    datamining_status: Mapped[str] = mapped_column(String(20), default="pending")

    # Configuration
    num_topics: Mapped[int] = mapped_column(Integer, default=5)

    # Results metadata
    total_urls: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="pipeline_runs",
        lazy="selectin"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="pipeline_runs",
        lazy="selectin"
    )

    def to_dict(self) -> dict:
        """Convert pipeline run to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "status": self.status,
            "crawling_status": self.crawling_status,
            "preprocessing_status": self.preprocessing_status,
            "transforming_status": self.transforming_status,
            "datamining_status": self.datamining_status,
            "num_topics": self.num_topics,
            "total_urls": self.total_urls,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "error_message": self.error_message,
            "error_stage": self.error_stage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self._get_duration()
        }

    def _get_duration(self) -> Optional[float]:
        """Calculate pipeline duration in seconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None


class Document(Base):
    """
    Document model for storing crawled and processed documents.
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Document content
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Processing metadata
    tokens_count: Mapped[int] = mapped_column(Integer, default=0)
    dominant_topic: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dominant_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Foreign key
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="documents",
        lazy="selectin"
    )

    def to_dict(self) -> dict:
        """Convert document to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:500] + "..." if self.content and len(self.content) > 500 else self.content,
            "url": self.url,
            "tokens_count": self.tokens_count,
            "dominant_topic": self.dominant_topic,
            "dominant_prob": self.dominant_prob,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_full(self) -> dict:
        """Convert document to dictionary with full content."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "tokens_count": self.tokens_count,
            "dominant_topic": self.dominant_topic,
            "dominant_prob": self.dominant_prob,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
