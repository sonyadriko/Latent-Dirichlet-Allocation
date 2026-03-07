"""
Pydantic schemas for KDD Pipeline
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PipelineStatus(str, Enum):
    """Pipeline status enum"""
    pending = "pending"
    running = "running"
    completed = "completed"
    error = "error"


class StageStatus(BaseModel):
    """Schema for individual stage status"""
    crawling: PipelineStatus
    selection: PipelineStatus
    preprocessing: PipelineStatus
    transforming: PipelineStatus
    datamining: PipelineStatus


class DataCount(BaseModel):
    """Schema for data count"""
    raw: int
    selected: int
    preprocessed: int


class CrawlResults(BaseModel):
    """Schema for crawl results"""
    success_count: int
    failed_count: int


class KDDStatusResponse(BaseModel):
    """Schema for KDD pipeline status response"""
    project_name: Optional[str]
    status: StageStatus
    data_count: DataCount
    crawl_results: Optional[CrawlResults]


class TopicWord(BaseModel):
    """Schema for a topic word with weight"""
    word: str
    weight: float


class Topic(BaseModel):
    """Schema for a topic"""
    topic_id: int
    words: List[str]
    weights: List[float]


class DocumentTopic(BaseModel):
    """Schema for document topic distribution"""
    doc_id: int
    dominant_topic: int
    topic_distribution: Dict[int, float]


class CrawlStats(BaseModel):
    """Schema for crawl statistics"""
    total_urls: int
    success_count: int
    failed_count: int


class KDDResults(BaseModel):
    """Schema for KDD pipeline results"""
    project_name: Optional[str]
    num_topics: int
    topics: List[Topic]
    document_topics: List[DocumentTopic]
    coherence_score: float
    topic_distribution: Dict[str, float]
    documents: List[Dict[str, Any]]
    crawl_stats: CrawlStats


class FullPipelineResponse(BaseModel):
    """Schema for full pipeline completion response"""
    project_name: str
    crawl_stats: CrawlStats
    num_topics: int
    topics: List[Topic]


class PreprocessingData(BaseModel):
    """Schema for preprocessing data item"""
    id: int
    title: str
    original_length: int
    tokens_count: int
    tokens_sample: List[str]


class PreprocessingResponse(BaseModel):
    """Schema for preprocessing response"""
    total_documents: int
    sample: List[PreprocessingData]


class TransformResponse(BaseModel):
    """Schema for transform response"""
    dictionary_size: int
    corpus_size: int
    sample_bow: List[List[tuple]]


class DataMiningResponse(BaseModel):
    """Schema for data mining response"""
    num_topics: int
    topics: List[Topic]
    document_topics: List[DocumentTopic]
    coherence_score: float
    topic_distribution: Dict[str, float]
