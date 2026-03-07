"""
Pydantic schemas for Search
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DocumentMatch(BaseModel):
    """Schema for document match"""
    id: int
    title: str
    url: Optional[str]
    combined_score: float
    title_match: bool
    content_match: bool


class SimilarDocument(BaseModel):
    """Schema for similar document"""
    id: int
    title: str
    similarity: float


class OnlineDocument(BaseModel):
    """Schema for online document"""
    title: str
    url: str
    source: str
    snippet: Optional[str]


class SearchResultsResponse(BaseModel):
    """Schema for search results response"""
    query: str
    matches: List[DocumentMatch]
    best_match: Optional[DocumentMatch]
    similar_documents: List[SimilarDocument]
    online_documents: List[OnlineDocument]
    online_count: int
    online_local_matches: Optional[List[Dict[str, Any]]] = None


class SearchOnlineResponse(BaseModel):
    """Schema for online search response"""
    query: str
    online_documents: List[OnlineDocument]
    count: int


class CrawlUrlRequest(BaseModel):
    """Schema for crawl URL request"""
    url: str = Field(..., description="URL to crawl")


class CrawlUrlResponse(BaseModel):
    """Schema for crawl URL response"""
    title: str
    content: str
    url: str


class AddOnlineRequest(BaseModel):
    """Schema for add online documents request"""
    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, description="Maximum results to fetch")


class AddOnlineResponse(BaseModel):
    """Schema for add online documents response"""
    online_found: int
    added_count: int
    documents: List[OnlineDocument]


class TrainLDARequest(BaseModel):
    """Schema for train LDA request"""
    num_topics: int = Field(default=5, ge=1, le=50, description="Number of topics")
    project_name: Optional[str] = Field(None, description="Project name to save model")
    project_description: str = Field(default="", description="Project description")


class TrainLDAResponse(BaseModel):
    """Schema for train LDA response"""
    num_topics: int
    coherence: float
    topics: List[Dict[str, Any]]
    project_name: Optional[str]


class SimilarDocumentsResponse(BaseModel):
    """Schema for similar documents response"""
    doc_id: int
    similar_documents: List[SimilarDocument]
    count: int


class DocumentTopicsResponse(BaseModel):
    """Schema for document topics response"""
    document_topics: List[Dict[str, Any]]
    topics: List[Dict[str, Any]]
    num_documents: int
    coherence: float


class ModelStatusResponse(BaseModel):
    """Schema for model status response"""
    model_config = {"protected_namespaces": ()}

    model_trained: bool
    document_count: int
    num_topics: int
    dictionary_size: int
