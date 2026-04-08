"""
Pydantic Schemas for KDD Pipeline Operations

Defines request/response schemas for pipeline endpoints.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, validator


class PipelineStatus(str, Enum):
    """Pipeline status enum."""
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"
    cancelled = "cancelled"


class StageStatus(str, Enum):
    """Individual pipeline stage status."""
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"
    skipped = "skipped"


# Request Schemas
class PipelineRunRequest(BaseModel):
    """Request to start a pipeline run."""
    project_name: str = Field(..., min_length=1, max_length=100, description="Project name")
    num_topics: int = Field(default=5, ge=1, le=50, description="Number of topics for LDA")

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Business News Analysis",
                "num_topics": 5
            }
        }


class PipelineStageRequest(BaseModel):
    """Request to execute a specific pipeline stage."""
    force: bool = Field(
        default=False,
        description="Force re-run even if stage is already completed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "force": False
            }
        }


class CrawlRequest(BaseModel):
    """Request for crawling stage."""
    project_name: str = Field(..., min_length=1, max_length=100)
    num_topics: int = Field(default=5, ge=1, le=50)

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Business News Analysis",
                "num_topics": 5
            }
        }


class DataminingRequest(BaseModel):
    """Request for data mining stage."""
    num_topics: int = Field(default=5, ge=1, le=50, description="Number of topics for LDA")

    class Config:
        json_schema_extra = {
            "example": {
                "num_topics": 5
            }
        }


# Response Schemas
class PipelineStatusResponse(BaseModel):
    """Response with current pipeline status."""
    project_name: Optional[str] = None
    status: PipelineStatus = Field(description="Overall pipeline status")
    data_count: dict = Field(description="Count of items at each stage")
    crawl_results: Optional[dict] = Field(default=None, description="Crawling results summary")

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "Business News Analysis",
                "status": "running",
                "data_count": {
                    "raw": 100,
                    "selected": 95,
                    "preprocessed": 0
                },
                "crawl_results": {
                    "success_count": 95,
                    "failed_count": 5
                }
            }
        }


class PipelineRunResponse(BaseModel):
    """Response with pipeline run details."""
    id: int
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    status: PipelineStatus
    crawling_status: StageStatus
    preprocessing_status: StageStatus
    transforming_status: StageStatus
    datamining_status: StageStatus
    num_topics: int
    total_urls: int = 0
    success_count: int = 0
    failed_count: int = 0
    error_message: Optional[str] = None
    error_stage: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "project_id": 1,
                "user_id": 1,
                "status": "completed",
                "crawling_status": "completed",
                "preprocessing_status": "completed",
                "transforming_status": "completed",
                "datamining_status": "completed",
                "num_topics": 5,
                "total_urls": 100,
                "success_count": 95,
                "failed_count": 5,
                "error_message": None,
                "error_stage": None,
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:05:00Z",
                "duration_seconds": 300.0
            }
        }


class PipelineStageResult(BaseModel):
    """Result of a pipeline stage execution."""
    success: bool
    message: str
    stage: str = Field(description="Stage name (crawling, preprocessing, etc.)")
    data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Stage completed successfully",
                "stage": "crawling",
                "data": {
                    "total": 100,
                    "success_count": 95,
                    "failed_count": 5
                }
            }
        }


class PipelineResultsResponse(BaseModel):
    """Response with LDA results from pipeline."""
    success: bool
    data: dict = Field(description="LDA results including topics, coherence, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "project_name": "Business News Analysis",
                    "num_topics": 5,
                    "topics": [],
                    "coherence_score": 0.45,
                    "topic_distribution": {},
                    "document_topics": [],
                    "documents": []
                }
            }
        }


class CrawlResultItem(BaseModel):
    """Single crawl result item."""
    url: str
    title: Optional[str] = None
    success: bool
    error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "title": "Article Title",
                "success": True,
                "error": None
            }
        }


class CrawlResultsResponse(BaseModel):
    """Response with crawling results."""
    success: bool
    message: str
    data: dict = Field(description="Crawling statistics and sample results")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Crawling completed successfully",
                "data": {
                    "total": 100,
                    "success_count": 95,
                    "failed_count": 5,
                    "sample": []
                }
            }
        }


class PreprocessingResult(BaseModel):
    """Response from preprocessing stage."""
    success: bool
    message: str
    data: dict = Field(description="Preprocessing statistics and sample")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Preprocessing completed successfully",
                "data": {
                    "total_documents": 100,
                    "sample": []
                }
            }
        }


class TransformResult(BaseModel):
    """Response from transforming stage."""
    success: bool
    message: str
    data: dict = Field(description="Transformation statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Transformation completed successfully",
                "data": {
                    "dictionary_size": 5000,
                    "corpus_size": 100,
                    "sample_bow": []
                }
            }
        }


class DataminingResult(BaseModel):
    """Response from data mining stage."""
    success: bool
    message: str
    data: dict = Field(description="LDA model results")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Data mining completed successfully",
                "data": {
                    "num_topics": 5,
                    "topics": [],
                    "coherence_score": 0.45,
                    "topic_distribution": {}
                }
            }
        }
