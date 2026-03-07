"""
Pydantic schemas for FastAPI request/response validation
"""
from .auth import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    LoginResponse,
    MessageResponse
)
from .kdd import (
    PipelineStatus,
    StageStatus,
    DataCount,
    CrawlResults,
    KDDStatusResponse,
    Topic,
    DocumentTopic,
    CrawlStats,
    KDDResults,
    FullPipelineResponse,
    PreprocessingResponse,
    TransformResponse,
    DataMiningResponse
)
from .search import (
    DocumentMatch,
    SimilarDocument,
    OnlineDocument,
    SearchResultsResponse,
    SearchOnlineResponse,
    CrawlUrlRequest,
    CrawlUrlResponse,
    AddOnlineRequest,
    AddOnlineResponse,
    TrainLDARequest,
    TrainLDAResponse,
    SimilarDocumentsResponse,
    DocumentTopicsResponse,
    ModelStatusResponse
)
from .project import (
    ProjectResponse,
    ProjectCreate,
    ProjectStats,
    LoadProjectResponse,
    CloneProjectRequest,
    CloneProjectResponse
)

__all__ = [
    # Auth schemas
    "RegisterRequest",
    "LoginRequest",
    "UserResponse",
    "LoginResponse",
    "MessageResponse",
    # KDD schemas
    "PipelineStatus",
    "StageStatus",
    "DataCount",
    "CrawlResults",
    "KDDStatusResponse",
    "Topic",
    "DocumentTopic",
    "CrawlStats",
    "KDDResults",
    "FullPipelineResponse",
    "PreprocessingResponse",
    "TransformResponse",
    "DataMiningResponse",
    # Search schemas
    "DocumentMatch",
    "SimilarDocument",
    "OnlineDocument",
    "SearchResultsResponse",
    "SearchOnlineResponse",
    "CrawlUrlRequest",
    "CrawlUrlResponse",
    "AddOnlineRequest",
    "AddOnlineResponse",
    "TrainLDARequest",
    "TrainLDAResponse",
    "SimilarDocumentsResponse",
    "DocumentTopicsResponse",
    "ModelStatusResponse",
    # Project schemas
    "ProjectResponse",
    "ProjectCreate",
    "ProjectStats",
    "LoadProjectResponse",
    "CloneProjectRequest",
    "CloneProjectResponse",
]
